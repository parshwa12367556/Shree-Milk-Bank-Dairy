"""
Smart Dairy ERP — Farmer Routes

GET     /api/farmers               — List farmers (paginated, filterable)
GET     /api/farmers/stats         — Farmer statistics
GET     /api/farmers/export        — Export farmers as CSV
POST    /api/farmers               — Register new farmer (Branch Manager)
GET     /api/farmers/<code>        — Farmer detail + bank + stats
PATCH   /api/farmers/<code>        — Update farmer (incl. bank details)
POST    /api/farmers/<code>/verify — Verify farmer (Head Office)
"""
from datetime import datetime
import csv
import io
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import Farmer, BankDetail, Collection, Payment, Branch, User
from backend.auth import role_required, get_identity, hash_password, reject_farmer
from backend.utils import (generate_farmer_code, generate_farmer_email, utcnow,
                           sign_farmer_qr, verify_farmer_qr)
from backend.audit import log_audit
from backend.notify import notify

farmer_bp = Blueprint('farmers', __name__)


@farmer_bp.route('/api/farmers', methods=['GET'])
@jwt_required()
def get_farmers():
    """List farmers with pagination and filtering."""
    reject_farmer()  # farmers use /api/farmer/me only
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    q = request.args.get('q', '').strip()
    branch_id = request.args.get('branchId', type=int)
    milk_type = request.args.get('milk_type', '').strip()
    status = request.args.get('status', '').strip()

    query = Farmer.query

    # Branch filter (respect user's branch)
    user = get_identity()
    user_branch_id = user.get('branchId')
    if user.get('role') not in ('ADMIN',) and user_branch_id:
        query = query.filter_by(branch_id=user_branch_id)
    elif branch_id:
        query = query.filter_by(branch_id=branch_id)

    # Search (ID, name, mobile, Aadhaar, village)
    if q:
        search = f'%{q}%'
        query = query.filter(
            db.or_(
                Farmer.farmer_code.ilike(search),
                Farmer.name.ilike(search),
                Farmer.mobile.ilike(search),
                Farmer.aadhaar.ilike(search),
                Farmer.village.ilike(search),
            )
        )

    # Milk type filter
    if milk_type:
        query = query.filter_by(milk_type=milk_type.upper())

    # Status filter
    if status:
        query = query.filter_by(status=status.upper())

    # Order by most recent
    query = query.order_by(Farmer.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'farmers': [f.to_dict() for f in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': per_page,
    })


@farmer_bp.route('/api/farmers/stats', methods=['GET'])
@jwt_required()
def get_farmer_stats():
    """Get farmer statistics (respects user's branch scope)."""
    reject_farmer()
    user = get_identity()
    user_branch_id = user.get('branchId')
    scoped = user.get('role') not in ('ADMIN',) and user_branch_id
    q = Farmer.query.filter_by(branch_id=user_branch_id) if scoped else Farmer.query

    total = q.count()
    active = q.filter_by(status='ACTIVE').count()
    pending = q.filter_by(status='PENDING_VERIFICATION').count()
    rejected = q.filter_by(status='REJECTED').count()
    cow = q.filter_by(milk_type='COW', status='ACTIVE').count()
    buffalo = q.filter_by(milk_type='BUFFALO', status='ACTIVE').count()
    mixed = q.filter_by(milk_type='MIXED', status='ACTIVE').count()
    inactive = q.filter_by(status='INACTIVE').count()
    blocked = q.filter_by(status='BLOCKED').count()

    return jsonify({
        'total': total,
        'active': active,
        'pendingVerification': pending,
        'rejected': rejected,
        'cow': cow,
        'buffalo': buffalo,
        'mixed': mixed,
        'inactive': inactive,
        'blocked': blocked,
    })


