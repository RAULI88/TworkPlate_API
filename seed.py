"""
Script para crear el primer usuario Admin en la base de datos.
Ejecutar una sola vez después de aplicar las migraciones:

    python seed.py
"""
from datetime import date
from werkzeug.security import generate_password_hash
from app import create_app
from extensions import db
from models import Empleado, Usuario, Especialidad


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        # ── Empleado Admin ──────────────────────────────────
        if not Empleado.query.filter_by(email='admin@clinica.com').first():
            admin_emp = Empleado(
                nombre_completo='Administrador',
                apellidos='Principal',
                telefono='555-0000',
                email='admin@clinica.com',
                tipo_empleado='Administrador',
                estado='Activo',
                fecha_contratacion=date.today(),
            )
            db.session.add(admin_emp)
            db.session.flush()  # obtener id_empleado sin commit

            admin_usr = Usuario(
                id_empleado=admin_emp.id_empleado,
                nombre_usuario='admin',
                password_hash=generate_password_hash('Admin1234!'),
                rol='Admin',
                estado='Activo',
            )
            db.session.add(admin_usr)
            print('✅  Usuario Admin creado  →  usuario: admin  |  password: Admin1234!')
        else:
            print('ℹ️   Usuario Admin ya existe, omitiendo.')

        # ── Especialidades de ejemplo ───────────────────────
        especialidades_base = [
            ('Medicina General', 'Atención primaria y consultas generales'),
            ('Pediatría', 'Atención médica para niños y adolescentes'),
            ('Odontología', 'Salud dental y bucal'),
            ('Rayos X', 'Diagnóstico por imagen'),
            ('Análisis Clínicos', 'Estudios de laboratorio'),
        ]
        for nombre, descripcion in especialidades_base:
            if not Especialidad.query.filter_by(nombre=nombre).first():
                db.session.add(Especialidad(nombre=nombre, descripcion=descripcion))

        db.session.commit()
        print('✅  Especialidades base cargadas.')
        print('\n🚀  Seed completado. Puedes iniciar sesión en POST /api/auth/login')


if __name__ == '__main__':
    seed()
