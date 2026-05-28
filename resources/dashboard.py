from flask import Blueprint, jsonify
from flask.views import MethodView
from datetime import date
from sqlalchemy import func, extract
from extensions import db
from models import Cita, Medico, Empleado, Pago
from utils import login_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


class DashboardResource(MethodView):

    @login_required
    def get(self):
        """Obtiene las métricas resumidas para el panel de control."""
        hoy = date.today()
        mes_actual = hoy.month
        anio_actual = hoy.year

        # 1. Calcular Citas de Hoy
        # Filtramos extrayendo solo la parte de la fecha de la columna fecha_hora
        citas_hoy = db.session.query(func.count(Cita.id_cita)).filter(
            func.date(Cita.fecha_hora) == hoy
        ).scalar() or 0

        # 2. Calcular Médicos Activos
        medicos_activos = db.session.query(func.count(Medico.id_medico)).join(Empleado).filter(
            Empleado.estado == 'Activo'
        ).scalar() or 0

        # 3. Calcular Ingresos del Mes
        # Sumamos el monto de los pagos que pertenecen a las citas de este mes
        ingresos_mes = db.session.query(func.sum(Pago.monto_total)).join(Cita).filter(
            extract('month', Cita.fecha_hora) == mes_actual,
            extract('year', Cita.fecha_hora) == anio_actual
        ).scalar() or 0.0

        return jsonify({
            'success': True,
            'data': {
                'citas_hoy': citas_hoy,
                'medicos_activos': medicos_activos,
                'ingresos_mes': float(ingresos_mes)
            }
        }), 200


# Registro de la ruta
dashboard_bp.add_url_rule('', view_func=DashboardResource.as_view('dashboard_metrics'))