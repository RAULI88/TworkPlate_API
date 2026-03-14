from flask import Blueprint, request, jsonify
from flask.views import MethodView
from def_model_tablas import db, Usuario, bcrypt

usuario_bp = Blueprint('usuario', __name__)


class UsuarioAPI(MethodView):

    def get(self):
        try:
            usuarios = Usuario.query.all()
            return jsonify([usuario.to_dict() for usuario in usuarios]), 200
        except Exception as e:
            return jsonify({"error": "Error al obtener usuarios", "detalle": str(e)}), 500

    def post(self):
        data = request.get_json()

        campos_requeridos = ['nombre', 'ap1', 'correo', 'contra', 'rol']
        if not data or not all(campo in data for campo in campos_requeridos):
            return jsonify({"error": "Faltan campos obligatorios (nombre, ap1, correo, contra, rol)"}), 400

        # ========================================================
        # NUEVA VALIDACIÓN DE ROLES
        # ========================================================
        if data['rol'] not in [1, 2, 3]:
            return jsonify({
                "error": "Rol inválido. Solo se permite: 1 (Admin General), 2 (Admin Secundario), 3 (Usuario Final)"
            }), 400

        try:
            hash_contrasena = bcrypt.generate_password_hash(data['contra']).decode('utf-8')

            nuevo_usuario = Usuario(
                nombre=data['nombre'],
                ap1=data['ap1'],
                ap2=data.get('ap2'),
                correo=data['correo'],
                contra=hash_contrasena,
                rol=data['rol']
            )

            db.session.add(nuevo_usuario)
            db.session.commit()

            return jsonify({
                "mensaje": "Usuario creado con éxito",
                "usuario": nuevo_usuario.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al crear usuario", "detalle": str(e)}), 500


usuario_bp.add_url_rule('/usuarios', view_func=UsuarioAPI.as_view('usuario_api'), methods=['GET', 'POST'])