@farmer_bp.route('/api/farmers', methods=['POST'])
@jwt_required()
@role_required('ADMIN', 'BRANCH_MANAGER')
def create_farmer():
    """Register a new farmer — ADMIN or BRANCH_MANAGER.

    Branch resolution (never trusted blindly):
      - ADMIN: the branch is taken from the request (branchId) and validated.
      - BRANCH_MANAGER: the branch is ALWAYS the manager's own assigned
        branch — a client-supplied branchId is ignored.
    The farmer ID is auto-generated as <branch_code><3-digit serial> (e.g. BR01001).
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    name = data.get('name', '').strip()
    mobile = data.get('mobile', '').strip()
    milk_type = (data.get('milkType') or '').upper()

    if not name:
        return jsonify({'error': 'Farmer name is required'}), 400
    if not mobile:
        return jsonify({'error': 'Mobile number is required'}), 400
    if milk_type not in ('COW', 'BUFFALO', 'MIXED'):
        return jsonify({'error': 'Valid milk type is required (COW, BUFFALO, MIXED)'}), 400

    user = get_identity()
    if user.get('role') == 'ADMIN':
        # Admin may register a farmer under any branch they choose.
        try:
            branch_id = int(data.get('branchId') or 0)
        except (TypeError, ValueError):
            branch_id = 0
        if not branch_id:
            return jsonify({'error': 'Please select the branch for this farmer.'}), 400
    else:
        # Branch operators can only register farmers for their own branch.
        branch_id = user.get('branchId')
        if not branch_id:
            return jsonify({'error': 'No branch assigned to this user. Contact Head Office.'}), 400

    branch = Branch.query.get(branch_id)
    if not branch or branch.status != 'ACTIVE':
        return jsonify({'error': 'Selected branch not found or inactive.'}), 400

    # Auto-generate farmer code: <branch_code><3-digit serial> (e.g. BR01001)
    prefix = branch.code
    existing_codes = [
        f.farmer_code for f in Farmer.query.filter(
            Farmer.farmer_code.like(f'{prefix}___')
        ).all()
    ]
    max_seq = 0
    for code in existing_codes:
        suffix = code[len(prefix):]
        if len(suffix) == 3 and suffix.isdigit():
            max_seq = max(max_seq, int(suffix))
    seq = max_seq + 1
    if seq > 999:
        return jsonify({'error': f'Farmer ID series exhausted for branch {prefix}. Contact Head Office.'}), 409

    farmer_code = generate_farmer_code(prefix, seq)
    # Signed QR payload — minted at registration so the farmer's QR exists
    # before it is ever scanned (contains only the farmer code + signature).
    qr_payload = sign_farmer_qr(farmer_code)

    # Farmers sign in with email + mobile, so an email is required. If the
    # branch didn't provide one, generate a deterministic address from the
    # farmer code (e.g. BR01011 -> br01011@dairy.com). Normalize to lowercase
    # so lookups (which are case-insensitive) stay consistent with storage.
    email = (data.get('email') or '').strip().lower()
    email = email or generate_farmer_email(farmer_code)

    farmer = Farmer(
        farmer_code=farmer_code,
        name=name,
        father_name=data.get('fatherName', ''),
        mobile=mobile,
        alt_mobile=data.get('altMobile', ''),
        email=email,
        aadhaar=data.get('aadhaar', ''),
        gender=data.get('gender', ''),
        address=data.get('address', ''),
        village=data.get('village', ''),
        taluka=data.get('taluka', ''),
        district=data.get('district', ''),
        state=data.get('state', ''),
        pincode=data.get('pincode', ''),
        milk_type=milk_type,
        cow_count=data.get('cowCount', 0),
        buffalo_count=data.get('buffaloCount', 0),
        breed=data.get('breed', ''),
        preferred_shift=data.get('preferredShift', ''),
        branch_id=branch_id,
        # New registrations enter the verification workflow (Head Office must
        # verify bank/aadhaar details before the farmer can receive payments).
        status='PENDING_VERIFICATION',
        created_by=user.get('uid'),
        qr_code=qr_payload,
    )
    db.session.add(farmer)
    db.session.flush()  # Get farmer ID

    # Auto-create the farmer's login account — login_id = farmer code
    # (so the Farmer Code IS the Login ID, spec §3), password = registered
    # mobile as the initial/temporary password. The account stays INACTIVE
    # until Head Office verifies the farmer, and must change the temporary
    # password on first login.
    db.session.add(User(
        login_id=farmer_code,
        username=farmer_code,
        password_hash=hash_password(mobile),
        name=name,
        role='FARMER',
        branch_id=branch_id,
        phone=mobile,
        email=email,
        status='INACTIVE',  # activated in verify_farmer on approval
        farmer_id=farmer.id,
        must_change_password=True,  # first login requires a real password
    ))

    # Create bank detail if provided
    if data.get('accountNumber') or data.get('ifsc'):
        bank = BankDetail(
            farmer_id=farmer.id,
            account_holder=data.get('accountHolder', name),
            bank_name=data.get('bankName', ''),
            branch_name=data.get('bankBranch', ''),
            account_number=data.get('accountNumber', ''),
            ifsc=data.get('ifsc', ''),
            upi=data.get('upi', ''),
        )
        db.session.add(bank)

    log_audit('CREATE', 'Farmer', farmer_code, detail=f'Farmer {name} registered (pending verification)')
    notify('farmer', 'New Farmer Registered',
           f'{name} ({farmer_code}) registered and awaiting verification.',
           link='farmers')
    db.session.commit()

    return jsonify({
        'farmer': farmer.to_dict(),
        'message': f'Farmer {name} registered with code {farmer_code}. Awaiting verification by Head Office.'
    }), 201


@farmer_bp.route('/api/farmers/<code>/verify', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def verify_farmer(code):
    """Verify (approve) or reject a farmer (Head Office only).

    body: {'action': 'approve' | 'reject', 'reason': '...'}
    - approve: PENDING_VERIFICATION → ACTIVE (eligible for payments)
    - reject:  PENDING_VERIFICATION → REJECTED with a reason (branch can edit
      and resubmit)
    """
    farmer = Farmer.query.filter_by(farmer_code=code).first()
    if not farmer:
        return jsonify({'error': 'Farmer not found'}), 404

    if farmer.status != 'PENDING_VERIFICATION':
        return jsonify({'error': f'Farmer is already {farmer.status}. Only pending farmers can be reviewed.'}), 400

    data = request.get_json(silent=True) or {}
    action = (data.get('action') or 'approve').lower()
    reason = (data.get('reason') or '').strip()
    user = get_identity()

    if action == 'approve':
        farmer.status = 'ACTIVE'
        farmer.status_reason = None
        farmer.verified_by = user.get('uid')
        farmer.verified_at = utcnow()
        # Activate the farmer's login account on approval
        if farmer.user_account:
            farmer.user_account.status = 'ACTIVE'
        log_audit('VERIFY', 'Farmer', farmer.farmer_code,
                  detail=f'Farmer {farmer.name} verified and activated by Head Office')
        notify('farmer', 'Farmer Verified',
               f'{farmer.name} ({farmer.farmer_code}) verified and activated.',
               link='farmers')
        message = f'Farmer {farmer.farmer_code} verified and activated. Payments can now be processed.'
    elif action == 'reject':
        if not reason:
            return jsonify({'error': 'A rejection reason is required'}), 400
        farmer.status = 'REJECTED'
        farmer.status_reason = reason
        # Rejected farmers stay locked out of the portal
        if farmer.user_account:
            farmer.user_account.status = 'INACTIVE'
        log_audit('REJECT', 'Farmer', farmer.farmer_code,
                  detail=f'Farmer {farmer.name} rejected: {reason}')
        notify('farmer', 'Farmer Rejected',
               f'{farmer.name} ({farmer.farmer_code}) verification rejected: {reason}',
               link='farmers')
        message = f'Farmer {farmer.farmer_code} rejected. Branch can edit and resubmit.'
    else:
        return jsonify({'error': "Action must be 'approve' or 'reject'"}), 400

    db.session.commit()
    return jsonify({'farmer': farmer.to_dict(), 'message': message})


@farmer_bp.route('/api/farmers/<code>/resubmit', methods=['POST'])
@jwt_required()
@role_required('ADMIN', 'BRANCH_MANAGER')
def resubmit_farmer(code):
    """Re-submit a REJECTED farmer for verification (Branch Manager)."""
    farmer = Farmer.query.filter_by(farmer_code=code).first()
    if not farmer:
        return jsonify({'error': 'Farmer not found'}), 404

    user = get_identity()
    if user.get('branchId') != farmer.branch_id:
        return jsonify({'error': 'You can only resubmit farmers from your own branch.'}), 403

    if farmer.status != 'REJECTED':
        return jsonify({'error': 'Only rejected farmers can be resubmitted.'}), 400

    farmer.status = 'PENDING_VERIFICATION'
    farmer.status_reason = None
    log_audit('UPDATE', 'Farmer', farmer.farmer_code,
              detail=f'Farmer {farmer.name} resubmitted for verification')
    db.session.commit()

    return jsonify({'farmer': farmer.to_dict(),
                    'message': f'Farmer {farmer.farmer_code} resubmitted for Head Office review.'})


@farmer_bp.route('/api/farmers/<code>/verify-bank', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def verify_farmer_bank(code):
    """Verify or reject a farmer's bank details (Head Office only).

    body: {'action': 'verify' | 'reject', 'reason': '...'}
    """
    farmer = Farmer.query.filter_by(farmer_code=code).first()
    if not farmer:
        return jsonify({'error': 'Farmer not found'}), 404

    bank = farmer.bank_detail
    if not bank:
        return jsonify({'error': 'No bank details on file for this farmer.'}), 400

    data = request.get_json(silent=True) or {}
    action = (data.get('action') or 'verify').lower()
    reason = (data.get('reason') or '').strip()
    user = get_identity()

    if action == 'verify':
        bank.verification_status = 'VERIFIED'
        bank.verified_by = user.get('uid')
        bank.verified_at = utcnow()
        log_audit('VERIFY', 'BankDetail', farmer.farmer_code,
                  detail=f'Bank details verified for {farmer.farmer_code} ({bank.bank_name})')
        message = f'Bank details for {farmer.farmer_code} verified.'
    elif action == 'reject':
        bank.verification_status = 'REJECTED'
        log_audit('REJECT', 'BankDetail', farmer.farmer_code,
                  detail=f'Bank details rejected for {farmer.farmer_code}' + (f': {reason}' if reason else ''))
        message = f'Bank details for {farmer.farmer_code} rejected.'
    else:
        return jsonify({'error': "Action must be 'verify' or 'reject'"}), 400

    db.session.commit()
    return jsonify({'farmer': farmer.to_dict(), 'message': message})


@farmer_bp.route('/api/farmers/export', methods=['GET'])
@jwt_required()
def export_farmers():
    """Export farmers as CSV (branch-scoped)."""
    reject_farmer()
    query = Farmer.query

    user = get_identity()
    user_branch_id = user.get('branchId')
    if user.get('role') not in ('ADMIN',) and user_branch_id:
        query = query.filter_by(branch_id=user_branch_id)

    branch_id = request.args.get('branchId', type=int)
    if branch_id and user.get('role') in ('ADMIN',):
        query = query.filter_by(branch_id=branch_id)

    farmers = query.order_by(Farmer.farmer_code).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Farmer ID', 'Name', 'Father Name', 'Mobile', 'Email', 'Aadhaar',
        'Village', 'Taluka', 'District', 'State', 'Pincode', 'Milk Type',
        'Cows', 'Buffaloes', 'Branch', 'Bank Name', 'IFSC', 'Account No',
        'Status', 'Joined',
    ])
    for f in farmers:
        bank = f.bank_detail
        writer.writerow([
            f.farmer_code, f.name, f.father_name or '', f.mobile or '',
            f.email or '', f.aadhaar or '', f.village or '', f.taluka or '',
            f.district or '', f.state or '', f.pincode or '', f.milk_type,
            f.cow_count or 0, f.buffalo_count or 0,
            f.branch.code if f.branch else '',
            bank.bank_name if bank else '', bank.ifsc if bank else '',
            bank.account_number if bank else '', f.status,
            f.joined_at.isoformat() if f.joined_at else '',
        ])

    log_audit('EXPORT', 'Farmer', None, detail=f'Exported {len(farmers)} farmers as CSV')
    db.session.commit()

    filename = 'farmers_export.csv'
    return Response(
        '\ufeff' + output.getvalue(),  # BOM for Excel compatibility
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )


def _qr_data_uri(payload):
    """Render the QR payload as an SVG data URI (pure Python, no Pillow)."""
    import base64
    from io import BytesIO
    try:
        import qrcode
        from qrcode.image.svg import SvgPathImage
    except ImportError:
        return None
    try:
        img = qrcode.make(payload, image_factory=SvgPathImage)
        buf = BytesIO()
        img.save(buf)
        return 'data:image/svg+xml;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')
    except Exception:
        return None


def _scoped_farmer_or_error(code):
    """Load a farmer and enforce the caller's branch scope (shared by QR routes)."""
    reject_farmer()
    farmer = Farmer.query.filter_by(farmer_code=code).first()
    if not farmer:
        return None, ({'error': 'Farmer not found'}, 404)
    user = get_identity()
    if user.get('role') not in ('ADMIN',) and user.get('branchId') != farmer.branch_id:
        return None, ({'error': 'You can only access farmers from your own branch.'}, 403)
    return farmer, None


