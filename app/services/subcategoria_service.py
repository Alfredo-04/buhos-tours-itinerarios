from datetime import datetime
from sqlalchemy import or_
from app import db
from app.models.subcategoria import Subcategoria
from app.models.categoria import Categoria
from app.models.atractivo import Atractivo

def listar_subcategorias(
    categoria_id: int | None = None,
    search_query: str = '',
    estado: str = 'activos',
    sort_by: str = 'nombre_asc',
    page: int = 1,
    per_page: int = 10
):
    """
    Lista subcategorías paginadas con filtros por categoría padre, búsqueda y estado (soft delete).
    """
    query = Subcategoria.query

    if estado == 'activos':
        query = query.filter(Subcategoria.deleted_at.is_(None))
    elif estado == 'eliminados':
        query = query.filter(Subcategoria.deleted_at.isnot(None))

    if categoria_id and str(categoria_id).isdigit() and int(categoria_id) > 0:
        query = query.filter(Subcategoria.id_categoria == int(categoria_id))

    if search_query:
        term = f"%{search_query.strip()}%"
        query = query.filter(
            or_(
                Subcategoria.nombre.ilike(term),
                Subcategoria.descripcion.ilike(term)
            )
        )

    if sort_by == 'id_asc':
        query = query.order_by(Subcategoria.id_subcategoria.asc())
    elif sort_by == 'id_desc':
        query = query.order_by(Subcategoria.id_subcategoria.desc())
    elif sort_by == 'nombre_desc':
        query = query.order_by(Subcategoria.nombre.desc())
    elif sort_by == 'categoria_asc':
        query = query.join(Subcategoria.categoria).order_by(Categoria.nombre.asc(), Subcategoria.nombre.asc())
    elif sort_by == 'categoria_desc':
        query = query.join(Subcategoria.categoria).order_by(Categoria.nombre.desc(), Subcategoria.nombre.asc())
    else:  # nombre_asc
        query = query.order_by(Subcategoria.nombre.asc())

    return query.paginate(page=page, per_page=per_page, error_out=False)

def obtener_todas_activas() -> list[Subcategoria]:
    """Retorna todas las subcategorías activas para selectores en formularios."""
    return Subcategoria.query.filter(Subcategoria.deleted_at.is_(None)).order_by(Subcategoria.nombre.asc()).all()

def obtener_subcategoria(id_subcategoria: int) -> Subcategoria | None:
    """Obtiene una subcategoría por su ID."""
    return db.session.get(Subcategoria, id_subcategoria)

def crear_subcategoria(data: dict) -> tuple[bool, str, Subcategoria | None]:
    """
    Crea una nueva subcategoría validando unicidad y existencia de la categoría padre.
    """
    nombre = (data.get('nombre') or '').strip()
    descripcion = (data.get('descripcion') or '').strip()
    id_categoria_raw = data.get('id_categoria')

    if not nombre or len(nombre) < 3:
        return False, "El nombre de la subcategoría es obligatorio y debe tener al menos 3 caracteres.", None

    if len(nombre) > 50:
        return False, "El nombre no puede exceder los 50 caracteres.", None

    if descripcion and len(descripcion) > 200:
        return False, "La descripción no puede exceder los 200 caracteres.", None

    try:
        id_categoria = int(id_categoria_raw)
        cat = db.session.get(Categoria, id_categoria)
        if not cat:
            return False, "La categoría seleccionada no existe.", None
    except (TypeError, ValueError):
        return False, "Debes seleccionar una categoría padre válida.", None

    # Validar nombre único
    existente = Subcategoria.query.filter(Subcategoria.nombre.ilike(nombre)).first()
    if existente:
        if existente.is_deleted:
            return False, f"Existe una subcategoría inactiva con el nombre '{nombre}'. Puedes restaurarla desde la papelera.", None
        return False, f"Ya existe una subcategoría registrada con el nombre '{nombre}'.", None

    try:
        nueva_subcat = Subcategoria(
            nombre=nombre,
            descripcion=descripcion if descripcion else None,
            id_categoria=id_categoria
        )
        db.session.add(nueva_subcat)
        db.session.commit()
        return True, f"Subcategoría '{nombre}' creada exitosamente.", nueva_subcat
    except Exception as e:
        db.session.rollback()
        return False, f"Error al crear subcategoría: {str(e)}", None

