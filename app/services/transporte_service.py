from datetime import datetime, time
from decimal import Decimal
from sqlalchemy import or_
from app import db
from app.models.transporte import Transporte

def parse_time_str(time_val):
    """Convierte cadena de texto (HH:MM o HH:MM:SS) a objeto time de Python."""
    if not time_val:
        return None
    if isinstance(time_val, time):
        return time_val
    time_str = str(time_val).strip()
    if not time_str:
        return None
    for fmt in ('%H:%M:%S', '%H:%M'):
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue
    return None

def listar_transportes(
    search_query: str = '',
    tipo_filtro: str = '',
    estado: str = 'activos',
    sort_by: str = 'nombre_asc',
    page: int = 1,
    per_page: int = 12
):
    """
    Lista transportes paginados con filtros de búsqueda, tipo y estado (soft delete).
    """
    query = Transporte.query

    if estado == 'activos':
        query = query.filter(Transporte.deleted_at.is_(None))
    elif estado == 'eliminados':
        query = query.filter(Transporte.deleted_at.isnot(None))

    if tipo_filtro and tipo_filtro in ['Privado', 'Público', 'Publico']:
        tipo_normalizado = 'Público' if tipo_filtro in ['Público', 'Publico'] else 'Privado'
        query = query.filter(Transporte.tipo == tipo_normalizado)

    if search_query:
        term = f"%{search_query.strip()}%"
        query = query.filter(
            or_(
                Transporte.nombre.ilike(term),
                Transporte.tipo.ilike(term),
                Transporte.tipo_costo.ilike(term)
            )
        )

    if sort_by == 'id_asc':
        query = query.order_by(Transporte.id_transporte.asc())
    elif sort_by == 'id_desc':
        query = query.order_by(Transporte.id_transporte.desc())
    elif sort_by == 'nombre_desc':
        query = query.order_by(Transporte.nombre.desc())
    elif sort_by == 'costo_asc':
        query = query.order_by(Transporte.costo.asc())
    elif sort_by == 'costo_desc':
        query = query.order_by(Transporte.costo.desc())
    elif sort_by == 'capacidad_asc':
        query = query.order_by(Transporte.capacidad.asc())
    elif sort_by == 'capacidad_desc':
        query = query.order_by(Transporte.capacidad.desc())
    elif sort_by in ['velocidad_asc', 'tiempo_asc']:
        query = query.order_by(Transporte.velocidad_promedio_kmh.asc())
    elif sort_by in ['velocidad_desc', 'tiempo_desc']:
        query = query.order_by(Transporte.velocidad_promedio_kmh.desc())
    else:  # nombre_asc
        query = query.order_by(Transporte.nombre.asc())

    return query.paginate(page=page, per_page=per_page, error_out=False)

def obtener_transporte(id_transporte: int, include_deleted: bool = False) -> Transporte | None:
    """Obtiene un medio de transporte por su ID."""
    t = db.session.get(Transporte, id_transporte)
    if not t:
        return None
    if not include_deleted and t.is_deleted:
        return None
    return t

