from flask import Blueprint, request, jsonify
from flask.views import MethodView
from werkzeug.security import generate_password_hash
from extensions import db
from models import Usuario, Empleado, Medico  # <-- Añadido el modelo Medico
from utils import admin_required, login_required

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/api/usuarios')

# <-- Añadido 'Medico' a los roles permitidos
ROLES_VALIDOS = ('Admin', 'Recepcionista', 'Medico')
ESTADOS_VALIDOS = ('Activo', 'Inactivo')


# ─────────────────────────────────────────────
# /api/usuarios
# ─────────────────────────────────────────────
class UsuariosResource(MethodView):

    @admin_required
    def get(self):
        """Lista todos los usuarios del sistema. Solo Admin."""
        usuarios = Usuario.query.order_by(Usuario.nombre_usuario).all()
        return jsonify({
            'success': True,
            'data': [u.to_dict() for u in usuarios],
            'total': len(usuarios)
        }), 200

    @admin_required
    def post(self):
        """
        Registra un nuevo usuario (Admin, Recepcionista o Medico). Solo Admin.
        Verifica dinámicamente si pertenece a Empleado o a Medico.
        """
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        # Validar campos base requeridos
        if not data.get('nombre_usuario') or not data.get('password') or not data.get('rol'):
            return jsonify({
                'success': False,
                'message': 'Los campos nombre_usuario, password y rol son requeridos.'
            }), 400

        if data['rol'] not in ROLES_VALIDOS:
            return jsonify({
                'success': False,
                'message': f'rol debe ser uno de: {ROLES_VALIDOS}'
            }), 400

        # Verificar nombre de usuario único antes de hacer consultas a otras tablas
        if Usuario.query.filter_by(nombre_usuario=data['nombre_usuario']).first():
            return jsonify({'success': False, 'message': 'El nombre de usuario ya existe.'}), 409

        if len(data['password']) < 8:
            return jsonify({
                'success': False,
                'message': 'La contraseña debe tener al menos 8 caracteres.'
            }), 400

        # --- VALIDACIÓN DINÁMICA DE ROLES ---
        id_empleado_db = None
        id_medico_db = None

        if data['rol'] == 'Medico':
            if not data.get('id_medico'):
                return jsonify(
                    {'success': False, 'message': 'El campo id_medico es requerido para registrar a un doctor.'}), 400

            medico = Medico.query.get(data['id_medico'])
            if not medico:
                return jsonify({'success': False, 'message': 'Médico no encontrado en la base de datos.'}), 404

            # Asumiendo que la relación en el modelo Medico se llama 'usuario'
            if hasattr(medico, 'usuario') and medico.usuario:
                return jsonify(
                    {'success': False, 'message': 'Este médico ya tiene una cuenta de usuario asignada.'}), 409

            id_medico_db = data['id_medico']

        else:  # Si es Admin o Recepcionista
            if not data.get('id_empleado'):
                return jsonify({'success': False, 'message': 'El campo id_empleado es requerido para este rol.'}), 400

            empleado = Empleado.query.get(data['id_empleado'])
            if not empleado:
                return jsonify({'success': False, 'message': 'Empleado no encontrado en la base de datos.'}), 404

            if empleado.usuario:
                return jsonify(
                    {'success': False, 'message': 'Este empleado ya tiene una cuenta de usuario asignada.'}), 409

            id_empleado_db = data['id_empleado']
        # ------------------------------------

        # Creación del usuario enviando el ID correspondiente (el otro quedará como NULL)
        usuario = Usuario(
            id_empleado=id_empleado_db,
            id_medico=id_medico_db,
            nombre_usuario=data['nombre_usuario'].strip(),
            password_hash=generate_password_hash(data['password']),
            rol=data['rol'],
            estado=data.get('estado', 'Activo'),
        )
        db.session.add(usuario)
        db.session.commit()

        return jsonify({'success': True, 'data': usuario.to_dict()}), 201


# ─────────────────────────────────────────────
# /api/usuarios/<id>
# ─────────────────────────────────────────────
class UsuarioResource(MethodView):

    @admin_required
    def get(self, id_usuario):
        """Obtiene un usuario por ID. Solo Admin."""
        usuario = Usuario.query.get_or_404(id_usuario)
        return jsonify({'success': True, 'data': usuario.to_dict()}), 200

    @admin_required
    def put(self, id_usuario):
        """Actualiza un usuario. Solo Admin."""
        usuario = Usuario.query.get_or_404(id_usuario)
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        if 'nombre_usuario' in data:
            existe = Usuario.query.filter(
                Usuario.nombre_usuario == data['nombre_usuario'],
                Usuario.id_usuario != id_usuario
            ).first()
            if existe:
                return jsonify({'success': False, 'message': 'El nombre de usuario ya existe.'}), 409
            usuario.nombre_usuario = data['nombre_usuario'].strip()

        if 'password' in data:
            if len(data['password']) < 8:
                return jsonify({
                    'success': False,
                    'message': 'La contraseña debe tener al menos 8 caracteres.'
                }), 400
            usuario.password_hash = generate_password_hash(data['password'])

        if 'rol' in data:
            if data['rol'] not in ROLES_VALIDOS:
                return jsonify({'success': False, 'message': 'rol inválido.'}), 400
            usuario.rol = data['rol']

        if 'estado' in data:
            if data['estado'] not in ESTADOS_VALIDOS:
                return jsonify({'success': False, 'message': 'estado inválido.'}), 400
            usuario.estado = data['estado']

        db.session.commit()
        return jsonify({'success': True, 'data': usuario.to_dict()}), 200

    @admin_required
    def delete(self, id_usuario):
        """Desactiva un usuario. Solo Admin."""
        usuario = Usuario.query.get_or_404(id_usuario)
        usuario.estado = 'Inactivo'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Usuario desactivado correctamente.'}), 200


# Registro de rutas
usuarios_bp.add_url_rule('',
                         view_func=UsuariosResource.as_view('usuarios_list'))
usuarios_bp.add_url_rule('/<int:id_usuario>',
                         view_func=UsuarioResource.as_view('usuario_detail'))