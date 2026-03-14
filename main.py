from flask import Flask, jsonify, request
import os
from dotenv import load_dotenv
from sqlalchemy import select, text, func, desc
from flask_bcrypt import Bcrypt
from flask_cors import CORS

# 1. Importa el objeto de los modelos
from def_model_tablas import db, Usuario, Funcionalidad

# --- AQUÍ IMPORTAMOS LOS BLUEPRINTS DE TUS OTROS ARCHIVOS ---
from usuario import usuario_bp
from funcionalidades import func_bp

# CARGA DE VARIABLES DE ENTORNO
load_dotenv()

app = Flask(__name__)
CORS(app)

# CONFIGURACIÓN DE CONEXIÓN A LA BASE DE DATOS
DB_USER = os.environ.get("MYSQLUSER")
DB_PASS = os.environ.get("MYSQLPASSWORD")
DB_HOST = os.environ.get("MYSQLHOST")
DB_PORT = os.environ.get("MYSQLPORT")
DB_NAME = os.environ.get("MYSQLDATABASE")

# Construye la URI de conexión
app.config['SQLALCHEMY_DATABASE_URI'] = \
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 2. INYECCIÓN DE DEPENDENCIAS
db.init_app(app)
bcrypt = Bcrypt(app)

# --- 3. REGISTRO DE RUTAS (BLUEPRINTS) ---
# Esto es lo que faltaba para que /api/usuarios y /api/funcionalidades funcionen
app.register_blueprint(usuario_bp, url_prefix='/api')
app.register_blueprint(func_bp, url_prefix='/api')

# 4. CONTEXTO DE APLICACIÓN
with app.app_context():
    db.create_all()

@app.route('/')
def root():
    return jsonify("API conectada y funcionando correctamente"), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)