@farmer_bp.route('/api/farmers/<code>/qr', methods=['GET'])
@jwt_required()
def get_farmer_qr(code):
    """Signed QR payload + rendered QR image for a farmer (branch-scoped).

    The payload carries NO private data (no Aadhaar/PAN/bank/mobile) — only
    the farmer code and an HMAC signature, so a scanned QR resolves to the
    right farmer without enabling impersonation.
    """
    farmer, err = _scoped_farmer_or_error(code)
    if err:
        return jsonify(err[0]), err[1]

    # Deterministic payload — minted at registration and stored on the row.
    payload = farmer.qr_code or sign_farmer_qr(farmer.farmer_code)
    if not farmer.qr_code:
        farmer.qr_code = payload
        db.session.commit()
    return jsonify({
        'farmerCode': farmer.farmer_code,
        'farmerName': farmer.name,
        'qrPayload': payload,
        'qrImage': _qr_data_uri(payload),
        'status': farmer.status,
    })


@farmer_bp.route('/api/farmers/<code>/qr', methods=['POST'])
@jwt_required()
def regenerate_farmer_qr(code):
    """Regenerate a farmer's signed QR payload (branch-scoped, ADMIN/operator)."""
    farmer, err = _scoped_farmer_or_error(code)
    if err:
        return jsonify(err[0]), err[1]
    payload = sign_farmer_qr(farmer.farmer_code)
    farmer.qr_code = payload
    log_audit('UPDATE', 'Farmer', farmer.farmer_code,
              detail=f'QR code regenerated for {farmer.farmer_code}')
    db.session.commit()
    return jsonify({
        'farmerCode': farmer.farmer_code,
        'qrPayload': payload,
        'qrImage': _qr_data_uri(payload),
    })


