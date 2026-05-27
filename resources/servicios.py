from flask import Blueprint, request, jsonify
from flask.views import MethodView
from extensions import db
from models import Servicio
from utils import admin_required, login_required

servicios_bp = Blueprint('servicios', __name__, url_prefix='/api/servicios')


# ─────────────────────────────────────────────
# /api/servicios   →   ServiciosResource
# ─────────────────────────────────────────────
class ServiciosResource(MethodView):

    @login_required
    def get(self):
        """Lista todos los servicios."""
        servicios = Servicio.query.order_by(Servicio.nombre_servicio).all()
        return jsonify({
            'success': True,
            'data':  [s.to_dict() for s in servicios],
            'total': len(servicios)
        }), 200

    @admin_required
    def post(self):
        """Crea un nuevo servicio. Solo Admin."""
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        campos_requeridos = ['nombre_servicio', 'costo', 'duracion_estimada']
        for campo in campos_requeridos:
            if data.get(campo) is None:
                return jsonify({
                    'success': False,
                    'message': f'El campo {campo} es requerido.'
                }), 400

        try:
            costo    = float(data['costo'])
            duracion = int(data['duracion_estimada'])
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'costo y duracion_estimada deben ser numéricos.'}), 400

        if costo < 0 or duracion < 1:
            return jsonify({'success': False, 'message': 'costo >= 0 y duracion_estimada >= 1.'}), 400

        servicio = Servicio(
            nombre_servicio   = data['nombre_servicio'].strip(),
            descripcion       = data.get('descripcion'),
            costo             = costo,
            duracion_estimada = duracion,
        )
        db.session.add(servicio)
        db.session.commit()
        return jsonify({'success': True, 'data': servicio.to_dict()}), 201


# ─────────────────────────────────────────────
# /api/servicios/<id>   →   ServicioResource
# ─────────────────────────────────────────────
class ServicioResource(MethodView):

    @login_required
    def get(self, id_servicio):
        """Obtiene un servicio por ID."""
        servicio = Servicio.query.get_or_404(id_servicio)
        return jsonify({'success': True, 'data': servicio.to_dict()}), 200

    @admin_required
    def put(self, id_servicio):
        """Actualiza un servicio. Solo Admin."""
        servicio = Servicio.query.get_or_404(id_servicio)
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        if 'nombre_servicio' in data:
            servicio.nombre_servicio = data['nombre_servicio'].strip()
        if 'descripcion' in data:
            servicio.descripcion = data['descripcion']
        if 'costo' in data:
            try:
                servicio.costo = float(data['costo'])
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'costo debe ser numérico.'}), 400
        if 'duracion_estimada' in data:
            try:
                servicio.duracion_estimada = int(data['duracion_estimada'])
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'duracion_estimada debe ser entero.'}), 400

        db.session.commit()
        return jsonify({'success': True, 'data': servicio.to_dict()}), 200

    @admin_required
    def delete(self, id_servicio):
        """Elimina un servicio. Solo Admin."""
        servicio = Servicio.query.get_or_404(id_servicio)
        if servicio.citas:
            return jsonify({
                'success': False,
                'message': 'No se puede eliminar: hay citas asociadas a este servicio.'
            }), 409
        db.session.delete(servicio)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Servicio eliminado.'}), 200


# Registro de rutas
servicios_bp.add_url_rule('',
    view_func=ServiciosResource.as_view('servicios_list'))
servicios_bp.add_url_rule('/<int:id_servicio>',
    view_func=ServicioResource.as_view('servicio_detail'))