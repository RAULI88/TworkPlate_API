from flask import Blueprint, request, jsonify
from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt
)
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db
from models import Usuario

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


# ─────────────────────────────────────────────
# POST /api/auth/login
# ─────────────────────────────────────────────
class LoginResource(MethodView):
    def post(self):
        """Iniciar sesión y obtener JWT."""
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        nombre_usuario = data.get('nombre_usuario', '').strip()
        password = data.get('password', '')

        if not nombre_usuario or not password:
            return jsonify({
                'success': False,
                'message': 'nombre_usuario y password son requeridos.'
            }), 400

        usuario = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()

        if not usuario or not check_password_hash(usuario.password_hash, password):
            return jsonify({'success': False, 'message': 'Credenciales incorrectas.'}), 401

        if usuario.estado == 'Inactivo':
            return jsonify({'success': False, 'message': 'Usuario inactivo.'}), 403

        # Incluimos el rol en los claims del token
        additional_claims = {
            'rol': usuario.rol,
            'id_usuario': usuario.id_usuario,
        }
        access_token = create_access_token(
            identity=str(usuario.id_usuario),
            additional_claims=additional_claims
        )

        return jsonify({
            'success': True,
            'access_token': access_token,
            'usuario': {
                'id_usuario': usuario.id_usuario,
                'nombre_usuario': usuario.nombre_usuario,
                'rol': usuario.rol,
                'id_empleado': usuario.id_empleado,
            }
        }), 200


# ─────────────────────────────────────────────
# GET /api/auth/me
# ─────────────────────────────────────────────
class MeResource(MethodView):
    @jwt_required()
    def get(self):
        """Retorna información del usuario autenticado."""
        claims = get_jwt()
        user_id = get_jwt_identity()
        usuario = Usuario.query.get(int(user_id))
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuario no encontrado.'}), 404
        return jsonify({'success': True, 'data': usuario.to_dict()}), 200


# Registro de rutas
auth_bp.add_url_rule('/login', view_func=LoginResource.as_view('login'))
auth_bp.add_url_rule('/me', view_func=MeResource.as_view('me'))
