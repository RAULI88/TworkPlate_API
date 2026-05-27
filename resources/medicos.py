from flask import Blueprint, request, jsonify
from flask.views import MethodView
from extensions import db
from models import Medico, Empleado, Especialidad
from utils import admin_required, login_required

medicos_bp = Blueprint('medicos', __name__, url_prefix='/api/medicos')


# ─────────────────────────────────────────────
# /api/medicos
# ─────────────────────────────────────────────
class MedicosResource(MethodView):

    @login_required
    def get(self):
        """Lista todos los médicos."""
        especialidad_id = request.args.get('especialidad')
        estado = request.args.get('estado')

        query = Medico.query.join(Empleado)
        if especialidad_id:
            query = query.filter(Medico.id_especialidad == especialidad_id)
        if estado:
            query = query.filter(Empleado.estado == estado)

        medicos = query.order_by(Empleado.nombre_completo).all()
        return jsonify({
            'success': True,
            'data': [m.to_dict() for m in medicos],
            'total': len(medicos)
        }), 200

    @admin_required
    def post(self):
        """
        Registra un nuevo médico. Solo Admin.
        El empleado debe existir y tener tipo_empleado = 'Medico'.
        """
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        campos_requeridos = ['id_empleado', 'id_especialidad', 'cedula_profesional']
        for campo in campos_requeridos:
            if not data.get(campo):
                return jsonify({
                    'success': False,
                    'message': f'El campo {campo} es requerido.'
                }), 400

        empleado = Empleado.query.get(data['id_empleado'])
        if not empleado:
            return jsonify({'success': False, 'message': 'Empleado no encontrado.'}), 404

        if empleado.tipo_empleado != 'Medico':
            return jsonify({
                'success': False,
                'message': 'El empleado no tiene el tipo "Medico".'
            }), 400

        if empleado.medico:
            return jsonify({
                'success': False,
                'message': 'Este empleado ya está registrado como médico.'
            }), 409

        if not Especialidad.query.get(data['id_especialidad']):
            return jsonify({'success': False, 'message': 'Especialidad no encontrada.'}), 404

        if Medico.query.filter_by(cedula_profesional=data['cedula_profesional']).first():
            return jsonify({'success': False, 'message': 'La cédula profesional ya está registrada.'}), 409

        medico = Medico(
            id_empleado=data['id_empleado'],
            id_especialidad=data['id_especialidad'],
            cedula_profesional=data['cedula_profesional'].strip(),
        )
        db.session.add(medico)
        db.session.commit()
        return jsonify({'success': True, 'data': medico.to_dict()}), 201


# ─────────────────────────────────────────────
# /api/medicos/<id>
# ─────────────────────────────────────────────
class MedicoResource(MethodView):

    @login_required
    def get(self, id_medico):
        medico = Medico.query.get_or_404(id_medico)
        return jsonify({'success': True, 'data': medico.to_dict()}), 200

    @admin_required
    def put(self, id_medico):
        """Actualiza un médico. Solo Admin."""
        medico = Medico.query.get_or_404(id_medico)
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        if 'id_especialidad' in data:
            if not Especialidad.query.get(data['id_especialidad']):
                return jsonify({'success': False, 'message': 'Especialidad no encontrada.'}), 404
            medico.id_especialidad = data['id_especialidad']

        if 'cedula_profesional' in data:
            existe = Medico.query.filter(
                Medico.cedula_profesional == data['cedula_profesional'],
                Medico.id_medico != id_medico
            ).first()
            if existe:
                return jsonify({'success': False, 'message': 'La cédula profesional ya existe.'}), 409
            medico.cedula_profesional = data['cedula_profesional'].strip()

        # Actualizar campos del empleado asociado
        emp_data = {k: v for k, v in data.items()
                    if k in ('nombre_completo', 'apellidos', 'telefono', 'estado')}
        if emp_data:
            for campo, valor in emp_data.items():
                setattr(medico.empleado, campo, valor)

        db.session.commit()
        return jsonify({'success': True, 'data': medico.to_dict()}), 200

    @admin_required
    def delete(self, id_medico):
        """Desactiva al empleado asociado al médico. Solo Admin."""
        medico = Medico.query.get_or_404(id_medico)
        medico.empleado.estado = 'Inactivo'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Médico desactivado correctamente.'}), 200


# Registro de rutas
medicos_bp.add_url_rule('',
                        view_func=MedicosResource.as_view('medicos_list'))
medicos_bp.add_url_rule('/<int:id_medico>',
                        view_func=MedicoResource.as_view('medico_detail'))
