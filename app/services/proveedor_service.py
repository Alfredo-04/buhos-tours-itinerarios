from datetime import datetime
import re
from decimal import Decimal
from sqlalchemy import or_
from app import db
from app.models.proveedor import Proveedor
from app.models.atractivo import Atractivo

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

def listar_proveedores(
    search_query: str = '',
    estado: str = 'activos',
    sort_by: str = 'razon_social_asc',
    page: int = 1,
    per_page: int = 10
):
    """
    Lista proveedores paginados con filtros de búsqueda y estado (soft delete).
    """
    query = Proveedor.query

    if estado == 'activos':
        query = query.filter(Proveedor.deleted_at.is_(None))
    elif estado == 'eliminados':
        query = query.filter(Proveedor.deleted_at.isnot(None))

    if search_query:
        term = f"%{search_query.strip()}%"
        query = query.filter(
            or_(
                Proveedor.razon_social.ilike(term),
                Proveedor.tipo.ilike(term),
                Proveedor.contacto_nombre.ilike(term),
                Proveedor.contacto_email.ilike(term)
            )
        )

    if sort_by == 'id_asc':
        query = query.order_by(Proveedor.id_proveedor.asc())
    elif sort_by == 'id_desc':
        query = query.order_by(Proveedor.id_proveedor.desc())
    elif sort_by == 'razon_social_desc':
        query = query.order_by(Proveedor.razon_social.desc())
    else:  # razon_social_asc
        query = query.order_by(Proveedor.razon_social.asc())

    return query.paginate(page=page, per_page=per_page, error_out=False)

def obtener_todos_activos() -> list[Proveedor]:
    """Retorna todos los proveedores activos para selectores en formularios."""
    return Proveedor.query.filter(Proveedor.deleted_at.is_(None)).order_by(Proveedor.razon_social.asc()).all()

def obtener_proveedor(id_proveedor: int) -> Proveedor | None:
    """Obtiene un proveedor por su ID."""
    return db.session.get(Proveedor, id_proveedor)

def crear_proveedor(data: dict) -> tuple[bool, str, Proveedor | None]:
    """
    Crea un nuevo proveedor con validación de datos.
    """
    razon_social = (data.get('razon_social') or '').strip()
    tipo = (data.get('tipo') or '').strip()
    contacto_nombre = (data.get('contacto_nombre') or '').strip()
    contacto_telefono = (data.get('contacto_telefono') or '').strip()
    contacto_email = (data.get('contacto_email') or '').strip()
    tarifa_especial_raw = data.get('tarifa_especial')
    observaciones = (data.get('observaciones') or '').strip()

    if not razon_social or len(razon_social) < 3:
        return False, "La razón social es obligatoria y debe tener al menos 3 caracteres.", None

    if len(razon_social) > 100:
        return False, "La razón social no puede exceder los 100 caracteres.", None

    if contacto_email and not re.match(EMAIL_REGEX, contacto_email):
        return False, "El correo de contacto tiene un formato inválido.", None

    tarifa_especial = None
    if tarifa_especial_raw is not None and str(tarifa_especial_raw).strip() != '':
        try:
            tarifa_especial = Decimal(str(tarifa_especial_raw))
            if tarifa_especial < 0:
                return False, "La tarifa especial debe ser un monto mayor o igual a 0.", None
        except Exception:
            return False, "La tarifa especial debe ser un valor numérico válido.", None

    try:
        nuevo_prov = Proveedor(
            razon_social=razon_social,
            tipo=tipo if tipo else None,
            contacto_nombre=contacto_nombre if contacto_nombre else None,
            contacto_telefono=contacto_telefono if contacto_telefono else None,
            contacto_email=contacto_email if contacto_email else None,
            tarifa_especial=tarifa_especial,
            observaciones=observaciones if observaciones else None
        )
        db.session.add(nuevo_prov)
        db.session.commit()
        return True, f"Proveedor '{razon_social}' creado exitosamente.", nuevo_prov
    except Exception as e:
        db.session.rollback()
        return False, f"Error al crear proveedor: {str(e)}", None

