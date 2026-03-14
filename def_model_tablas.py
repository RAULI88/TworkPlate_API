import flask_bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
# 1. Instanciamos el objeto 'db' de SQLAlchemy.
# Este objeto será el padre del que heredarán todas nuestras clases (modelos).
db = SQLAlchemy()
bcrypt = Bcrypt()
# 2. Definición de la clase Usuario (Hereda de db.Model)
class Usuario(db.Model):
    __tablename__ = 'usuario'

    # Atributos del objeto (Columnas de la tabla)
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    ap1 = db.Column(db.String(100), nullable=False)
    ap2 = db.Column(db.String(100), nullable=True)
    correo = db.Column(db.String(150), unique=True, nullable=False)
    contra = db.Column(db.String(255), nullable=False) # Asumiendo que ampliarás a 255 en DBeaver
    rol = db.Column(db.Integer, nullable=False)

    # Relación a nivel de objetos: Flask automáticamente creará una lista de
    # objetos 'Funcionalidad' dentro de cada objeto 'Usuario'.
    funcionalidades = db.relationship('Funcionalidad', backref='usuario_dueno', lazy=True)

    # Método del objeto para convertir su información en un diccionario (JSON)
    def to_dict(self):
        return {
            "id_usuario": self.id_usuario,
            "nombre": self.nombre,
            "ap1": self.ap1,
            "ap2": self.ap2,
            "correo": self.correo,
            "rol": self.rol
        }


# 3. Definición de la clase Funcionalidad (Hereda de db.Model)
class Funcionalidad(db.Model):
    __tablename__ = 'funcionalidad'

    # Atributos del objeto
    id_funcionalidad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    json_fun = db.Column(db.String(5000), nullable=False)

    # Método del objeto
    def to_dict(self):
        return {
            "id_funcionalidad": self.id_funcionalidad,
            "id_usuario": self.id_usuario,
            "json_fun": self.json_fun
        }