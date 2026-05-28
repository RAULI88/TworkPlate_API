from extensions import db
from datetime import datetime, date


# ─────────────────────────────────────────────
# EMPLEADOS
# ─────────────────────────────────────────────
class Empleado(db.Model):
    __tablename__ = 'empleados'

    id_empleado = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(15))
    email = db.Column(db.String(100), unique=True)
    tipo_empleado = db.Column(
        db.Enum('Medico', 'Recepcionista', 'Administrador', 'Otro',
                name='tipo_empleado_enum'),
        nullable=False
    )
    estado = db.Column(
        db.Enum('Activo', 'Inactivo', name='estado_enum'),
        nullable=False,
        default='Activo'
    )
    fecha_contratacion = db.Column(db.Date, nullable=False)

    usuario = db.relationship('Usuario', back_populates='empleado', uselist=False)
    medico = db.relationship('Medico', back_populates='empleado', uselist=False)

    def to_dict(self):
        return {
            'id_empleado': self.id_empleado,
            'nombre_completo': self.nombre_completo,
            'apellidos': self.apellidos,
            'telefono': self.telefono,
            'email': self.email,
            'tipo_empleado': self.tipo_empleado,
            'estado': self.estado,
            'fecha_contratacion': self.fecha_contratacion.isoformat()
            if self.fecha_contratacion else None,
        }


# ─────────────────────────────────────────────
# USUARIOS
# ─────────────────────────────────────────────
class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id_usuario = db.Column(db.Integer, primary_key=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey('empleados.id_empleado',
                                                      onupdate='CASCADE', ondelete='RESTRICT'),
                            nullable=True, unique=True)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id_paciente',
                                                      onupdate='CASCADE', ondelete='RESTRICT'),
                            nullable=True, unique=True)
    nombre_usuario = db.Column(db.String(60), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(
        db.Enum('Admin', 'Recepcionista', 'Paciente', name='rol_enum'),
        nullable=False
    )
    estado = db.Column(
        db.Enum('Activo', 'Inactivo', name='estado_enum'),
        nullable=False,
        default='Activo'
    )

    empleado = db.relationship('Empleado', back_populates='usuario')
    paciente = db.relationship('Paciente', backref='credenciales_usuario')
    def to_dict(self):
        return {
            'id_usuario': self.id_usuario,
            'id_empleado': self.id_empleado,
            'id_paciente': self.id_paciente,
            'nombre_usuario': self.nombre_usuario,
            'rol': self.rol,
            'estado': self.estado,
            'empleado': self.empleado.to_dict() if self.empleado else None,
            'paciente_vinculado': f"{self.paciente.nombre} {self.paciente.apellidos}" if hasattr(self,
                                                                                                 'paciente') and self.paciente else None
        }


# ─────────────────────────────────────────────
# ESPECIALIDADES
# ─────────────────────────────────────────────
class Especialidad(db.Model):
    __tablename__ = 'especialidades'

    id_especialidad = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.Text)

    medicos = db.relationship('Medico', back_populates='especialidad')

    def to_dict(self):
        return {
            'id_especialidad': self.id_especialidad,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
        }


# ─────────────────────────────────────────────
# MEDICOS
# ─────────────────────────────────────────────
class Medico(db.Model):
    __tablename__ = 'medicos'

    id_medico = db.Column(db.Integer, primary_key=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey('empleados.id_empleado',
                                                      onupdate='CASCADE', ondelete='RESTRICT'),
                            nullable=False, unique=True)
    id_especialidad = db.Column(db.Integer, db.ForeignKey('especialidades.id_especialidad',
                                                          onupdate='CASCADE', ondelete='RESTRICT'),
                                nullable=False)
    cedula_profesional = db.Column(db.String(20), nullable=False, unique=True)

    empleado = db.relationship('Empleado', back_populates='medico')
    especialidad = db.relationship('Especialidad', back_populates='medicos')
    citas = db.relationship('Cita', back_populates='medico')

    def to_dict(self):
        emp = self.empleado
        return {
            'id_medico': self.id_medico,
            'id_empleado': self.id_empleado,
            'cedula_profesional': self.cedula_profesional,
            'nombre_completo': emp.nombre_completo if emp else None,
            'apellidos': emp.apellidos if emp else None,
            'telefono': emp.telefono if emp else None,
            'estado': emp.estado if emp else None,
            'id_especialidad': self.id_especialidad,
            'especialidad': self.especialidad.nombre if self.especialidad else None,
        }


# ─────────────────────────────────────────────
# PACIENTES
# ─────────────────────────────────────────────
class Paciente(db.Model):
    __tablename__ = 'pacientes'

    id_paciente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    telefono = db.Column(db.String(15))
    email = db.Column(db.String(100))
    curp = db.Column(db.String(18), unique=True)
    rfc = db.Column(db.String(13), unique=True)
    fecha_registro = db.Column(db.DateTime, nullable=False,
                               default=datetime.utcnow)

    citas = db.relationship('Cita', back_populates='paciente')

    def to_dict(self):
        return {
            'id_paciente': self.id_paciente,
            'nombre': self.nombre,
            'apellidos': self.apellidos,
            'fecha_nacimiento': self.fecha_nacimiento.isoformat()
            if self.fecha_nacimiento else None,
            'telefono': self.telefono,
            'email': self.email,
            'curp': self.curp,
            'rfc': self.rfc,
            'fecha_registro': self.fecha_registro.isoformat()
            if self.fecha_registro else None,
        }


