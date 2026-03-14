from flask import Blueprint, request, jsonify
from flask.views import MethodView
# IMPORTANTE: Se agregó 'Usuario' a la importación
from def_model_tablas import db, Funcionalidad, Usuario
import json

func_bp = Blueprint('funcionalidad', __name__)


class FuncionalidadAPI(MethodView):

    # ---------------------------------------------------------
    # ENDPOINT GET: Regresa solo los objetos json_fun como un array
    # ---------------------------------------------------------
    def get(self):
        try:
            # Traemos todos los registros
            funcionalidades = Funcionalidad.query.all()

            # Solo guardaremos el contenido de json_fun en esta lista
            solo_funcionalidades = []

            for func in funcionalidades:
                try:
                    # Convertimos el texto de la DB a un objeto JSON (diccionario)
                    data_extraida = json.loads(func.json_fun)
                    solo_funcionalidades.append(data_extraida)
                except:
                    # Si algún registro tiene texto corrupto, lo saltamos o lo enviamos como texto
                    solo_funcionalidades.append({"error": "Formato JSON inválido en este registro"})

            # Retornamos directamente el array de objetos
            return jsonify(solo_funcionalidades), 200

        except Exception as e:
            return jsonify({"error": "Error al obtener funcionalidades", "detalle": str(e)}), 500

    def post(self):
        data = request.get_json()

        if not data or 'id_usuario' not in data or 'json_fun' not in data:
            return jsonify({"error": "Se requiere id_usuario y json_fun"}), 400

        # ========================================================
        # NUEVA VALIDACIÓN: SOLO ROL 1 PUEDE CREAR
        # ========================================================
        # Buscamos al usuario en la base de datos usando el ID que nos enviaron
        usuario_creador = db.session.get(Usuario, data['id_usuario'])

        if not usuario_creador:
            return jsonify({"error": "El id_usuario proporcionado no existe"}), 404

        if usuario_creador.rol != 1:
            return jsonify({
                "error": "Acceso denegado. Solo los administradores generales (rol 1) pueden crear funcionalidades"
            }), 403  # 403 es el código HTTP estándar para "Prohibido / Sin permisos"

        try:
            contenido_json = data['json_fun']

            if isinstance(contenido_json, dict) or isinstance(contenido_json, list):
                contenido_json = json.dumps(contenido_json)

            nueva_funcionalidad = Funcionalidad(
                id_usuario=data['id_usuario'],
                json_fun=contenido_json
            )

            db.session.add(nueva_funcionalidad)
            db.session.commit()

            return jsonify({
                "mensaje": "Funcionalidad creada con éxito",
                "id_funcionalidad": nueva_funcionalidad.id_funcionalidad
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al crear funcionalidad", "detalle": str(e)}), 500


func_bp.add_url_rule('/funcionalidades', view_func=FuncionalidadAPI.as_view('funcionalidad_api'),
                     methods=['GET', 'POST'])