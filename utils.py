from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def admin_required(fn):
    """Permite acceso solo a usuarios con rol Admin."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('rol') != 'Admin':
            return jsonify({
                'success': False,
                'message': 'Acceso denegado. Se requiere rol de Administrador.'
            }), 403
        return fn(*args, **kwargs)

    return wrapper


def login_required(fn):
    """Permite acceso a cualquier usuario autenticado."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)

    return wrapper
