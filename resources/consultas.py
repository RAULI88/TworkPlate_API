from flask import Blueprint, request, jsonify
from flask.views import MethodView
from extensions import db
from models import Consulta, Cita
from utils import login_required, admin_required

consultas_bp = Blueprint('consultas', __name__, url_prefix='/api/consultas')


# ─────────────────────────────────────────────
# /api/consultas
# ─────────────────────────────────────────────
class ConsultasResource(MethodView):

    @login_required
    def get(self):
        """Lista todas las consultas. Filtro opcional por id_paciente."""
        id_paciente = request.args.get('id_paciente')

        query = Consulta.query.join(Cita)
        if id_paciente:
            query = query.filter(Cita.id_paciente == id_paciente)

        consultas = query.order_by(Cita.fecha_hora.desc()).all()
        return jsonify({
            'success': True,
            'data': [c.to_dict() for c in consultas],
            'total': len(consultas)
        }), 200

    @login_required
    def post(self):
        """
        Registra una nueva consulta.
        La cita asociada debe existir y estar en estado 'Completada' o 'En Progreso'.
        """
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        if not data.get('id_cita'):
            return jsonify({'success': False, 'message': 'El campo id_cita es requerido.'}), 400

        cita = Cita.query.get(data['id_cita'])
        if not cita:
            return jsonify({'success': False, 'message': 'Cita no encontrada.'}), 404

        if cita.estado not in ('En Progreso', 'Completada'):
            return jsonify({
                'success': False,
                'message': 'Solo se puede registrar consulta para citas "En Progreso" o "Completadas".'
            }), 400

        if cita.consulta:
            return jsonify({
                'success': False,
                'message': 'Esta cita ya tiene una consulta registrada.'
            }), 409

        consulta = Consulta(
            id_cita=data['id_cita'],
            sintomas=data.get('sintomas'),
            diagnostico=data.get('diagnostico'),
            tratamiento=data.get('tratamiento'),
            receta_medica=data.get('receta_medica'),
        )
        # Marcar cita como completada automáticamente
        cita.estado = 'Completada'

        db.session.add(consulta)
        db.session.commit()
        return jsonify({'success': True, 'data': consulta.to_dict()}), 201


# ─────────────────────────────────────────────
# /api/consultas/<id>
# ─────────────────────────────────────────────
class ConsultaResource(MethodView):

    @login_required
    def get(self, id_consulta):
        consulta = Consulta.query.get_or_404(id_consulta)
        return jsonify({'success': True, 'data': consulta.to_dict()}), 200

    @login_required
    def put(self, id_consulta):
        """Actualiza una consulta."""
        consulta = Consulta.query.get_or_404(id_consulta)
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        if 'sintomas' in data: consulta.sintomas = data['sintomas']
        if 'diagnostico' in data: consulta.diagnostico = data['diagnostico']
        if 'tratamiento' in data: consulta.tratamiento = data['tratamiento']
        if 'receta_medica' in data: consulta.receta_medica = data['receta_medica']

        db.session.commit()
        return jsonify({'success': True, 'data': consulta.to_dict()}), 200

    @admin_required
    def delete(self, id_consulta):
        """Elimina una consulta. Solo Admin."""
        consulta = Consulta.query.get_or_404(id_consulta)
        db.session.delete(consulta)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Consulta eliminada.'}), 200


# Registro de rutas
consultas_bp.add_url_rule('',
                          view_func=ConsultasResource.as_view('consultas_list'))
consultas_bp.add_url_rule('/<int:id_consulta>',
                          view_func=ConsultaResource.as_view('consulta_detail'))
