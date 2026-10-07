import os
import uuid
from datetime import datetime, time
from decimal import Decimal
from PIL import Image
from sqlalchemy import or_
from app import db
from app.models.atractivo import Atractivo
from app.models.categoria import Categoria
from app.models.subcategoria import Subcategoria
from app.models.proveedor import Proveedor

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

def get_upload_dir():
    """Retorna la ruta absoluta del directorio de subida de imágenes de atractivos."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads', 'atractivos'))
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

def guardar_imagen_atractivo(archivo) -> tuple[bool, str, str | None]:
    """
    Valida, redimensiona con Pillow (ancho máx 1200px) y guarda físicamente la imagen de un atractivo.
    Retorna (éxito, mensaje, ruta_relativa).
    """
    if not archivo or not hasattr(archivo, 'filename') or not archivo.filename:
        return True, "No se proporcionó archivo de imagen.", None

    filename = archivo.filename.strip()
    if not filename:
        return True, "Nombre de archivo vacío.", None

    if '.' not in filename:
        return False, "El archivo debe tener una extensión válida (png, jpg, jpeg, webp).", None

    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Formato no permitido (.{ext}). Formatos aceptados: png, jpg, jpeg, webp.", None

    # Validar tamaño del archivo
    archivo.seek(0, os.SEEK_END)
    file_length = archivo.tell()
    archivo.seek(0)
    if file_length > MAX_IMAGE_SIZE:
        return False, "La imagen excede el tamaño máximo permitido de 5 MB.", None

    try:
        img = Image.open(archivo)
        
        # Redimensionar si el ancho supera los 1200px manteniendo la proporción
        max_width = 1200
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(float(img.height) * float(ratio))
            resample_filter = getattr(Image, 'Resampling', Image).LANCZOS
            img = img.resize((max_width, new_height), resample_filter)

        # Generar nombre único con UUID
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        upload_dir = get_upload_dir()
        dest_path = os.path.join(upload_dir, unique_name)

        # Normalizar modo de color para JPEG
        if ext in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')
        
        img.save(dest_path, optimize=True, quality=85)
        
        relative_path = f"uploads/atractivos/{unique_name}"
        return True, "Imagen guardada exitosamente.", relative_path
    except Exception as e:
        return False, f"Error al procesar la imagen: {str(e)}", None

def eliminar_archivo_imagen(ruta_relativa: str | None):
    """Elimina físicamente del disco el archivo de imagen anterior de un atractivo."""
    if not ruta_relativa:
        return
    try:
        clean_rel = ruta_relativa.replace('\\', '/').lstrip('/')
        if clean_rel.startswith('uploads/atractivos/'):
            filename = os.path.basename(clean_rel)
            file_path = os.path.join(get_upload_dir(), filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except Exception as e:
        print(f"Advertencia: no se pudo eliminar archivo físico {ruta_relativa}: {e}")

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

    # Filtro por categoría o subcategoría
    if categoria_id and str(categoria_id).isdigit() and int(categoria_id) > 0:
        query = query.join(Atractivo.subcategoria).filter(Subcategoria.id_categoria == int(categoria_id))

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

def crear_atractivo(data: dict, imagen_file=None) -> tuple[bool, str, Atractivo | None]:
    """
    Crea un nuevo atractivo turístico validando reglas comerciales, geográficas y de horario.
    Soporta subida física de imagen con Pillow (Solo Administrador).
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

    # 3. Subcategoría y Proveedor
    id_subcategoria_raw = data.get('id_subcategoria') or data.get('id_categoria')
    subcat = None
    if id_subcategoria_raw and str(id_subcategoria_raw).isdigit():
        subcat = db.session.get(Subcategoria, int(id_subcategoria_raw))
        if not subcat:
            # Fallback si se pasó un id_categoria
            subcat = Subcategoria.query.filter_by(id_categoria=int(id_subcategoria_raw)).first()

    if not subcat:
        return False, "Debes seleccionar una subcategoría válida.", None
    id_subcategoria = subcat.id_subcategoria

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

    # 8. Procesamiento de Imagen (archivo físico o ruta)
    imagen_url = None
    if imagen_file and hasattr(imagen_file, 'filename') and imagen_file.filename:
        ok_img, msg_img, ruta_img = guardar_imagen_atractivo(imagen_file)
        if not ok_img:
            return False, msg_img, None
        imagen_url = ruta_img
    elif data.get('imagen_url'):
        imagen_url = str(data.get('imagen_url')).strip() or None

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
            id_subcategoria=id_subcategoria,
            id_proveedor=id_proveedor,
            imagen_url=imagen_url,
            fecha_inicio=data.get('fecha_inicio'),
            fecha_fin=data.get('fecha_fin'),
            afecta_rutas=bool(data.get('afecta_rutas', False)),
            sensible_al_clima=bool(data.get('sensible_al_clima', False)),
            tipo_clima_ideal=data.get('tipo_clima_ideal')
        )
        db.session.add(nuevo_atractivo)
        db.session.commit()
        return True, f"Atractivo turístico '{nombre}' creado exitosamente.", nuevo_atractivo
    except Exception as e:
        db.session.rollback()
        # Si falló la BD y se había guardado un archivo, limpiarlo
        if imagen_url and imagen_url.startswith('uploads/atractivos/'):
            eliminar_archivo_imagen(imagen_url)
        return False, f"Error al registrar atractivo: {str(e)}", None

