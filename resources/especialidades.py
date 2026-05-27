from flask import Blueprint, request, jsonify
from flask.views import MethodView
from extensions import db
from models import Especialidad
from utils import admin_required, login_required

especialidades_bp = Blueprint('especialidades', __name__, url_prefix='/api/especialidades')


# ─────────────────────────────────────────────
# /api/especialidades   →   EspecialidadesResource
# ─────────────────────────────────────────────
class EspecialidadesResource(MethodView):

    @login_required
    def get(self):
        """Lista todas las especialidades."""
        especialidades = Especialidad.query.order_by(Especialidad.nombre).all()
        return jsonify({
            'success': True,
            'data':  [e.to_dict() for e in especialidades],
            'total': len(especialidades)
        }), 200

    @admin_required
    def post(self):
        """Crea una nueva especialidad. Solo Admin."""
        data = request.get_json()
        if not data or not data.get('nombre'):
            return jsonify({'success': False, 'message': 'El campo nombre es requerido.'}), 400

        if Especialidad.query.filter_by(nombre=data['nombre']).first():
            return jsonify({'success': False, 'message': 'La especialidad ya existe.'}), 409

        especialidad = Especialidad(
            nombre      = data['nombre'].strip(),
            descripcion = data.get('descripcion'),
        )
        db.session.add(especialidad)
        db.session.commit()
        return jsonify({'success': True, 'data': especialidad.to_dict()}), 201


# ─────────────────────────────────────────────
# /api/especialidades/<id>   →   EspecialidadResource
# ─────────────────────────────────────────────
class EspecialidadResource(MethodView):

    @login_required
    def get(self, id_especialidad):
        """Obtiene una especialidad por ID."""
        especialidad = Especialidad.query.get_or_404(id_especialidad)
        return jsonify({'success': True, 'data': especialidad.to_dict()}), 200

    @admin_required
    def put(self, id_especialidad):
        """Actualiza una especialidad. Solo Admin."""
        especialidad = Especialidad.query.get_or_404(id_especialidad)
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        if 'nombre' in data:
            existe = Especialidad.query.filter(
                Especialidad.nombre == data['nombre'],
                Especialidad.id_especialidad != id_especialidad
            ).first()
            if existe:
                return jsonify({'success': False, 'message': 'La especialidad ya existe.'}), 409
            especialidad.nombre = data['nombre'].strip()

        if 'descripcion' in data:
            especialidad.descripcion = data['descripcion']

        db.session.commit()
        return jsonify({'success': True, 'data': especialidad.to_dict()}), 200

    @admin_required
    def delete(self, id_especialidad):
        """Elimina una especialidad. Solo Admin."""
        especialidad = Especialidad.query.get_or_404(id_especialidad)
        if especialidad.medicos:
            return jsonify({
                'success': False,
                'message': 'No se puede eliminar: hay médicos asignados a esta especialidad.'
            }), 409
        db.session.delete(especialidad)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Especialidad eliminada.'}), 200


# Registro de rutas
especialidades_bp.add_url_rule('',
    view_func=EspecialidadesResource.as_view('especialidades_list'))
especialidades_bp.add_url_rule('/<int:id_especialidad>',
    view_func=EspecialidadResource.as_view('especialidad_detail'))