def crear_transporte(data: dict) -> tuple[bool, str, Transporte | None]:
    """
    Crea un nuevo medio de transporte (Acceso exclusivo Administrador).
    """
    nombre = (data.get('nombre') or '').strip()
    tipo = (data.get('tipo') or '').strip()
    capacidad_raw = data.get('capacidad')
    horario_inicio_raw = data.get('horario_inicio')
    horario_fin_raw = data.get('horario_fin')
    costo_por_tramo_raw = data.get('costo_por_tramo')
    tipo_costo = (data.get('tipo_costo') or '').strip()
    velocidad_promedio_kmh_raw = data.get('velocidad_promedio_kmh')

    if not nombre or len(nombre) < 3:
        return False, "El nombre del transporte es obligatorio y debe tener al menos 3 caracteres.", None

    if len(nombre) > 100:
        return False, "El nombre no puede exceder los 100 caracteres.", None

    # Normalizar tipo
    if tipo in ['Publico', 'Público']:
        tipo = 'Público'
    elif tipo == 'Privado':
        tipo = 'Privado'
    else:
        return False, "El tipo de transporte debe ser 'Privado' o 'Público'.", None

    if tipo_costo not in ['por_persona', 'por_vehiculo']:
        return False, "El tipo de costo debe ser 'por_persona' o 'por_vehiculo'.", None

    # Capacidad
    try:
        capacidad = int(capacidad_raw)
        if capacidad <= 0:
            return False, "La capacidad debe ser un número entero mayor a 0.", None
    except (TypeError, ValueError):
        return False, "La capacidad es obligatoria y debe ser un número entero mayor a 0.", None

    # Tiempos y horarios
    h_inicio = parse_time_str(horario_inicio_raw)
    h_fin = parse_time_str(horario_fin_raw)

    if not h_inicio:
        return False, "El horario de inicio es obligatorio y debe tener formato válido (HH:MM).", None
    if not h_fin:
        return False, "El horario de fin es obligatorio y debe tener formato válido (HH:MM).", None

    if h_fin <= h_inicio:
        return False, "El horario de finalización debe ser posterior al horario de inicio.", None

    # Costo
    costo_raw = data.get('costo') if 'costo' in data else data.get('costo_por_tramo')
    try:
        costo = Decimal(str(costo_raw))
        if costo < 0:
            return False, "El costo debe ser mayor o igual a 0.", None
    except Exception:
        return False, "El costo debe ser un valor decimal válido.", None

    # Velocidad promedio (km/h)
    try:
        velocidad_promedio_kmh = Decimal(str(velocidad_promedio_kmh_raw))
        if velocidad_promedio_kmh <= Decimal('0.0') or velocidad_promedio_kmh > Decimal('120.0'):
            return False, "La velocidad promedio debe ser mayor a 0 km/h y menor o igual a 120 km/h.", None
    except Exception:
        return False, "La velocidad promedio debe ser un número decimal válido (ej. 30.0).", None

    try:
        nuevo_transporte = Transporte(
            nombre=nombre,
            tipo=tipo,
            capacidad=capacidad,
            horario_inicio=h_inicio,
            horario_fin=h_fin,
            costo=costo,
            tipo_costo=tipo_costo,
            velocidad_promedio_kmh=velocidad_promedio_kmh
        )
        db.session.add(nuevo_transporte)
        db.session.commit()
        return True, f"Transporte '{nombre}' registrado exitosamente.", nuevo_transporte
    except Exception as e:
        db.session.rollback()
        return False, f"Error al registrar transporte: {str(e)}", None

