from datetime import datetime
from sqlalchemy import or_
from app import db
from app.models.categoria import Categoria
from app.models.atractivo import Atractivo

def listar_categorias(
    search_query: str = '',
    estado: str = 'activos',
    sort_by: str = 'nombre_asc',
    page: int = 1,
    per_page: int = 10
):
    """
    Lista categorías paginadas con filtros de búsqueda y estado (soft delete).
    """
    query = Categoria.query

    if estado == 'activos':
        query = query.filter(Categoria.deleted_at.is_(None))
    elif estado == 'eliminados':
        query = query.filter(Categoria.deleted_at.isnot(None))
    # 'todos' no filtra por deleted_at

    if search_query:
        term = f"%{search_query.strip()}%"
        query = query.filter(
            or_(
                Categoria.nombre.ilike(term),
                Categoria.descripcion.ilike(term)
            )
        )

    if sort_by == 'id_asc':
        query = query.order_by(Categoria.id_categoria.asc())
    elif sort_by == 'id_desc':
        query = query.order_by(Categoria.id_categoria.desc())
    elif sort_by == 'nombre_desc':
        query = query.order_by(Categoria.nombre.desc())
    else:  # nombre_asc
        query = query.order_by(Categoria.nombre.asc())

    return query.paginate(page=page, per_page=per_page, error_out=False)

def obtener_todas_activas() -> list[Categoria]:
    """Retorna todas las categorías activas para selectores en formularios."""
    return Categoria.query.filter(Categoria.deleted_at.is_(None)).order_by(Categoria.nombre.asc()).all()

def obtener_categoria(id_categoria: int) -> Categoria | None:
    """Obtiene una categoría por su ID."""
    return db.session.get(Categoria, id_categoria)

def crear_categoria(data: dict) -> tuple[bool, str, Categoria | None]:
    """
    Crea una nueva categoría validando reglas de negocio.
    """
    nombre = (data.get('nombre') or '').strip()
    descripcion = (data.get('descripcion') or '').strip()

    if not nombre or len(nombre) < 3:
        return False, "El nombre de la categoría es obligatorio y debe tener al menos 3 caracteres.", None

    if len(nombre) > 50:
        return False, "El nombre no puede exceder los 50 caracteres.", None

    if descripcion and len(descripcion) > 200:
        return False, "La descripción no puede exceder los 200 caracteres.", None

    # Validar nombre único
    existente = Categoria.query.filter(Categoria.nombre.ilike(nombre)).first()
    if existente:
        if existente.is_deleted:
            return False, f"Existe una categoría inactiva con el nombre '{nombre}'. Puedes restaurarla desde la papelera.", None
        return False, f"Ya existe una categoría registrada con el nombre '{nombre}'.", None

    try:
        nueva_cat = Categoria(
            nombre=nombre,
            descripcion=descripcion if descripcion else None
        )
        db.session.add(nueva_cat)
        db.session.commit()
        return True, f"Categoría '{nombre}' creada exitosamente.", nueva_cat
    except Exception as e:
        db.session.rollback()
        return False, f"Error al crear categoría: {str(e)}", None

def actualizar_categoria(id_categoria: int, data: dict) -> tuple[bool, str, Categoria | None]:
    """
    Actualiza una categoría existente.
    """
    cat = obtener_categoria(id_categoria)
    if not cat:
        return False, "Categoría no encontrada.", None

    nombre = (data.get('nombre') or '').strip()
    descripcion = (data.get('descripcion') or '').strip()

    if not nombre or len(nombre) < 3:
        return False, "El nombre de la categoría es obligatorio y debe tener al menos 3 caracteres.", None

    if len(nombre) > 50:
        return False, "El nombre no puede exceder los 50 caracteres.", None

    if descripcion and len(descripcion) > 200:
        return False, "La descripción no puede exceder los 200 caracteres.", None

    # Validar que no se duplique con otra categoría
    otro = Categoria.query.filter(Categoria.nombre.ilike(nombre), Categoria.id_categoria != id_categoria).first()
    if otro:
        return False, f"Ya existe otra categoría registrada con el nombre '{nombre}'.", None

    try:
        cat.nombre = nombre
        cat.descripcion = descripcion if descripcion else None
        db.session.commit()
        return True, "Categoría actualizada exitosamente.", cat
    except Exception as e:
        db.session.rollback()
        return False, f"Error al actualizar categoría: {str(e)}", None

def eliminar_categoria(id_categoria: int) -> tuple[bool, str]:
    """
    Aplica soft delete a la categoría verificando integridad referencial con Atractivo.
    """
    cat = obtener_categoria(id_categoria)
    if not cat:
        return False, "Categoría no encontrada."

    # Verificar si tiene atractivos activos asociados
    atractivos_asociados = Atractivo.query.filter_by(id_categoria=id_categoria, deleted_at=None).count()
    if atractivos_asociados > 0:
        return False, f"No se puede eliminar la categoría '{cat.nombre}' porque tiene {atractivos_asociados} atractivo(s) activo(s) asociado(s). Reasigna o desactiva esos atractivos primero."

    try:
        cat.deleted_at = datetime.utcnow()
        db.session.commit()
        return True, f"Categoría '{cat.nombre}' desactivada exitosamente (eliminación lógica)."
    except Exception as e:
        db.session.rollback()
        return False, f"Error al eliminar categoría: {str(e)}"

def restaurar_categoria(id_categoria: int) -> tuple[bool, str]:
    """
    Restaura una categoría eliminada lógicamente.
    """
    cat = obtener_categoria(id_categoria)
    if not cat:
        return False, "Categoría no encontrada."

    try:
        cat.deleted_at = None
        db.session.commit()
        return True, f"Categoría '{cat.nombre}' restaurada exitosamente."
    except Exception as e:
        db.session.rollback()
        return False, f"Error al restaurar categoría: {str(e)}"

def get_estadisticas_categorias() -> dict:
    """Métricas de categorías para el panel admin."""
    total = Categoria.query.count()
    activos = Categoria.query.filter(Categoria.deleted_at.is_(None)).count()
    eliminados = Categoria.query.filter(Categoria.deleted_at.isnot(None)).count()
    return {
        'total': total,
        'activos': activos,
        'eliminados': eliminados
    }