def actualizar_proveedor(id_proveedor: int, data: dict) -> tuple[bool, str, Proveedor | None]:
    """
    Actualiza un proveedor existente.
    """
    prov = obtener_proveedor(id_proveedor)
    if not prov:
        return False, "Proveedor no encontrado.", None

    razon_social = (data.get('razon_social') or '').strip()
    tipo = (data.get('tipo') or '').strip()
    contacto_nombre = (data.get('contacto_nombre') or '').strip()
    contacto_telefono = (data.get('contacto_telefono') or '').strip()
    contacto_email = (data.get('contacto_email') or '').strip()
    tarifa_especial_raw = data.get('tarifa_especial')
    observaciones = (data.get('observaciones') or '').strip()

    if not razon_social or len(razon_social) < 3:
        return False, "La razón social es obligatoria y debe tener al menos 3 caracteres.", None

    if len(razon_social) > 100:
        return False, "La razón social no puede exceder los 100 caracteres.", None

    if contacto_email and not re.match(EMAIL_REGEX, contacto_email):
        return False, "El correo de contacto tiene un formato inválido.", None

    tarifa_especial = None
    if tarifa_especial_raw is not None and str(tarifa_especial_raw).strip() != '':
        try:
            tarifa_especial = Decimal(str(tarifa_especial_raw))
            if tarifa_especial < 0:
                return False, "La tarifa especial debe ser un monto mayor o igual a 0.", None
        except Exception:
            return False, "La tarifa especial debe ser un valor numérico válido.", None

    try:
        prov.razon_social = razon_social
        prov.tipo = tipo if tipo else None
        prov.contacto_nombre = contacto_nombre if contacto_nombre else None
        prov.contacto_telefono = contacto_telefono if contacto_telefono else None
        prov.contacto_email = contacto_email if contacto_email else None
        prov.tarifa_especial = tarifa_especial
        prov.observaciones = observaciones if observaciones else None

        db.session.commit()
        return True, "Proveedor actualizado exitosamente.", prov
    except Exception as e:
        db.session.rollback()
        return False, f"Error al actualizar proveedor: {str(e)}", None

def eliminar_proveedor(id_proveedor: int) -> tuple[bool, str]:
    """
    Aplica soft delete al proveedor verificando integridad referencial con Atractivo.
    """
    prov = obtener_proveedor(id_proveedor)
    if not prov:
        return False, "Proveedor no encontrado."

    # Verificar si tiene atractivos activos asociados
    atractivos_asociados = Atractivo.query.filter_by(id_proveedor=id_proveedor, deleted_at=None).count()
    if atractivos_asociados > 0:
        return False, f"No se puede eliminar el proveedor '{prov.razon_social}' porque tiene {atractivos_asociados} atractivo(s) activo(s) asociado(s). Reasigna o desactiva esos atractivos primero."

    try:
        prov.deleted_at = datetime.utcnow()
        db.session.commit()
        return True, f"Proveedor '{prov.razon_social}' desactivado exitosamente (eliminación lógica)."
    except Exception as e:
        db.session.rollback()
        return False, f"Error al eliminar proveedor: {str(e)}"

def restaurar_proveedor(id_proveedor: int) -> tuple[bool, str]:
    """
    Restaura un proveedor eliminado lógicamente.
    """
    prov = obtener_proveedor(id_proveedor)
    if not prov:
        return False, "Proveedor no encontrado."

    try:
        prov.deleted_at = None
        db.session.commit()
        return True, f"Proveedor '{prov.razon_social}' restaurado exitosamente."
    except Exception as e:
        db.session.rollback()
        return False, f"Error al restaurar proveedor: {str(e)}"

def get_estadisticas_proveedores() -> dict:
    """Métricas de proveedores para el panel admin."""
    total = Proveedor.query.count()
    activos = Proveedor.query.filter(Proveedor.deleted_at.is_(None)).count()
    eliminados = Proveedor.query.filter(Proveedor.deleted_at.isnot(None)).count()
    return {
        'total': total,
        'activos': activos,
        'eliminados': eliminados
    }