@farmer_bp.route('/api/farmers/qr-lookup', methods=['GET'])
@jwt_required()
def qr_lookup():
    """Resolve a signed QR payload to a farmer (branch-scoped).

    The HMAC signature is verified first, so a forged/tampered QR is
    rejected outright; the lookup itself cannot cross branch boundaries or
    expose other farmers' data.
    """
    reject_farmer()
    payload = request.args.get('payload', '')
    code = verify_farmer_qr(payload)
    if not code:
        return jsonify({'error': 'Invalid or tampered QR code.'}), 400
    farmer = Farmer.query.filter_by(farmer_code=code).first()
    if not farmer:
        return jsonify({'error': 'Farmer not found for this QR code.'}), 404
    user = get_identity()
    if user.get('role') not in ('ADMIN',) and user.get('branchId') != farmer.branch_id:
        return jsonify({'error': 'Access denied. Farmer belongs to another branch.'}), 403
    return jsonify({'farmer': farmer.to_dict(), 'status': farmer.status})


@farmer_bp.route('/api/farmers/<code>', methods=['GET'])
@jwt_required()
def get_farmer(code):
    """Get detailed farmer information including bank detail and stats."""
    reject_farmer()
    farmer = Farmer.query.filter_by(farmer_code=code).first()
    if not farmer:
        return jsonify({'error': 'Farmer not found'}), 404

    # Branch scope: managers can only view farmers from their own branch
    user = get_identity()
    if user.get('role') not in ('ADMIN',) and user.get('branchId') != farmer.branch_id:
        return jsonify({'error': 'You can only view farmers from your own branch.'}), 403

    # Get collection stats
    total_qty = db.session.query(db.func.sum(Collection.quantity))\
        .filter(Collection.farmer_id == farmer.id).scalar() or 0
    total_amount = db.session.query(db.func.sum(Collection.amount))\
        .filter(Collection.farmer_id == farmer.id).scalar() or 0
    collection_count = Collection.query.filter_by(farmer_id=farmer.id).count()

    # Get recent collections (passbook)
    recent_collections = Collection.query\
        .filter_by(farmer_id=farmer.id)\
        .order_by(Collection.created_at.desc())\
        .limit(20).all()

    return jsonify({
        'farmer': farmer.to_dict(),
        'stats': {
            'totalQuantity': total_qty,
            'totalAmount': total_amount,
            'collectionCount': collection_count,
        },
        'recentCollections': [c.to_dict() for c in recent_collections],
    })


