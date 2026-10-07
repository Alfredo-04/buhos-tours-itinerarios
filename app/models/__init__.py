# Models package
from .rol import Rol
from .usuario import Usuario
from .turista import Turista
from .categoria import Categoria
from .subcategoria import Subcategoria
from .proveedor import Proveedor
from .transporte import Transporte
from .atractivo import Atractivo
from .zona_trafico import ZonaTrafico
from .patron_trafico import PatronTrafico
from .generacion import Generacion
from .itinerario import Itinerario
from .itinerario_detalle import ItinerarioDetalle
from .viaje_turista import ViajeTurista
from .itinerario_detalle_trafico import ItinerarioDetalleTrafico
from .tipo_cambio import TipoCambio
from .consulta_nsga2 import ConsultaNSGA2

__all__ = [
    'Rol',
    'Usuario',
    'Turista',
    'Categoria',
    'Subcategoria',
    'Proveedor',
    'Transporte',
    'Atractivo',
    'ZonaTrafico',
    'PatronTrafico',
    'Generacion',
    'Itinerario',
    'ItinerarioDetalle',
    'ViajeTurista',
    'ItinerarioDetalleTrafico',
    'TipoCambio',
    'ConsultaNSGA2',
]