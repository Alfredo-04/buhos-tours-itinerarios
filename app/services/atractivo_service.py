from datetime import datetime, time
from decimal import Decimal
from sqlalchemy import or_
from app import db
from app.models.atractivo import Atractivo
from app.models.categoria import Categoria
from app.models.proveedor import Proveedor

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

def listar_atractivos(
    search_query: str = '',
    categoria_id: int | None = None,
    estado: str = 'activos',
    sort_by: str = 'nombre_asc',
    page: int = 1,
    per_page: int = 12
):
    """
    Lista atractivos paginados con filtros de búsqueda, categoría, estado (soft delete) y ordenamiento.
    """
    query = Atractivo.query

    # Filtro de soft delete
    if estado == 'activos':
        query = query.filter(Atractivo.deleted_at.is_(None))
    elif estado == 'eliminados':
        query = query.filter(Atractivo.deleted_at.isnot(None))

    # Filtro por categoría
    if categoria_id and str(categoria_id).isdigit() and int(categoria_id) > 0:
        query = query.filter(Atractivo.id_categoria == int(categoria_id))

    # Búsqueda por texto (nombre, descripción, dirección)
    if search_query:
        term = f"%{search_query.strip()}%"
        query = query.filter(
            or_(
                Atractivo.nombre.ilike(term),
                Atractivo.descripcion.ilike(term),
                Atractivo.direccion.ilike(term)
            )
        )

    # Ordenamiento
    if sort_by == 'id_asc':
        query = query.order_by(Atractivo.id_atractivo.asc())
    elif sort_by == 'id_desc':
        query = query.order_by(Atractivo.id_atractivo.desc())
    elif sort_by == 'nombre_desc':
        query = query.order_by(Atractivo.nombre.desc())
    elif sort_by == 'costo_asc':
        query = query.order_by(Atractivo.costo_entrada.asc(), Atractivo.nombre.asc())
    elif sort_by == 'costo_desc':
        query = query.order_by(Atractivo.costo_entrada.desc(), Atractivo.nombre.asc())
    elif sort_by == 'tiempo_asc':
        query = query.order_by(Atractivo.tiempo_visita_estimado.asc(), Atractivo.nombre.asc())
    elif sort_by == 'tiempo_desc':
        query = query.order_by(Atractivo.tiempo_visita_estimado.desc(), Atractivo.nombre.asc())
    else:  # nombre_asc por defecto
        query = query.order_by(Atractivo.nombre.asc())

    return query.paginate(page=page, per_page=per_page, error_out=False)

def obtener_atractivo(id_atractivo: int, include_deleted: bool = False) -> Atractivo | None:
    """Obtiene un atractivo por su ID."""
    atractivo = db.session.get(Atractivo, id_atractivo)
    if not atractivo:
        return None
    if not include_deleted and atractivo.is_deleted:
        return None
    return atractivo

