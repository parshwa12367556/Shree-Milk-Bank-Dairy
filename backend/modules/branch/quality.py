"""
Smart Dairy ERP — Quality Control Routes

GET  /api/quality     — List quality tests
POST /api/quality     — Create new quality test
"""
from datetime import date, datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.models import QualityTest, Collection, Farmer
from backend.auth import get_identity, get_branch_scope, scope_query
from backend.pricing import auto_grade_quality
from backend.audit import log_audit

quality_bp = Blueprint('quality', __name__)


@quality_bp.route('/api/quality', methods=['GET'])
@jwt_required()
def get_quality_tests():
    """List quality tests with filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    date_str = request.args.get('date', '')
    result = request.args.get('result', '')
    farmer_id = request.args.get('farmerId', type=int)

    # Branch isolation: Branch Managers only see quality tests of their branch
    query = scope_query(QualityTest.query, QualityTest).order_by(QualityTest.created_at.desc())

    if date_str:
        try:
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter_by(date=query_date)
        except (ValueError, TypeError):
            pass

    if result:
        query = query.filter_by(overall_result=result.upper())
    if farmer_id:
        query = query.filter_by(farmer_id=farmer_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'tests': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    })


@quality_bp.route('/api/quality', methods=['POST'])
@jwt_required()
def create_quality_test():
    """Create a new quality test with auto-grading."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    collection_id = data.get('collectionId')
    farmer_id = data.get('farmerId')

    if not collection_id and not farmer_id:
        return jsonify({'error': 'Collection ID or Farmer ID is required'}), 400

    farmer = None
    if farmer_id:
        farmer = Farmer.query.get(farmer_id)
    elif collection_id:
        collection = Collection.query.get(collection_id)
        if collection:
            farmer = collection.farmer
            farmer_id = farmer.id if farmer else farmer_id

    if not farmer:
        return jsonify({'error': 'Farmer not found'}), 404

    # Branch isolation: Branch Managers can only test farmers of their branch
    forced = get_branch_scope()
    if forced and farmer.branch_id != forced:
        return jsonify({'error': 'Access denied. Farmer belongs to another branch.'}), 403

    # Auto-grade based on parameters
    fat = data.get('fat', 0)
    water = data.get('waterContent', 0)
    clr = data.get('clr', 0)
    temperature = data.get('temperature', 0)

    grading = auto_grade_quality(
        fat=fat,
        snf=data.get('snf', 0),
        clr=clr,
        water=water,
        temperature=temperature,
        milk_type=farmer.milk_type,
    )

    test = QualityTest(
        collection_id=collection_id,
        farmer_id=farmer_id,
        branch_id=forced or data.get('branchId', farmer.branch_id),
        tested_by=get_identity().get('uid'),
        date=date.today(),
        shift=data.get('shift', ''),
        fat=fat,
        snf=data.get('snf'),
        clr=clr,
        density=data.get('density'),
        protein=data.get('protein'),
        lactose=data.get('lactose'),
        water_content=water,
        temperature=temperature,
        acidity=data.get('acidity'),
        mbrt=data.get('mbrt'),
        alcohol_test=data.get('alcoholTest'),
        freezing_point=data.get('freezingPoint'),
        overall_result=grading['overall'],
        result_summary='; '.join(grading['warnings']) if grading['warnings'] else grading['overall'],
    )
    db.session.add(test)
    db.session.flush()
    log_audit('CREATE', 'QualityTest', test.id,
              detail=f'Quality test for {farmer.farmer_code} → {grading["overall"]}')
    db.session.commit()

    return jsonify({
        'test': test.to_dict(),
        'grading': grading,
        'message': f'Quality test recorded. Result: {grading["overall"]}',
    }), 201
