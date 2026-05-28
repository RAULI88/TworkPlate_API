from flask import Flask, jsonify
import os
from dotenv import load_dotenv

# Importar las extensiones (db, jwt, cors) desde tu archivo extensions.py
from extensions import db, jwt, cors

# Importar todos los blueprints de la carpeta resources
# Importar todos los blueprints de la carpeta resources
from resources.dashboard import dashboard_bp
from resources.auth import auth_bp
from resources.empleados import empleados_bp
from resources.usuarios import usuarios_bp
from resources.especialidades import especialidades_bp
from resources.medicos import medicos_bp
from resources.pacientes import pacientes_bp
from resources.servicios import servicios_bp
from resources.citas import citas_bp
from resources.consultas import consultas_bp
from resources.pagos import pagos_bp
from resources.public import public_bp

# CARGA DE VARIABLES DE ENTORNO
load_dotenv()


def create_app():
    app = Flask(__name__)

    # 1. Configuración de CORS y JWT
    cors.init_app(app, resources={r'/api/*': {'origins': '*'}})
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "clave-secreta-de-respaldo")
    jwt.init_app(app)

    # 2. CONFIGURACIÓN DE CONEXIÓN A LA BASE DE DATOS (PostgreSQL)
    DB_USER = os.environ.get("POSTGRES_USER")
    DB_PASS = os.environ.get("POSTGRES_PASSWORD")
    DB_HOST = os.environ.get("POSTGRES_HOST")
    DB_PORT = os.environ.get("POSTGRES_PORT")
    DB_NAME = os.environ.get("POSTGRES_DB")

    # Construye la URI de conexión asegurando que use el driver de postgresql
    app.config['SQLALCHEMY_DATABASE_URI'] = \
        f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar Base de datos
    db.init_app(app)

    # 3. REGISTRO DE RUTAS (BLUEPRINTS)
    blueprints = [
        auth_bp,
        empleados_bp,
        usuarios_bp,
        especialidades_bp,
        medicos_bp,
        pacientes_bp,
        servicios_bp,
        citas_bp,
        consultas_bp,
        pagos_bp,
        public_bp,
        dashboard_bp
    ]

    # Se registran todos los endpoints de la API
    for bp in blueprints:
        app.register_blueprint(bp)

    # 4. MANEJO DE ERRORES GLOBALES (Opcional pero recomendado)
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'message': 'Recurso no encontrado.'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error interno del servidor.'}), 500

    # 5. RUTA RAÍZ
    @app.route('/')
    def root():
        return jsonify({"success": True, "message": "API de Tworkplate conectada y funcionando correctamente"}), 200

    return app


# Inicialización del servidor
if __name__ == '__main__':
    app = create_app()

    # Contexto de la aplicación para crear tablas si no existen
    with app.app_context():
        db.create_all()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)