def actualizar_transporte(id_transporte: int, data: dict, rol: str = 'admin') -> tuple[bool, str, Transporte | None]:
    """
    Actualiza un transporte existente con control de permisos según rol:
    - Admin: Puede modificar todos los campos.
    - Agente: Solo puede modificar campos operativos (capacidad, horarios, velocidad promedio).
    """
    t = db.session.get(Transporte, id_transporte)
    if not t:
        return False, "Transporte no encontrado.", None

    # Validar campos operativos (comunes para Admin y Agente)
    capacidad_raw = data.get('capacidad')
    horario_inicio_raw = data.get('horario_inicio')
    horario_fin_raw = data.get('horario_fin')
    velocidad_promedio_kmh_raw = data.get('velocidad_promedio_kmh')

    try:
        capacidad = int(capacidad_raw)
        if capacidad <= 0:
            return False, "La capacidad debe ser un número entero mayor a 0.", None
    except (TypeError, ValueError):
        return False, "La capacidad debe ser un número entero mayor a 0.", None

    h_inicio = parse_time_str(horario_inicio_raw)
    h_fin = parse_time_str(horario_fin_raw)

    if not h_inicio:
        return False, "El horario de inicio es obligatorio y debe tener formato válido (HH:MM).", None
    if not h_fin:
        return False, "El horario de fin es obligatorio y debe tener formato válido (HH:MM).", None

    if h_fin <= h_inicio:
        return False, "El horario de finalización debe ser posterior al horario de inicio.", None

    try:
        velocidad_promedio_kmh = Decimal(str(velocidad_promedio_kmh_raw))
        if velocidad_promedio_kmh <= Decimal('0.0') or velocidad_promedio_kmh > Decimal('120.0'):
            return False, "La velocidad promedio debe ser mayor a 0 km/h y menor o igual a 120 km/h.", None
    except Exception:
        return False, "La velocidad promedio debe ser un número decimal válido (ej. 30.0).", None

    # Actualizar campos operativos
    t.capacidad = capacidad
    t.horario_inicio = h_inicio
    t.horario_fin = h_fin
    t.velocidad_promedio_kmh = velocidad_promedio_kmh

    # Si es Administrador, validar y actualizar también campos comerciales y estructurales
    if rol == 'admin':
        nombre = (data.get('nombre') or '').strip()
        tipo = (data.get('tipo') or '').strip()
        costo_raw = data.get('costo') if 'costo' in data else data.get('costo_por_tramo')
        tipo_costo = (data.get('tipo_costo') or '').strip()

        if not nombre or len(nombre) < 3:
            return False, "El nombre del transporte es obligatorio y debe tener al menos 3 caracteres.", None
        if len(nombre) > 100:
            return False, "El nombre no puede exceder los 100 caracteres.", None

        if tipo in ['Publico', 'Público']:
            tipo = 'Público'
        elif tipo == 'Privado':
            tipo = 'Privado'
        else:
            return False, "El tipo de transporte debe ser 'Privado' o 'Público'.", None

        if tipo_costo not in ['por_persona', 'por_vehiculo']:
            return False, "El tipo de costo debe ser 'por_persona' o 'por_vehiculo'.", None

        try:
            costo = Decimal(str(costo_raw))
            if costo < 0:
                return False, "El costo debe ser mayor o igual a 0.", None
        except Exception:
            return False, "El costo debe ser un valor decimal válido.", None

        t.nombre = nombre
        t.tipo = tipo
        t.costo = costo
        t.tipo_costo = tipo_costo

    try:
        db.session.commit()
        mensaje = "Transporte actualizado exitosamente." if rol == 'admin' else "Campos operativos del transporte actualizados exitosamente."
        return True, mensaje, t
    except Exception as e:
        db.session.rollback()
        return False, f"Error al actualizar transporte: {str(e)}", None

def eliminar_transporte(id_transporte: int) -> tuple[bool, str]:
    """
    Aplica soft delete al transporte (Solo Admin).
    """
    t = db.session.get(Transporte, id_transporte)
    if not t:
        return False, "Transporte no encontrado."

    try:
        t.deleted_at = datetime.utcnow()
        db.session.commit()
        return True, f"Transporte '{t.nombre}' desactivado exitosamente (eliminación lógica)."
    except Exception as e:
        db.session.rollback()
        return False, f"Error al eliminar transporte: {str(e)}"

def restaurar_transporte(id_transporte: int) -> tuple[bool, str]:
    """
    Restaura un transporte eliminado lógicamente (Solo Admin).
    """
    t = db.session.get(Transporte, id_transporte)
    if not t:
        return False, "Transporte no encontrado."

    try:
        t.deleted_at = None
        db.session.commit()
        return True, f"Transporte '{t.nombre}' restaurado exitosamente."
    except Exception as e:
        db.session.rollback()
        return False, f"Error al restaurar transporte: {str(e)}"

def get_estadisticas_transportes() -> dict:
    """Métricas de transportes para paneles de control."""
    total = Transporte.query.count()
    activos = Transporte.query.filter(Transporte.deleted_at.is_(None)).count()
    eliminados = Transporte.query.filter(Transporte.deleted_at.isnot(None)).count()
    publicos = Transporte.query.filter(Transporte.tipo == 'Público', Transporte.deleted_at.is_(None)).count()
    privados = Transporte.query.filter(Transporte.tipo == 'Privado', Transporte.deleted_at.is_(None)).count()

    return {
        'total': total,
        'activos': activos,
        'eliminados': eliminados,
        'publicos': publicos,
        'privados': privados
    }
