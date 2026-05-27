from flask import Blueprint, request, jsonify
from flask.views import MethodView
from extensions import db
from models import Empleado
from utils import admin_required, login_required
from datetime import datetime

empleados_bp = Blueprint('empleados', __name__, url_prefix='/api/empleados')

TIPOS_VALIDOS = ('Medico', 'Recepcionista', 'Administrador', 'Otro')
ESTADOS_VALIDOS = ('Activo', 'Inactivo')


# ─────────────────────────────────────────────
# /api/empleados
# ─────────────────────────────────────────────
class EmpleadosResource(MethodView):

    @login_required
    def get(self):
        """Lista todos los empleados."""
        tipo = request.args.get('tipo')
        estado = request.args.get('estado', 'Activo')

        query = Empleado.query
        if tipo:
            query = query.filter_by(tipo_empleado=tipo)
        if estado:
            query = query.filter_by(estado=estado)

        empleados = query.order_by(Empleado.nombre_completo).all()
        return jsonify({
            'success': True,
            'data': [e.to_dict() for e in empleados],
            'total': len(empleados)
        }), 200

    @admin_required
    def post(self):
        """Crea un nuevo empleado. Solo Admin."""
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        campos_requeridos = ['nombre_completo', 'apellidos', 'tipo_empleado', 'fecha_contratacion']
        for campo in campos_requeridos:
            if not data.get(campo):
                return jsonify({
                    'success': False,
                    'message': f'El campo {campo} es requerido.'
                }), 400

        if data['tipo_empleado'] not in TIPOS_VALIDOS:
            return jsonify({
                'success': False,
                'message': f'tipo_empleado debe ser uno de: {TIPOS_VALIDOS}'
            }), 400

        if data.get('email'):
            existe = Empleado.query.filter_by(email=data['email']).first()
            if existe:
                return jsonify({'success': False, 'message': 'El email ya está registrado.'}), 409

        try:
            fecha = datetime.strptime(data['fecha_contratacion'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Formato de fecha inválido. Use YYYY-MM-DD.'}), 400

        empleado = Empleado(
            nombre_completo=data['nombre_completo'].strip(),
            apellidos=data['apellidos'].strip(),
            telefono=data.get('telefono'),
            email=data.get('email'),
            tipo_empleado=data['tipo_empleado'],
            estado=data.get('estado', 'Activo'),
            fecha_contratacion=fecha,
        )
        db.session.add(empleado)
        db.session.commit()

        return jsonify({'success': True, 'data': empleado.to_dict()}), 201


# ─────────────────────────────────────────────
# /api/empleados/<id>
# ─────────────────────────────────────────────
class EmpleadoResource(MethodView):

    @login_required
    def get(self, id_empleado):
        """Obtiene un empleado por ID."""
        empleado = Empleado.query.get_or_404(id_empleado)
        return jsonify({'success': True, 'data': empleado.to_dict()}), 200

    @admin_required
    def put(self, id_empleado):
        """Actualiza un empleado. Solo Admin."""
        empleado = Empleado.query.get_or_404(id_empleado)
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        if 'nombre_completo' in data:
            empleado.nombre_completo = data['nombre_completo'].strip()
        if 'apellidos' in data:
            empleado.apellidos = data['apellidos'].strip()
        if 'telefono' in data:
            empleado.telefono = data['telefono']
        if 'email' in data:
            existe = Empleado.query.filter(
                Empleado.email == data['email'],
                Empleado.id_empleado != id_empleado
            ).first()
            if existe:
                return jsonify({'success': False, 'message': 'El email ya está registrado.'}), 409
            empleado.email = data['email']
        if 'tipo_empleado' in data:
            if data['tipo_empleado'] not in TIPOS_VALIDOS:
                return jsonify({'success': False, 'message': 'tipo_empleado inválido.'}), 400
            empleado.tipo_empleado = data['tipo_empleado']
        if 'estado' in data:
            if data['estado'] not in ESTADOS_VALIDOS:
                return jsonify({'success': False, 'message': 'estado inválido.'}), 400
            empleado.estado = data['estado']
        if 'fecha_contratacion' in data:
            try:
                empleado.fecha_contratacion = datetime.strptime(
                    data['fecha_contratacion'], '%Y-%m-%d'
                ).date()
            except ValueError:
                return jsonify({'success': False, 'message': 'Formato de fecha inválido.'}), 400

        db.session.commit()
        return jsonify({'success': True, 'data': empleado.to_dict()}), 200

    @admin_required
    def delete(self, id_empleado):
        """Elimina un empleado. Solo Admin."""
        empleado = Empleado.query.get_or_404(id_empleado)
        # Soft delete: marcar como Inactivo en lugar de borrar
        empleado.estado = 'Inactivo'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Empleado desactivado correctamente.'}), 200


# Registro de rutas
empleados_bp.add_url_rule('',
                          view_func=EmpleadosResource.as_view('empleados_list'))
empleados_bp.add_url_rule('/<int:id_empleado>',
                          view_func=EmpleadoResource.as_view('empleado_detail'))
