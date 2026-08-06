"""Remove validation test farmers (Flow Test Farmer / Reject Flow) and their logins."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app, db
from backend.models import Farmer, User

app = create_app()
with app.app_context():
    removed_f = removed_u = 0
    for f in Farmer.query.filter(Farmer.name.in_(['Flow Test Farmer', 'Reject Flow'])).all():
        u = User.query.filter_by(farmer_id=f.id).first()
        if u:
            db.session.delete(u)
            removed_u += 1
        db.session.delete(f)
        removed_f += 1
    db.session.commit()
    print(f'Removed {removed_f} test farmers, {removed_u} test logins')
