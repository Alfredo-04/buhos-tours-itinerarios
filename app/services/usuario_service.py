from sqlalchemy import or_
from app.models.usuario import Usuario

def get_usuarios_filtrados(search_query: str = '', rol_filtro: str = '', sort_by: str = 'id_asc') -> list[Usuario]:
    """
    Obtiene la lista de usuarios aplicando búsqueda por texto, filtro de rol y ordenamiento.
    """
    query = Usuario.query

    # Búsqueda por texto (nombres, apellidos, email)
    if search_query:
        term = f"%{search_query.strip()}%"
        query = query.filter(
            or_(
                Usuario.nombres.ilike(term),
                Usuario.apellidos.ilike(term),
                Usuario.email.ilike(term)
            )
        )

    # Filtro por rol
    if rol_filtro and rol_filtro in ['admin', 'agente']:
        query = query.filter(Usuario.rol == rol_filtro)

    # Ordenamiento
    if sort_by == 'id_desc':
        query = query.order_by(Usuario.id_usuario.desc())
    elif sort_by == 'nombre_asc':
        query = query.order_by(Usuario.nombres.asc(), Usuario.apellidos.asc())
    elif sort_by == 'fecha_desc':
        query = query.order_by(Usuario.fecha_registro.desc(), Usuario.id_usuario.desc())
    elif sort_by == 'fecha_asc':
        query = query.order_by(Usuario.fecha_registro.asc(), Usuario.id_usuario.asc())
    else:  # id_asc por defecto
        query = query.order_by(Usuario.id_usuario.asc())

    return query.all()

def get_total_estadisticas() -> dict:
    """
    Retorna métricas de usuarios para las tarjetas de resumen del listado.
    """
    total = Usuario.query.count()
    admins = Usuario.query.filter_by(rol='admin').count()
    agentes = Usuario.query.filter_by(rol='agente').count()
    return {
        'total': total,
        'admins': admins,
        'agentes': agentes
    }