@farmer_bp.route('/api/farmers/<code>', methods=['PATCH'])
@jwt_required()
def update_farmer(code):
    """Update farmer information."""
    reject_farmer()
    farmer = Farmer.query.filter_by(farmer_code=code).first()
    if not farmer:
        return jsonify({'error': 'Farmer not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Branch scope: managers can only edit farmers from their own branch
    user = get_identity()
    if user.get('role') not in ('ADMIN',) and user.get('branchId') != farmer.branch_id:
        return jsonify({'error': 'You can only edit farmers from your own branch.'}), 403

    # Map JSON field names to model attributes
    field_map = {
        'name': 'name', 'fatherName': 'father_name', 'mobile': 'mobile',
        'altMobile': 'alt_mobile', 'email': 'email', 'aadhaar': 'aadhaar',
        'pan': 'pan', 'dateOfBirth': 'date_of_birth',
        'village': 'village', 'taluka': 'taluka',
        'district': 'district', 'state': 'state', 'pincode': 'pincode',
        'address': 'address', 'landmark': 'landmark', 'remarks': 'remarks',
        'status': 'status', 'milkType': 'milk_type',
        'cowCount': 'cow_count', 'buffaloCount': 'buffalo_count',
        'breed': 'breed', 'preferredShift': 'preferred_shift',
    }

    for json_key, model_attr in field_map.items():
        if json_key in data:
            setattr(farmer, model_attr, data[json_key])

    # Only Head Office may change a farmer's status (freeze / activate)
    user = get_identity()
    if 'status' in data and user.get('role') not in ('ADMIN',):
        return jsonify({'error': 'Only Admin can change farmer status.'}), 403

    # Keep the farmer's login account status in sync (ACTIVE ⇄ locked out)
    if farmer.user_account:
        farmer.user_account.status = 'ACTIVE' if farmer.status == 'ACTIVE' else 'INACTIVE'

    # Update / create bank details (Head Office authorized bank updates)
    bank_fields = ['accountHolder', 'bankName', 'bankBranch', 'accountNumber', 'ifsc', 'upi']
    if any(k in data for k in bank_fields):
        bank = farmer.bank_detail
        if not bank:
            bank = BankDetail(farmer_id=farmer.id)
            db.session.add(bank)
        if 'accountHolder' in data:
            bank.account_holder = data['accountHolder']
        if 'bankName' in data:
            bank.bank_name = data['bankName']
        if 'bankBranch' in data:
            bank.branch_name = data['bankBranch']
        if 'accountNumber' in data:
            bank.account_number = data['accountNumber']
        if 'ifsc' in data:
            bank.ifsc = data['ifsc']
        if 'upi' in data:
            bank.upi = data['upi']

    log_audit('UPDATE', 'Farmer', farmer.farmer_code,
              detail=f'Farmer {farmer.name} updated')

    # Keep the login account email in sync (farmers log in with email).
    if 'email' in data:
        if farmer.email:
            farmer.email = farmer.email.strip().lower()
        if farmer.user_account:
            farmer.user_account.email = farmer.email or generate_farmer_email(farmer.farmer_code)

    db.session.commit()
    return jsonify({'farmer': farmer.to_dict(), 'message': 'Farmer updated successfully'})
