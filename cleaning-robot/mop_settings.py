from flask import (
    Blueprint, request, jsonify
)

from air_service import *
from db import get_db

bp = Blueprint('mop_settings', __name__)

@bp.route('/mop_settings', methods=['POST'])
def set_vacuum_settings():
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
def get_mop_settings():
    id = request.form['id']
    result = get_db().execute(
        'SELECT *'
        ' FROM mop_settings'
        ' WHERE id=(?)',
        (id, )
    ).fetchone()
    return jsonify({
    'data': {
        'id': result['id'],
        'timestamp': result['timestamp'],
        'frequency': result['frequency']
    }
}), 200