def crear_atractivo(data: dict) -> tuple[bool, str, Atractivo | None]:
    """
    Crea un nuevo atractivo turístico validando reglas comerciales, geográficas y de horario.
    (Solo Administrador).
    """
    nombre = (data.get('nombre') or '').strip()
    descripcion = (data.get('descripcion') or '').strip()
    direccion = (data.get('direccion') or '').strip()
    latitud_raw = data.get('latitud')
    longitud_raw = data.get('longitud')
    horario_apertura_raw = data.get('horario_apertura')
    horario_cierre_raw = data.get('horario_cierre')
    costo_entrada_raw = data.get('costo_entrada')
    tiempo_visita_estimado_raw = data.get('tiempo_visita_estimado')
    dias_cerrado = (data.get('dias_cerrado') or '').strip()
    id_categoria_raw = data.get('id_categoria')
    id_proveedor_raw = data.get('id_proveedor')
    imagen_url = (data.get('imagen_url') or '').strip()

    # 1. Nombre
    if not nombre or len(nombre) < 3:
        return False, "El nombre del atractivo es obligatorio y debe tener al menos 3 caracteres.", None
    if len(nombre) > 100:
        return False, "El nombre no puede exceder los 100 caracteres.", None

    existente = Atractivo.query.filter(Atractivo.nombre.ilike(nombre)).first()
    if existente:
        if existente.is_deleted:
            return False, f"Existe un atractivo inactivo con el nombre '{nombre}'. Puedes restaurarlo desde la papelera.", None
        return False, f"Ya existe un atractivo registrado con el nombre '{nombre}'.", None

    # 2. Descripción y Dirección
    if descripcion and len(descripcion) > 500:
        return False, "La descripción no puede exceder los 500 caracteres.", None
    if direccion and len(direccion) > 200:
        return False, "La dirección no puede exceder los 200 caracteres.", None

    # 3. Categoría y Proveedor
    try:
        id_categoria = int(id_categoria_raw)
        cat = db.session.get(Categoria, id_categoria)
        if not cat:
            return False, "La categoría seleccionada no existe.", None
    except (TypeError, ValueError):
        return False, "Debes seleccionar una categoría válida.", None

    try:
        id_proveedor = int(id_proveedor_raw)
        prov = db.session.get(Proveedor, id_proveedor)
        if not prov:
            return False, "El proveedor seleccionado no existe.", None
    except (TypeError, ValueError):
        return False, "Debes seleccionar un proveedor válido.", None

    # 4. Coordenadas (Rango Bolivia: Latitud -22 a -9, Longitud -69 a -57)
    latitud = None
    if latitud_raw is not None and str(latitud_raw).strip() != '':
        try:
            latitud = Decimal(str(latitud_raw))
            if latitud < Decimal('-23.0') or latitud > Decimal('-9.0'):
                return False, "La latitud debe estar dentro del rango geográfico válido de Bolivia (entre -22.0 y -9.0).", None
        except Exception:
            return False, "La latitud debe ser un valor numérico decimal válido.", None

    longitud = None
    if longitud_raw is not None and str(longitud_raw).strip() != '':
        try:
            longitud = Decimal(str(longitud_raw))
            if longitud < Decimal('-70.0') or longitud > Decimal('-57.0'):
                return False, "La longitud debe estar dentro del rango geográfico válido de Bolivia (entre -69.0 y -57.0).", None
        except Exception:
            return False, "La longitud debe ser un valor numérico decimal válido.", None

    # 5. Horarios
    h_apertura = parse_time_str(horario_apertura_raw)
    h_cierre = parse_time_str(horario_cierre_raw)

    if (horario_apertura_raw and not h_apertura) or (horario_cierre_raw and not h_cierre):
        return False, "Los horarios deben tener un formato válido (HH:MM).", None

    if h_apertura and h_cierre and h_cierre <= h_apertura:
        return False, "El horario de cierre debe ser posterior al horario de apertura.", None

    # 6. Costo entrada
    costo_entrada = Decimal('0.00')
    if costo_entrada_raw is not None and str(costo_entrada_raw).strip() != '':
        try:
            costo_entrada = Decimal(str(costo_entrada_raw))
            if costo_entrada < 0:
                return False, "El costo de entrada debe ser un monto mayor o igual a 0.", None
        except Exception:
            return False, "El costo de entrada debe ser un valor decimal válido.", None

    # 7. Tiempo estimado de visita (minutos)
    tiempo_visita_estimado = None
    if tiempo_visita_estimado_raw is not None and str(tiempo_visita_estimado_raw).strip() != '':
        try:
            tiempo_visita_estimado = int(tiempo_visita_estimado_raw)
            if tiempo_visita_estimado <= 0:
                return False, "El tiempo de visita estimado debe ser un número entero mayor a 0 minutos.", None
        except (TypeError, ValueError):
            return False, "El tiempo de visita estimado debe ser un número entero válido.", None

    # 8. Imagen URL
    if imagen_url and len(imagen_url) > 255:
        return False, "La URL de imagen no puede exceder los 255 caracteres.", None

    try:
        nuevo_atractivo = Atractivo(
            nombre=nombre,
            descripcion=descripcion if descripcion else None,
            direccion=direccion if direccion else None,
            latitud=latitud,
            longitud=longitud,
            horario_apertura=h_apertura,
            horario_cierre=h_cierre,
            costo_entrada=costo_entrada,
            tiempo_visita_estimado=tiempo_visita_estimado,
            dias_cerrado=dias_cerrado if dias_cerrado else None,
            id_categoria=id_categoria,
            id_proveedor=id_proveedor,
            imagen_url=imagen_url if imagen_url else None
        )
        db.session.add(nuevo_atractivo)
        db.session.commit()
        return True, f"Atractivo turístico '{nombre}' creado exitosamente.", nuevo_atractivo
    except Exception as e:
        db.session.rollback()
        return False, f"Error al registrar atractivo: {str(e)}", None

