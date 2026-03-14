from flask import Flask, jsonify, request
import os
from dotenv import load_dotenv
from sqlalchemy import select, text, func, desc
from flask_bcrypt import Bcrypt
from flask_cors import CORS

# 1. Importa el objeto de los modelos de las tablas de la base de datos
from def_model_tablas import db, Usuario, Funcionalidad

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

# 2. INYECCIÓN DE DEPENDENCIAS: Vinculamos la app a nuestro objeto 'db' existente
db.init_app(app)
bcrypt = Bcrypt(app)  # Inicializa Bcrypt

# 3. CONTEXTO DE APLICACIÓN: Sincroniza las clases OOP con las tablas reales
with app.app_context():
    db.create_all()



@app.route('/')
def root():
    return jsonify("API conectada y funcionando"), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