def actualizar_atractivo(id_atractivo: int, data: dict, rol: str = 'admin', imagen_file=None) -> tuple[bool, str, Atractivo | None]:
    """
    Actualiza un atractivo turístico diferenciando permisos:
    - Admin: Puede modificar la totalidad de los datos (comerciales, estructurales, operativos e imagen).
    - Agente: Solo puede modificar campos operativos (descripción, dirección, coordenadas, horarios, días cerrado, tiempo estimado). NO puede modificar imagen.
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

    # 2. Si el rol es Administrador, validar y actualizar campos comerciales, estructurales e imagen
    archivo_anterior_a_eliminar = None
    if rol == 'admin':
        nombre = (data.get('nombre') or '').strip()
        costo_entrada_raw = data.get('costo_entrada')
        id_categoria_raw = data.get('id_categoria')
        id_proveedor_raw = data.get('id_proveedor')

        if not nombre or len(nombre) < 3:
            return False, "El nombre del atractivo es obligatorio y debe tener al menos 3 caracteres.", None
        if len(nombre) > 100:
            return False, "El nombre no puede exceder los 100 caracteres.", None

        otro = Atractivo.query.filter(Atractivo.nombre.ilike(nombre), Atractivo.id_atractivo != id_atractivo).first()
        if otro:
            return False, f"Ya existe otro atractivo turístico con el nombre '{nombre}'.", None

        id_subcategoria_raw = data.get('id_subcategoria') or data.get('id_categoria')
        subcat = None
        if id_subcategoria_raw and str(id_subcategoria_raw).isdigit():
            subcat = db.session.get(Subcategoria, int(id_subcategoria_raw))
            if not subcat:
                subcat = Subcategoria.query.filter_by(id_categoria=int(id_subcategoria_raw)).first()

        if not subcat:
            return False, "Debes seleccionar una subcategoría válida.", None

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

        # Manejo de imagen
        if imagen_file and hasattr(imagen_file, 'filename') and imagen_file.filename:
            ok_img, msg_img, ruta_img = guardar_imagen_atractivo(imagen_file)
            if not ok_img:
                return False, msg_img, None
            archivo_anterior_a_eliminar = atractivo.imagen_url
            atractivo.imagen_url = ruta_img
        elif data.get('eliminar_imagen') in ['1', 'true', 'True', True]:
            archivo_anterior_a_eliminar = atractivo.imagen_url
            atractivo.imagen_url = None
        elif 'imagen_url' in data and data.get('imagen_url') != atractivo.imagen_url:
            nueva_ruta = (data.get('imagen_url') or '').strip() or None
            atractivo.imagen_url = nueva_ruta

        atractivo.nombre = nombre
        atractivo.costo_entrada = costo_entrada
        atractivo.id_subcategoria = subcat.id_subcategoria
        atractivo.id_proveedor = id_proveedor

    try:
        db.session.commit()
        if archivo_anterior_a_eliminar and archivo_anterior_a_eliminar != atractivo.imagen_url:
            eliminar_archivo_imagen(archivo_anterior_a_eliminar)
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