def actualizar_atractivo(id_atractivo: int, data: dict, rol: str = 'admin') -> tuple[bool, str, Atractivo | None]:
    """
    Actualiza un atractivo turístico diferenciando permisos:
    - Admin: Puede modificar la totalidad de los datos (comerciales, estructurales y operativos).
    - Agente: Solo puede modificar campos operativos (descripción, dirección, coordenadas, horarios, días cerrado, tiempo estimado).
    """
    atractivo = db.session.get(Atractivo, id_atractivo)
    if not atractivo:
        return False, "Atractivo turístico no encontrado.", None

    # 1. Campos operativos (comunes para Admin y Agente)
    descripcion = (data.get('descripcion') or '').strip()
    direccion = (data.get('direccion') or '').strip()
    latitud_raw = data.get('latitud')
    longitud_raw = data.get('longitud')
    horario_apertura_raw = data.get('horario_apertura')
    horario_cierre_raw = data.get('horario_cierre')
    dias_cerrado = (data.get('dias_cerrado') or '').strip()
    tiempo_visita_estimado_raw = data.get('tiempo_visita_estimado')

    if descripcion and len(descripcion) > 500:
        return False, "La descripción no puede exceder los 500 caracteres.", None
    if direccion and len(direccion) > 200:
        return False, "La dirección no puede exceder los 200 caracteres.", None

    # Coordenadas
    latitud = None
    if latitud_raw is not None and str(latitud_raw).strip() != '':
        try:
            latitud = Decimal(str(latitud_raw))
            if latitud < Decimal('-23.0') or latitud > Decimal('-9.0'):
                return False, "La latitud debe estar dentro del rango de Bolivia (-22.0 a -9.0).", None
        except Exception:
            return False, "La latitud debe ser un valor decimal válido.", None

    longitud = None
    if longitud_raw is not None and str(longitud_raw).strip() != '':
        try:
            longitud = Decimal(str(longitud_raw))
            if longitud < Decimal('-70.0') or longitud > Decimal('-57.0'):
                return False, "La longitud debe estar dentro del rango de Bolivia (-69.0 a -57.0).", None
        except Exception:
            return False, "La longitud debe ser un valor decimal válido.", None

    # Horarios
    h_apertura = parse_time_str(horario_apertura_raw)
    h_cierre = parse_time_str(horario_cierre_raw)

    if (horario_apertura_raw and not h_apertura) or (horario_cierre_raw and not h_cierre):
        return False, "Los horarios deben tener un formato válido (HH:MM).", None

    if h_apertura and h_cierre and h_cierre <= h_apertura:
        return False, "El horario de cierre debe ser posterior al horario de apertura.", None

    # Tiempo de visita
    tiempo_visita_estimado = None
    if tiempo_visita_estimado_raw is not None and str(tiempo_visita_estimado_raw).strip() != '':
        try:
            tiempo_visita_estimado = int(tiempo_visita_estimado_raw)
            if tiempo_visita_estimado <= 0:
                return False, "El tiempo de visita estimado debe ser mayor a 0 minutos.", None
        except (TypeError, ValueError):
            return False, "El tiempo de visita estimado debe ser un número entero válido.", None

    # Asignar campos operativos
    atractivo.descripcion = descripcion if descripcion else None
    atractivo.direccion = direccion if direccion else None
    atractivo.latitud = latitud
    atractivo.longitud = longitud
    atractivo.horario_apertura = h_apertura
    atractivo.horario_cierre = h_cierre
    atractivo.dias_cerrado = dias_cerrado if dias_cerrado else None
    atractivo.tiempo_visita_estimado = tiempo_visita_estimado

    # 2. Si el rol es Administrador, validar y actualizar campos comerciales y estructurales
    if rol == 'admin':
        nombre = (data.get('nombre') or '').strip()
        costo_entrada_raw = data.get('costo_entrada')
        id_categoria_raw = data.get('id_categoria')
        id_proveedor_raw = data.get('id_proveedor')
        imagen_url = (data.get('imagen_url') or '').strip()

        if not nombre or len(nombre) < 3:
            return False, "El nombre del atractivo es obligatorio y debe tener al menos 3 caracteres.", None
        if len(nombre) > 100:
            return False, "El nombre no puede exceder los 100 caracteres.", None

        otro = Atractivo.query.filter(Atractivo.nombre.ilike(nombre), Atractivo.id_atractivo != id_atractivo).first()
        if otro:
            return False, f"Ya existe otro atractivo turístico con el nombre '{nombre}'.", None

        try:
            id_categoria = int(id_categoria_raw)
            cat = db.session.get(Categoria, id_categoria)
            if not cat:
                return False, "La categoría seleccionada no existe.", None
        except (TypeError, ValueError):
            return False, "Debes seleccionar una categoría válida.", None

        try:
            id_proveedor = int(id_proveedor_raw)
            prov = db.session.get(Proveedor, id_proveedor)
            if not prov:
                return False, "El proveedor seleccionado no existe.", None
        except (TypeError, ValueError):
            return False, "Debes seleccionar un proveedor válido.", None

        costo_entrada = Decimal('0.00')
        if costo_entrada_raw is not None and str(costo_entrada_raw).strip() != '':
            try:
                costo_entrada = Decimal(str(costo_entrada_raw))
                if costo_entrada < 0:
                    return False, "El costo de entrada debe ser mayor o igual a 0.", None
            except Exception:
                return False, "El costo de entrada debe ser un número decimal válido.", None

        if imagen_url and len(imagen_url) > 255:
            return False, "La URL de imagen no puede exceder los 255 caracteres.", None

        atractivo.nombre = nombre
        atractivo.costo_entrada = costo_entrada
        atractivo.id_categoria = id_categoria
        atractivo.id_proveedor = id_proveedor
        atractivo.imagen_url = imagen_url if imagen_url else None

    try:
        db.session.commit()
        mensaje = "Atractivo turístico actualizado exitosamente." if rol == 'admin' else "Campos operativos del atractivo actualizados exitosamente."
        return True, mensaje, atractivo
    except Exception as e:
        db.session.rollback()
        return False, f"Error al actualizar atractivo: {str(e)}", None

