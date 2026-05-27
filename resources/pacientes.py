from flask import Blueprint, request, jsonify
from flask.views import MethodView
from datetime import datetime
from extensions import db
from models import Paciente
from utils import admin_required, login_required

pacientes_bp = Blueprint('pacientes', __name__, url_prefix='/api/pacientes')


# ─────────────────────────────────────────────
# /api/pacientes   →   PacientesResource
# ─────────────────────────────────────────────
class PacientesResource(MethodView):

    @login_required
    def get(self):
        """Lista todos los pacientes. Soporta búsqueda por nombre."""
        busqueda = request.args.get('busqueda', '').strip()

        query = Paciente.query
        if busqueda:
            like = f'%{busqueda}%'
            query = query.filter(
                db.or_(
                    Paciente.nombre.ilike(like),
                    Paciente.apellidos.ilike(like),
                    Paciente.curp.ilike(like),
                    Paciente.rfc.ilike(like),
                )
            )

        pacientes = query.order_by(Paciente.apellidos, Paciente.nombre).all()
        return jsonify({
            'success': True,
            'data':  [p.to_dict() for p in pacientes],
            'total': len(pacientes)
        }), 200

    @login_required
    def post(self):
        """Registra un nuevo paciente."""
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        campos_requeridos = ['nombre', 'apellidos', 'fecha_nacimiento']
        for campo in campos_requeridos:
            if not data.get(campo):
                return jsonify({
                    'success': False,
                    'message': f'El campo {campo} es requerido.'
                }), 400

        try:
            fecha_nac = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Formato de fecha inválido. Use YYYY-MM-DD.'}), 400

        if data.get('curp'):
            if Paciente.query.filter_by(curp=data['curp']).first():
                return jsonify({'success': False, 'message': 'El CURP ya está registrado.'}), 409
        if data.get('rfc'):
            if Paciente.query.filter_by(rfc=data['rfc']).first():
                return jsonify({'success': False, 'message': 'El RFC ya está registrado.'}), 409

        paciente = Paciente(
            nombre           = data['nombre'].strip(),
            apellidos        = data['apellidos'].strip(),
            fecha_nacimiento = fecha_nac,
            telefono         = data.get('telefono'),
            email            = data.get('email'),
            curp             = data.get('curp'),
            rfc              = data.get('rfc'),
        )
        db.session.add(paciente)
        db.session.commit()
        return jsonify({'success': True, 'data': paciente.to_dict()}), 201


# ─────────────────────────────────────────────
# /api/pacientes/<id>   →   PacienteResource
# ─────────────────────────────────────────────
class PacienteResource(MethodView):

    @login_required
    def get(self, id_paciente):
        """Obtiene un paciente por ID."""
        paciente = Paciente.query.get_or_404(id_paciente)
        return jsonify({'success': True, 'data': paciente.to_dict()}), 200

    @login_required
    def put(self, id_paciente):
        """Actualiza un paciente."""
        paciente = Paciente.query.get_or_404(id_paciente)
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        if 'nombre'    in data: paciente.nombre    = data['nombre'].strip()
        if 'apellidos' in data: paciente.apellidos = data['apellidos'].strip()
        if 'telefono'  in data: paciente.telefono  = data['telefono']
        if 'email'     in data: paciente.email     = data['email']

        if 'fecha_nacimiento' in data:
            try:
                paciente.fecha_nacimiento = datetime.strptime(
                    data['fecha_nacimiento'], '%Y-%m-%d'
                ).date()
            except ValueError:
                return jsonify({'success': False, 'message': 'Formato de fecha inválido.'}), 400

        if 'curp' in data:
            existe = Paciente.query.filter(
                Paciente.curp == data['curp'],
                Paciente.id_paciente != id_paciente
            ).first()
            if existe:
                return jsonify({'success': False, 'message': 'El CURP ya existe.'}), 409
            paciente.curp = data['curp']

        if 'rfc' in data:
            existe = Paciente.query.filter(
                Paciente.rfc == data['rfc'],
                Paciente.id_paciente != id_paciente
            ).first()
            if existe:
                return jsonify({'success': False, 'message': 'El RFC ya existe.'}), 409
            paciente.rfc = data['rfc']

        db.session.commit()
        return jsonify({'success': True, 'data': paciente.to_dict()}), 200

    @admin_required
    def delete(self, id_paciente):
        """Elimina un paciente. Solo Admin."""
        paciente = Paciente.query.get_or_404(id_paciente)
        if paciente.citas:
            return jsonify({
                'success': False,
                'message': 'No se puede eliminar: el paciente tiene citas registradas.'
            }), 409
        db.session.delete(paciente)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Paciente eliminado.'}), 200


# Registro de rutas
pacientes_bp.add_url_rule('',
    view_func=PacientesResource.as_view('pacientes_list'))
pacientes_bp.add_url_rule('/<int:id_paciente>',
    view_func=PacienteResource.as_view('paciente_detail'))