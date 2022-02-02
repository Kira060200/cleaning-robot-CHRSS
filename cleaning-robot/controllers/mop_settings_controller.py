from services.air_service import *
from db import get_db
from services.robot_service import get_mop_settings
from auth import login_required

bp = Blueprint('mop_settings', __name__)

@bp.route('/mop_settings', methods=['POST'])
@login_required
def set_mop_settings_api():
    frequency = request.form['frequency']
    error = None

    air = get_air()

    if not frequency:
        if air is None:
            set_air_realtime()
            return jsonify({
                'status': 'No air quality record found; trying api...'
            }), 404
        frequency = air['value'] // 50 + 1

    db = get_db()
    db.execute(
        'INSERT INTO mop_settings (frequency)'
        ' VALUES (?)',
        (frequency, )
    )
    db.commit()

    check = get_db().execute(
        'SELECT id, timestamp, frequency'
        ' FROM mop_settings'
        ' ORDER BY timestamp DESC'
    ).fetchone()
    return jsonify({
        'status': 'Mop setting successfully recorded',
        'data': {
            'id': check['id'],
            'timestamp': check['timestamp'],
            'frequency': check['frequency']
        }
    }), 200

@bp.route('/mop_settings', methods=['GET'])
@login_required
def get_mop_settings_api():
    id = request.args.get('id')
    result = get_mop_settings(id)
    return jsonify(result), 200