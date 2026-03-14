from flask import Blueprint, request, jsonify
from def_model_tablas import db, Usuario, bcrypt
from flask_jwt_extended import create_access_token
import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    correo = data.get('correo')
    contra = data.get('contra')

    # Buscamos al usuario
    usuario = Usuario.query.filter_by(correo=correo).first()

    # Verificamos existencia y contraseña
    if usuario and bcrypt.check_password_hash(usuario.contra, contra):
        # El token durará 24 horas
        expires = datetime.timedelta(hours=24)

        # Guardamos el ID y el ROL dentro del token
        token = create_access_token(
            identity=str(usuario.id_usuario),
            additional_claims={"rol": usuario.rol},
            expires_delta=expires
        )

        return jsonify({
            "mensaje": "Bienvenido",
            "token": token,
            "usuario": usuario.to_dict()
        }), 200

    # Si falla, regresamos el código de error que mencionaste
    return jsonify({"error": "Correo o contraseña incorrectos"}), 401