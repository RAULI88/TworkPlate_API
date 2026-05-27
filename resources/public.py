from flask import Blueprint, request, jsonify
from flask.views import MethodView
from extensions import db
from models import Servicio, Medico, Empleado

public_bp = Blueprint('public', __name__, url_prefix='/api/public')


# ─────────────────────────────────────────────
# /api/public/servicios   →   PublicServiciosResource
# ─────────────────────────────────────────────
class PublicServiciosResource(MethodView):

    def get(self):
        """Catálogo de servicios para la landing page. Sin autenticación."""
        servicios = Servicio.query.order_by(Servicio.nombre_servicio).all()
        return jsonify({'success': True, 'data': [s.to_dict() for s in servicios]}), 200


# ─────────────────────────────────────────────
# /api/public/medicos   →   PublicMedicosResource
# ─────────────────────────────────────────────
class PublicMedicosResource(MethodView):

    def get(self):
        """Médicos activos para la landing page. Sin autenticación."""
        medicos = (
            Medico.query
            .join(Empleado)
            .filter(Empleado.estado == 'Activo')
            .order_by(Empleado.nombre_completo)
            .all()
        )
        return jsonify({'success': True, 'data': [m.to_dict() for m in medicos]}), 200


# ─────────────────────────────────────────────
# /api/public/solicitar-cita   →   PublicSolicitarCitaResource
# ─────────────────────────────────────────────
class PublicSolicitarCitaResource(MethodView):

    def post(self):
        """Recibe solicitud de cita desde el formulario de la landing page."""
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        campos_requeridos = ['nombre_completo', 'telefono']
        for campo in campos_requeridos:
            if not data.get(campo):
                return jsonify({
                    'success': False,
                    'message': f'El campo {campo} es requerido.'
                }), 400

        return jsonify({
            'success': True,
            'message': (
                f"Solicitud recibida. Nos pondremos en contacto "
                f"al {data['telefono']} para confirmar tu cita."
            ),
            'data': {
                'nombre_completo': data.get('nombre_completo'),
                'telefono':        data.get('telefono'),
                'email':           data.get('email'),
                'servicio':        data.get('servicio'),
                'notas':           data.get('notas'),
            }
        }), 200


# Registro de rutas
public_bp.add_url_rule('/servicios',
    view_func=PublicServiciosResource.as_view('public_servicios'))
public_bp.add_url_rule('/medicos',
    view_func=PublicMedicosResource.as_view('public_medicos'))
public_bp.add_url_rule('/solicitar-cita',
    view_func=PublicSolicitarCitaResource.as_view('public_solicitar_cita'))