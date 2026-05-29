from flask import Blueprint, request, jsonify
from flask.views import MethodView
from werkzeug.security import generate_password_hash
from extensions import db
from models import Usuario, Empleado, Medico  # <-- Asegúrate de tener Medico importado
from utils import admin_required, login_required

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/api/usuarios')

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
        Registra un nuevo usuario.
        Todos los usuarios se ligan mediante id_empleado.
        Si el rol es 'Medico', se valida cruzado que el empleado exista en la tabla de médicos.
        """
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        campos_requeridos = ['id_empleado', 'nombre_usuario', 'password', 'rol']
        for campo in campos_requeridos:
            if not data.get(campo):
                return jsonify({
                    'success': False,
                    'message': f'El campo {campo} es requerido.'
                }), 400

        if data['rol'] not in ROLES_VALIDOS:
            return jsonify({
                'success': False,
                'message': f'rol debe ser uno de: {ROLES_VALIDOS}'
            }), 400

        # 1. Verificar que el empleado existe en la base de datos general
        id_empleado = data['id_empleado']
        empleado = Empleado.query.get(id_empleado)
        if not empleado:
            return jsonify({'success': False, 'message': 'Empleado no encontrado.'}), 404

        # 2. Verificar que el empleado no tenga ya una cuenta de usuario
        if empleado.usuario:
            return jsonify({'success': False, 'message': 'Este empleado ya tiene un usuario asignado.'}), 409

        # 3. Verificar nombre de usuario único
        if Usuario.query.filter_by(nombre_usuario=data['nombre_usuario']).first():
            return jsonify({'success': False, 'message': 'El nombre de usuario ya existe.'}), 409

        if len(data['password']) < 8:
            return jsonify({
                'success': False,
                'message': 'La contraseña debe tener al menos 8 caracteres.'
            }), 400

        # --- VALIDACIÓN CRUZADA PARA MÉDICOS ---
        if data['rol'] == 'Medico':
            # Buscamos en la tabla Medico si existe algún registro vinculado a este id_empleado
            es_medico = Medico.query.filter_by(id_empleado=id_empleado).first()

            if not es_medico:
                return jsonify({
                    'success': False,
                    'message': f'Operación denegada: El empleado con ID {id_empleado} no está registrado como Médico en el sistema.'
                }), 403
        # ---------------------------------------

        # Creación del usuario (Todo fluye hacia id_empleado de forma normalizada)
        usuario = Usuario(
            id_empleado=id_empleado,
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