# ─────────────────────────────────────────────
# SERVICIOS
# ─────────────────────────────────────────────
class Servicio(db.Model):
    __tablename__ = 'servicios'

    id_servicio = db.Column(db.Integer, primary_key=True)
    nombre_servicio = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    costo = db.Column(db.Numeric(10, 2), nullable=False)
    duracion_estimada = db.Column(db.Integer, nullable=False)

    citas = db.relationship('Cita', back_populates='servicio')

    def to_dict(self):
        return {
            'id_servicio': self.id_servicio,
            'nombre_servicio': self.nombre_servicio,
            'descripcion': self.descripcion,
            'costo': float(self.costo),
            'duracion_estimada': self.duracion_estimada,
        }


# ─────────────────────────────────────────────
# CITAS
# ─────────────────────────────────────────────
class Cita(db.Model):
    __tablename__ = 'citas'

    id_cita = db.Column(db.Integer, primary_key=True)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id_paciente',
                                                      onupdate='CASCADE', ondelete='RESTRICT'),
                            nullable=False)
    id_medico = db.Column(db.Integer, db.ForeignKey('medicos.id_medico',
                                                    onupdate='CASCADE', ondelete='RESTRICT'),
                          nullable=False)
    id_servicio = db.Column(db.Integer, db.ForeignKey('servicios.id_servicio',
                                                      onupdate='CASCADE', ondelete='RESTRICT'),
                            nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    estado = db.Column(
        db.Enum('Agendada', 'En Progreso', 'Completada', 'Cancelada',
                name='estado_cita_enum'),
        nullable=False,
        default='Agendada'
    )
    motivo_visita = db.Column(db.String(255))

    paciente = db.relationship('Paciente', back_populates='citas')
    medico = db.relationship('Medico', back_populates='citas')
    servicio = db.relationship('Servicio', back_populates='citas')
    consulta = db.relationship('Consulta', back_populates='cita', uselist=False)
    pago = db.relationship('Pago', back_populates='cita', uselist=False)

    def to_dict(self):
        return {
            'id_cita': self.id_cita,
            'id_paciente': self.id_paciente,
            'id_medico': self.id_medico,
            'id_servicio': self.id_servicio,
            'fecha_hora': self.fecha_hora.isoformat() if self.fecha_hora else None,
            'estado': self.estado,
            'motivo_visita': self.motivo_visita,
            'paciente': f"{self.paciente.nombre} {self.paciente.apellidos}"
            if self.paciente else None,
            'medico': f"{self.medico.empleado.nombre_completo}"
            if self.medico and self.medico.empleado else None,
            'servicio': self.servicio.nombre_servicio if self.servicio else None,
        }


# ─────────────────────────────────────────────
# CONSULTAS
# ─────────────────────────────────────────────
class Consulta(db.Model):
    __tablename__ = 'consultas'

    id_consulta = db.Column(db.Integer, primary_key=True)
    id_cita = db.Column(db.Integer, db.ForeignKey('citas.id_cita',
                                                  onupdate='CASCADE', ondelete='RESTRICT'),
                        nullable=False, unique=True)
    sintomas = db.Column(db.Text)
    diagnostico = db.Column(db.Text)
    tratamiento = db.Column(db.Text)
    receta_medica = db.Column(db.Text)

    cita = db.relationship('Cita', back_populates='consulta')

    def to_dict(self):
        cita = self.cita
        return {
            'id_consulta': self.id_consulta,
            'id_cita': self.id_cita,
            'sintomas': self.sintomas,
            'diagnostico': self.diagnostico,
            'tratamiento': self.tratamiento,
            'receta_medica': self.receta_medica,
            'fecha': cita.fecha_hora.date().isoformat()
            if cita and cita.fecha_hora else None,
            'paciente': f"{cita.paciente.nombre} {cita.paciente.apellidos}"
            if cita and cita.paciente else None,
            'medico': cita.medico.empleado.nombre_completo
            if cita and cita.medico and cita.medico.empleado else None,
        }


# ─────────────────────────────────────────────
# PAGOS
# ─────────────────────────────────────────────
class Pago(db.Model):
    __tablename__ = 'pagos'

    id_pago = db.Column(db.Integer, primary_key=True)
    id_cita = db.Column(db.Integer, db.ForeignKey('citas.id_cita',
                                                  onupdate='CASCADE', ondelete='RESTRICT'),
                        nullable=False, unique=True)
    monto_total = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pago = db.Column(
        db.Enum('Efectivo', 'Tarjeta', 'Transferencia', name='metodo_pago_enum'),
        nullable=False
    )
    fecha_pago = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    cita = db.relationship('Cita', back_populates='pago')

    def to_dict(self):
        cita = self.cita
        return {
            'id_pago': self.id_pago,
            'id_cita': self.id_cita,
            'monto_total': float(self.monto_total),
            'metodo_pago': self.metodo_pago,
            'fecha_pago': self.fecha_pago.isoformat() if self.fecha_pago else None,
            'paciente': f"{cita.paciente.nombre} {cita.paciente.apellidos}"
            if cita and cita.paciente else None,
        }