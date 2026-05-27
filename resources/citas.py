from flask import Blueprint, request, jsonify
from flask.views import MethodView
from datetime import datetime
from extensions import db
from models import Cita, Paciente, Medico, Servicio
from utils import admin_required, login_required

citas_bp = Blueprint('citas', __name__, url_prefix='/api/citas')

ESTADOS_VALIDOS = ('Agendada', 'En Progreso', 'Completada', 'Cancelada')


# ─────────────────────────────────────────────
# /api/citas
# ─────────────────────────────────────────────
class CitasResource(MethodView):

    @login_required
    def get(self):
        """
        Lista citas. Filtros opcionales:
          - estado: Agendada | En Progreso | Completada | Cancelada
          - id_medico, id_paciente
          - fecha_desde / fecha_hasta (YYYY-MM-DD)
        """
        query = Cita.query

        if (estado := request.args.get('estado')):
            query = query.filter_by(estado=estado)
        if (id_medico := request.args.get('id_medico')):
            query = query.filter_by(id_medico=id_medico)
        if (id_paciente := request.args.get('id_paciente')):
            query = query.filter_by(id_paciente=id_paciente)
        if (fecha_desde := request.args.get('fecha_desde')):
            try:
                query = query.filter(Cita.fecha_hora >= datetime.strptime(fecha_desde, '%Y-%m-%d'))
            except ValueError:
                return jsonify({'success': False, 'message': 'fecha_desde inválida.'}), 400
        if (fecha_hasta := request.args.get('fecha_hasta')):
            try:
                query = query.filter(Cita.fecha_hora <= datetime.strptime(fecha_hasta, '%Y-%m-%d'))
            except ValueError:
                return jsonify({'success': False, 'message': 'fecha_hasta inválida.'}), 400

        citas = query.order_by(Cita.fecha_hora.desc()).all()
        return jsonify({
            'success': True,
            'data': [c.to_dict() for c in citas],
            'total': len(citas)
        }), 200

    @login_required
    def post(self):
        """Agenda una nueva cita."""
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        campos_requeridos = ['id_paciente', 'id_medico', 'id_servicio', 'fecha_hora']
        for campo in campos_requeridos:
            if not data.get(campo):
                return jsonify({
                    'success': False,
                    'message': f'El campo {campo} es requerido.'
                }), 400

        if not Paciente.query.get(data['id_paciente']):
            return jsonify({'success': False, 'message': 'Paciente no encontrado.'}), 404
        if not Medico.query.get(data['id_medico']):
            return jsonify({'success': False, 'message': 'Médico no encontrado.'}), 404
        if not Servicio.query.get(data['id_servicio']):
            return jsonify({'success': False, 'message': 'Servicio no encontrado.'}), 404

        try:
            fecha_hora = datetime.fromisoformat(data['fecha_hora'])
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Formato de fecha_hora inválido. Use ISO 8601: YYYY-MM-DDTHH:MM:SS'
            }), 400

        # Verificar disponibilidad del médico en esa fecha/hora
        conflicto = Cita.query.filter(
            Cita.id_medico == data['id_medico'],
            Cita.fecha_hora == fecha_hora,
            Cita.estado.in_(['Agendada', 'En Progreso'])
        ).first()
        if conflicto:
            return jsonify({
                'success': False,
                'message': 'El médico ya tiene una cita agendada en ese horario.'
            }), 409

        cita = Cita(
            id_paciente=data['id_paciente'],
            id_medico=data['id_medico'],
            id_servicio=data['id_servicio'],
            fecha_hora=fecha_hora,
            estado=data.get('estado', 'Agendada'),
            motivo_visita=data.get('motivo_visita'),
        )
        db.session.add(cita)
        db.session.commit()
        return jsonify({'success': True, 'data': cita.to_dict()}), 201


# ─────────────────────────────────────────────
# /api/citas/<id>
# ─────────────────────────────────────────────
class CitaResource(MethodView):

    @login_required
    def get(self, id_cita):
        cita = Cita.query.get_or_404(id_cita)
        return jsonify({'success': True, 'data': cita.to_dict()}), 200

    @login_required
    def put(self, id_cita):
        """Actualiza una cita."""
        cita = Cita.query.get_or_404(id_cita)
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        if cita.estado == 'Cancelada':
            return jsonify({'success': False, 'message': 'No se puede editar una cita cancelada.'}), 400

        if 'estado' in data:
            if data['estado'] not in ESTADOS_VALIDOS:
                return jsonify({'success': False, 'message': 'estado inválido.'}), 400
            cita.estado = data['estado']

        if 'fecha_hora' in data:
            try:
                cita.fecha_hora = datetime.fromisoformat(data['fecha_hora'])
            except ValueError:
                return jsonify({'success': False, 'message': 'Formato de fecha_hora inválido.'}), 400

        if 'motivo_visita' in data: cita.motivo_visita = data['motivo_visita']
        if 'id_servicio' in data:
            if not Servicio.query.get(data['id_servicio']):
                return jsonify({'success': False, 'message': 'Servicio no encontrado.'}), 404
            cita.id_servicio = data['id_servicio']

        db.session.commit()
        return jsonify({'success': True, 'data': cita.to_dict()}), 200

    @login_required
    def delete(self, id_cita):
        """Cancela una cita (soft delete)."""
        cita = Cita.query.get_or_404(id_cita)
        if cita.estado == 'Completada':
            return jsonify({'success': False, 'message': 'No se puede cancelar una cita completada.'}), 400
        cita.estado = 'Cancelada'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Cita cancelada correctamente.'}), 200


# ─────────────────────────────────────────────
# PATCH /api/citas/<id>/estado
# ─────────────────────────────────────────────
class CitaEstadoResource(MethodView):

    @login_required
    def patch(self, id_cita):
        """Cambia únicamente el estado de una cita."""
        cita = Cita.query.get_or_404(id_cita)
        data = request.get_json()
        estado = data.get('estado') if data else None

        if not estado or estado not in ESTADOS_VALIDOS:
            return jsonify({
                'success': False,
                'message': f'estado requerido. Valores válidos: {ESTADOS_VALIDOS}'
            }), 400

        cita.estado = estado
        db.session.commit()
        return jsonify({'success': True, 'data': cita.to_dict()}), 200


# Registro de rutas
citas_bp.add_url_rule('',
                      view_func=CitasResource.as_view('citas_list'))
citas_bp.add_url_rule('/<int:id_cita>',
                      view_func=CitaResource.as_view('cita_detail'))
citas_bp.add_url_rule('/<int:id_cita>/estado',
                      view_func=CitaEstadoResource.as_view('cita_estado'))
