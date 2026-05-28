from flask import Blueprint, request, jsonify
from flask.views import MethodView
from extensions import db
from models import Pago, Cita
from utils import login_required, admin_required
from flask_jwt_extended import get_jwt

pagos_bp = Blueprint('pagos', __name__, url_prefix='/api/pagos')

METODOS_VALIDOS = ('Efectivo', 'Tarjeta', 'Transferencia')


# ─────────────────────────────────────────────
# /api/pagos
# ─────────────────────────────────────────────
class PagosResource(MethodView):

    @login_required
    def get(self):
        """Lista pagos con seguridad por rol."""
        query = Pago.query

        # --- SEGURIDAD DE LECTURA (RBAC) ---
        claims = get_jwt()
        if claims.get('rol') == 'Paciente':
            # Unimos la tabla Cita para poder filtrar por el dueño de la cita pagada
            id_paciente_token = claims.get('id_paciente')
            query = query.join(Cita).filter(Cita.id_paciente == id_paciente_token)
        # -----------------------------------

        pagos = query.order_by(Pago.fecha_pago.desc()).all()
        return jsonify({
            'success': True,
            'data': [p.to_dict() for p in pagos],
            'total': len(pagos)
        }), 200

    @login_required
    def post(self):
        """Registra un pago para una cita. Protegido contra pagos ajenos."""
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        campos_requeridos = ['id_cita', 'monto_total', 'metodo_pago']
        for campo in campos_requeridos:
            if data.get(campo) is None:
                return jsonify({
                    'success': False,
                    'message': f'El campo {campo} es requerido.'
                }), 400

        cita = Cita.query.get(data['id_cita'])
        if not cita:
            return jsonify({'success': False, 'message': 'Cita no encontrada.'}), 404

        # --- SEGURIDAD DE ESCRITURA (RBAC) ---
        claims = get_jwt()
        if claims.get('rol') == 'Paciente' and cita.id_paciente != claims.get('id_paciente'):
            return jsonify({'success': False, 'message': 'No tienes permiso para pagar esta cita.'}), 403
        # -----------------------------------

        if cita.pago:
            return jsonify({'success': False, 'message': 'Esta cita ya tiene un pago registrado.'}), 409

        if data['metodo_pago'] not in METODOS_VALIDOS:
            return jsonify({
                'success': False,
                'message': f'metodo_pago debe ser uno de: {METODOS_VALIDOS}'
            }), 400

        try:
            monto = float(data['monto_total'])
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'monto_total debe ser numérico.'}), 400

        if monto < 0:
            return jsonify({'success': False, 'message': 'monto_total debe ser >= 0.'}), 400

        pago = Pago(
            id_cita=data['id_cita'],
            monto_total=monto,
            metodo_pago=data['metodo_pago'],
        )
        db.session.add(pago)
        db.session.commit()
        return jsonify({'success': True, 'data': pago.to_dict()}), 201


# ─────────────────────────────────────────────
# /api/pagos/<id>
# ─────────────────────────────────────────────
class PagoResource(MethodView):

    @login_required
    def get(self, id_pago):
        """Ve un pago específico. Protegido por dueño."""
        pago = Pago.query.get_or_404(id_pago)

        # --- SEGURIDAD (RBAC) ---
        claims = get_jwt()
        if claims.get('rol') == 'Paciente':
            cita = Cita.query.get(pago.id_cita)
            if cita and cita.id_paciente != claims.get('id_paciente'):
                return jsonify({'success': False, 'message': 'Acceso denegado.'}), 403
        # -----------------------------------

        return jsonify({'success': True, 'data': pago.to_dict()}), 200

    @login_required
    def put(self, id_pago):
        """Actualiza un pago. Solo empleados."""
        # --- SEGURIDAD (RBAC): Bloquear a pacientes ---
        claims = get_jwt()
        if claims.get('rol') == 'Paciente':
            return jsonify({'success': False, 'message': 'Los pacientes no tienen permiso para editar pagos.'}), 403
        # -----------------------------------

        pago = Pago.query.get_or_404(id_pago)
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Body requerido.'}), 400

        if 'monto_total' in data:
            try:
                pago.monto_total = float(data['monto_total'])
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'monto_total inválido.'}), 400

        if 'metodo_pago' in data:
            if data['metodo_pago'] not in METODOS_VALIDOS:
                return jsonify({'success': False, 'message': 'metodo_pago inválido.'}), 400
            pago.metodo_pago = data['metodo_pago']

        db.session.commit()
        return jsonify({'success': True, 'data': pago.to_dict()}), 200

    @admin_required
    def delete(self, id_pago):
        """Elimina un pago. Solo Admin."""
        pago = Pago.query.get_or_404(id_pago)
        db.session.delete(pago)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Pago eliminado.'}), 200


# Registro de rutas
pagos_bp.add_url_rule('',
                      view_func=PagosResource.as_view('pagos_list'))
pagos_bp.add_url_rule('/<int:id_pago>',
                      view_func=PagoResource.as_view('pago_detail'))