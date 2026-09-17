from decimal import Decimal
from datetime import time
from app import db
from app.models.categoria import Categoria
from app.models.proveedor import Proveedor
from app.models.transporte import Transporte
from app.models.atractivo import Atractivo

def seed_catalogo():
    """
    Puebla la base de datos con categorías, proveedores, transportes y atractivos iniciales de Bolivia.
    """
    print("Iniciando seeder de catálogo...")

    # 1. Categorías
    categorias_data = [
        {"nombre": "Arqueológico y Cultural", "descripcion": "Sitios históricos, complejos arqueológicos, ruinas y templos precolombinos."},
        {"nombre": "Naturaleza y Paisajes", "descripcion": "Salinas, lagunas de altura, parques nacionales, miradores y maravillas naturales."},
        {"nombre": "Aventura y Ecoturismo", "descripcion": "Rutas de senderismo, ciclismo, deportes de montaña y reservas biológicas."},
        {"nombre": "Urbano e Histórico", "descripcion": "Centros coloniales, plazas mayores, museos de arte y arquitectura urbana."},
        {"nombre": "Gastronomía y Tradición", "descripcion": "Mercados tradicionales, ferias gastronómicas y experiencias culturales autóctonas."}
    ]

    categoria_map = {}
    for c_data in categorias_data:
        cat = Categoria.query.filter_by(nombre=c_data["nombre"]).first()
        if not cat:
            cat = Categoria(nombre=c_data["nombre"], descripcion=c_data["descripcion"])
            db.session.add(cat)
            db.session.flush()
        categoria_map[c_data["nombre"]] = cat

    # 2. Proveedores
    proveedores_data = [
        {
            "razon_social": "Operadora de Turismo Andina Bolivia S.R.L.",
            "tipo": "Agencia Receptiva y Excursiones",
            "contacto_nombre": "Carlos Mendoza",
            "contacto_telefono": "+591 2 2445566",
            "contacto_email": "reservas@andinabolivia.bo",
            "tarifa_especial": Decimal("10.00"),
            "observaciones": "Convenio de tarifa corporativa para paquetes de altura."
        },
        {
            "razon_social": "Transportes Turísticos del Altiplano",
            "tipo": "Transporte Terrestre Especializado",
            "contacto_nombre": "Patricia Quispe",
            "contacto_telefono": "+591 71512345",
            "contacto_email": "contacto@transaltiplano.bo",
            "tarifa_especial": Decimal("15.00"),
            "observaciones": "Flota 4x4 con choferes certificados en primeros auxilios."
        },
        {
            "razon_social": "Asociación de Guías Oficiales de Tiwanaku",
            "tipo": "Servicios de Guiaje Local",
            "contacto_nombre": "Jaime Mamani",
            "contacto_telefono": "+591 72098765",
            "contacto_email": "guias@tiwanaku-turismo.bo",
            "tarifa_especial": Decimal("5.00"),
            "observaciones": "Guías acreditados bilingües (Español, Inglés, Francés, Aymara)."
        },
        {
            "razon_social": "Red Ecoturística Comunitaria del Titicaca",
            "tipo": "Comunidad Náutica y Hospedaje",
            "contacto_nombre": "Lucía Flores",
            "contacto_telefono": "+591 73245678",
            "contacto_email": "titicaca.eco@comunidades.bo",
            "tarifa_especial": Decimal("8.00"),
            "observaciones": "Embarcaciones a motor registradas y con chalecos salvavidas."
        }
    ]

    proveedor_map = {}
    for p_data in proveedores_data:
        prov = Proveedor.query.filter_by(razon_social=p_data["razon_social"]).first()
        if not prov:
            prov = Proveedor(
                razon_social=p_data["razon_social"],
                tipo=p_data["tipo"],
                contacto_nombre=p_data["contacto_nombre"],
                contacto_telefono=p_data["contacto_telefono"],
                contacto_email=p_data["contacto_email"],
                tarifa_especial=p_data["tarifa_especial"],
                observaciones=p_data["observaciones"]
            )
            db.session.add(prov)
            db.session.flush()
        proveedor_map[p_data["razon_social"]] = prov

    # 3. Transportes
    transportes_data = [
        {
            "nombre": "Minibús Ejecutivo Turístico",
            "tipo": "Privado",
            "capacidad": 15,
            "horario_inicio": time(6, 0),
            "horario_fin": time(22, 0),
            "costo_por_tramo": Decimal("120.00"),
            "tipo_costo": "por_vehiculo",
            "tiempo_recorrido_base": 45
        },
        {
            "nombre": "Bus Panorámico Interurbano",
            "tipo": "Público",
            "capacidad": 45,
            "horario_inicio": time(7, 0),
            "horario_fin": time(20, 0),
            "costo_por_tramo": Decimal("15.00"),
            "tipo_costo": "por_persona",
            "tiempo_recorrido_base": 60
        },
        {
            "nombre": "Vagoneta 4x4 Todo Terreno",
            "tipo": "Privado",
            "capacidad": 6,
            "horario_inicio": time(5, 30),
            "horario_fin": time(23, 0),
            "costo_por_tramo": Decimal("180.00"),
            "tipo_costo": "por_vehiculo",
            "tiempo_recorrido_base": 35
        },
        {
            "nombre": "Lancha a Motor Lago Titicaca",
            "tipo": "Privado",
            "capacidad": 20,
            "horario_inicio": time(7, 30),
            "horario_fin": time(17, 30),
            "costo_por_tramo": Decimal("35.00"),
            "tipo_costo": "por_persona",
            "tiempo_recorrido_base": 50
        },
        {
            "nombre": "Red de Teleférico Metropolitano",
            "tipo": "Público",
            "capacidad": 10,
            "horario_inicio": time(6, 0),
            "horario_fin": time(23, 0),
            "costo_por_tramo": Decimal("3.00"),
            "tipo_costo": "por_persona",
            "tiempo_recorrido_base": 15
        }
    ]

    for t_data in transportes_data:
        t = Transporte.query.filter_by(nombre=t_data["nombre"]).first()
        if not t:
            t = Transporte(
                nombre=t_data["nombre"],
                tipo=t_data["tipo"],
                capacidad=t_data["capacidad"],
                horario_inicio=t_data["horario_inicio"],
                horario_fin=t_data["horario_fin"],
                costo_por_tramo=t_data["costo_por_tramo"],
                tipo_costo=t_data["tipo_costo"],
                tiempo_recorrido_base=t_data["tiempo_recorrido_base"]
            )
            db.session.add(t)

    # 4. Atractivos
    atractivos_data = [
        {
            "nombre": "Salar de Uyuni",
            "descripcion": "El mayor desierto de sal continuo y alto del mundo, famoso por su superficie reflectante tipo espejo durante el periodo de lluvias e islas de cactus gigantes.",
            "direccion": "Provincia Daniel Campos, Departamento de Potosí",
            "latitud": Decimal("-20.1337772"),
            "longitud": Decimal("-67.4891345"),
            "horario_apertura": time(6, 0),
            "horario_cierre": time(19, 0),
            "costo_entrada": Decimal("30.00"),
            "tiempo_visita_estimado": 240,
            "dias_cerrado": None,
            "categoria": "Naturaleza y Paisajes",
            "proveedor": "Operadora de Turismo Andina Bolivia S.R.L."
        },
        {
            "nombre": "Complejo Arqueológico de Tiwanaku",
            "descripcion": "Centro espiritual y político de la cultura Tiwanacota, declarado Patrimonio de la Humanidad por la UNESCO. Destacan la Puerta del Sol y el Templo de Kalasasaya.",
            "direccion": "Municipio de Tiwanaku, Provincia Ingavi, La Paz",
            "latitud": Decimal("-16.5552390"),
            "longitud": Decimal("-68.6738910"),
            "horario_apertura": time(8, 30),
            "horario_cierre": time(17, 0),
            "costo_entrada": Decimal("100.00"),
            "tiempo_visita_estimado": 180,
            "dias_cerrado": None,
            "categoria": "Arqueológico y Cultural",
            "proveedor": "Asociación de Guías Oficiales de Tiwanaku"
        },
        {
            "nombre": "Isla del Sol - Lago Titicaca",
            "descripcion": "Mítica isla cuna de la civilización Inca en el lago navegable más alto del mundo, con terrazas agrícolas preincaicas y senderos panorámicos.",
            "direccion": "Copacabana, Lago Titicaca, La Paz",
            "latitud": Decimal("-15.9986111"),
            "longitud": Decimal("-69.1763889"),
            "horario_apertura": time(7, 0),
            "horario_cierre": time(17, 30),
            "costo_entrada": Decimal("25.00"),
            "tiempo_visita_estimado": 210,
            "dias_cerrado": None,
            "categoria": "Naturaleza y Paisajes",
            "proveedor": "Red Ecoturística Comunitaria del Titicaca"
        },
        {
            "nombre": "Valle de la Luna La Paz",
            "descripcion": "Curiosa formación geológica esculpida por la erosión hídrica y eólica que asemeja un paisaje lunar con agujas y pináculos de arcilla.",
            "direccion": "Mallasa, Zona Sur, Ciudad de La Paz",
            "latitud": Decimal("-16.5683700"),
            "longitud": Decimal("-68.0934100"),
            "horario_apertura": time(8, 0),
            "horario_cierre": time(17, 30),
            "costo_entrada": Decimal("15.00"),
            "tiempo_visita_estimado": 90,
            "dias_cerrado": None,
            "categoria": "Naturaleza y Paisajes",
            "proveedor": "Operadora de Turismo Andina Bolivia S.R.L."
        },
        {
            "nombre": "Mirador Killi Killi",
            "descripcion": "Ubicado en el cerro Santa Bárbara, ofrece una vista panorámica de 360 grados de la ciudad de La Paz y el majestuoso nevado Illimani.",
            "direccion": "Av. La Bandera, Villa Pabón, La Paz",
            "latitud": Decimal("-16.4957600"),
            "longitud": Decimal("-68.1256900"),
            "horario_apertura": time(6, 0),
            "horario_cierre": time(21, 0),
            "costo_entrada": Decimal("0.00"),
            "tiempo_visita_estimado": 45,
            "dias_cerrado": None,
            "categoria": "Urbano e Histórico",
            "proveedor": "Operadora de Turismo Andina Bolivia S.R.L."
        },
        {
            "nombre": "Laguna Colorada - Reserva Eduardo Abaroa",
            "descripcion": "Laguna altoandina de aguas rojizas debido a sedimentos y pigmentación de algas, hogar de miles de flamencos andinos y james.",
            "direccion": "Reserva Nacional de Fauna Andina Eduardo Abaroa, Potosí",
            "latitud": Decimal("-22.2025000"),
            "longitud": Decimal("-67.7733333"),
            "horario_apertura": time(6, 0),
            "horario_cierre": time(18, 0),
            "costo_entrada": Decimal("150.00"),
            "tiempo_visita_estimado": 120,
            "dias_cerrado": None,
            "categoria": "Naturaleza y Paisajes",
            "proveedor": "Transportes Turísticos del Altiplano"
        }
    ]

    for a_data in atractivos_data:
        a = Atractivo.query.filter_by(nombre=a_data["nombre"]).first()
        if not a:
            cat_obj = categoria_map.get(a_data["categoria"])
            prov_obj = proveedor_map.get(a_data["proveedor"])
            if cat_obj and prov_obj:
                a = Atractivo(
                    nombre=a_data["nombre"],
                    descripcion=a_data["descripcion"],
                    direccion=a_data["direccion"],
                    latitud=a_data["latitud"],
                    longitud=a_data["longitud"],
                    horario_apertura=a_data["horario_apertura"],
                    horario_cierre=a_data["horario_cierre"],
                    costo_entrada=a_data["costo_entrada"],
                    tiempo_visita_estimado=a_data["tiempo_visita_estimado"],
                    dias_cerrado=a_data["dias_cerrado"],
                    id_categoria=cat_obj.id_categoria,
                    id_proveedor=prov_obj.id_proveedor
                )
                db.session.add(a)

    db.session.commit()
    print("Seeder de catálogo ejecutado exitosamente.")