def eliminar_atractivo(id_atractivo: int) -> tuple[bool, str]:
    """
    Aplica soft delete al atractivo turístico (Solo Admin).
    """
    atractivo = db.session.get(Atractivo, id_atractivo)
    if not atractivo:
        return False, "Atractivo turístico no encontrado."

    try:
        atractivo.deleted_at = datetime.utcnow()
        db.session.commit()
        return True, f"Atractivo turístico '{atractivo.nombre}' desactivado exitosamente (eliminación lógica)."
    except Exception as e:
        db.session.rollback()
        return False, f"Error al eliminar atractivo: {str(e)}"

def restaurar_atractivo(id_atractivo: int) -> tuple[bool, str]:
    """
    Restaura un atractivo turístico eliminado lógicamente (Solo Admin).
    """
    atractivo = db.session.get(Atractivo, id_atractivo)
    if not atractivo:
        return False, "Atractivo turístico no encontrado."

    try:
        atractivo.deleted_at = None
        db.session.commit()
        return True, f"Atractivo turístico '{atractivo.nombre}' restaurado exitosamente."
    except Exception as e:
        db.session.rollback()
        return False, f"Error al restaurar atractivo: {str(e)}"

def get_estadisticas_atractivos() -> dict:
    """Métricas de atractivos para paneles de control."""
    total = Atractivo.query.count()
    activos = Atractivo.query.filter(Atractivo.deleted_at.is_(None)).count()
    eliminados = Atractivo.query.filter(Atractivo.deleted_at.isnot(None)).count()
    categorias_activas = Categoria.query.filter(Categoria.deleted_at.is_(None)).count()
    proveedores_activos = Proveedor.query.filter(Proveedor.deleted_at.is_(None)).count()

    return {
        'total': total,
        'activos': activos,
        'eliminados': eliminados,
        'categorias_activas': categorias_activas,
        'proveedores_activos': proveedores_activos
    }