def actualizar_subcategoria(id_subcategoria: int, data: dict) -> tuple[bool, str, Subcategoria | None]:
    """
    Actualiza una subcategoría existente.
    """
    subcat = obtener_subcategoria(id_subcategoria)
    if not subcat:
        return False, "Subcategoría no encontrada.", None

    nombre = (data.get('nombre') or '').strip()
    descripcion = (data.get('descripcion') or '').strip()
    id_categoria_raw = data.get('id_categoria')

    if not nombre or len(nombre) < 3:
        return False, "El nombre de la subcategoría es obligatorio y debe tener al menos 3 caracteres.", None

    if len(nombre) > 50:
        return False, "El nombre no puede exceder los 50 caracteres.", None

    if descripcion and len(descripcion) > 200:
        return False, "La descripción no puede exceder los 200 caracteres.", None

    try:
        id_categoria = int(id_categoria_raw)
        cat = db.session.get(Categoria, id_categoria)
        if not cat:
            return False, "La categoría seleccionada no existe.", None
    except (TypeError, ValueError):
        return False, "Debes seleccionar una categoría padre válida.", None

    otro = Subcategoria.query.filter(Subcategoria.nombre.ilike(nombre), Subcategoria.id_subcategoria != id_subcategoria).first()
    if otro:
        return False, f"Ya existe otra subcategoría registrada con el nombre '{nombre}'.", None

    try:
        subcat.nombre = nombre
        subcat.descripcion = descripcion if descripcion else None
        subcat.id_categoria = id_categoria
        db.session.commit()
        return True, "Subcategoría actualizada exitosamente.", subcat
    except Exception as e:
        db.session.rollback()
        return False, f"Error al actualizar subcategoría: {str(e)}", None

def eliminar_subcategoria(id_subcategoria: int) -> tuple[bool, str]:
    """
    Aplica soft delete a la subcategoría verificando integridad referencial con Atractivo.
    """
    subcat = obtener_subcategoria(id_subcategoria)
    if not subcat:
        return False, "Subcategoría no encontrada."

    # Verificar atractivos activos asociados
    atractivos_asociados = Atractivo.query.filter_by(id_subcategoria=id_subcategoria, deleted_at=None).count()
    if atractivos_asociados > 0:
        return False, f"No se puede desactivar la subcategoría '{subcat.nombre}' porque tiene {atractivos_asociados} atractivo(s) activo(s) asociado(s). Reasigna o desactiva esos atractivos primero."

    try:
        subcat.deleted_at = datetime.utcnow()
        db.session.commit()
        return True, f"Subcategoría '{subcat.nombre}' desactivada exitosamente (eliminación lógica)."
    except Exception as e:
        db.session.rollback()
        return False, f"Error al eliminar subcategoría: {str(e)}"

def restaurar_subcategoria(id_subcategoria: int) -> tuple[bool, str]:
    """
    Restaura una subcategoría eliminada lógicamente.
    """
    subcat = obtener_subcategoria(id_subcategoria)
    if not subcat:
        return False, "Subcategoría no encontrada."

    try:
        subcat.deleted_at = None
        db.session.commit()
        return True, f"Subcategoría '{subcat.nombre}' restaurada exitosamente."
    except Exception as e:
        db.session.rollback()
        return False, f"Error al restaurar subcategoría: {str(e)}"

def get_estadisticas_subcategorias() -> dict:
    """Métricas de subcategorías para el panel admin."""
    total = Subcategoria.query.count()
    activos = Subcategoria.query.filter(Subcategoria.deleted_at.is_(None)).count()
    eliminados = Subcategoria.query.filter(Subcategoria.deleted_at.isnot(None)).count()
    return {
        'total': total,
        'activos': activos,
        'eliminados': eliminados
    }
