"""
Seeder del Catálogo de Gestión de Buhos Tours.

Puebla la base de datos con un dataset real, ordenado y coherente de la ciudad de La Paz:
- Categorías: Cultural, Urbano, Naturaleza
- Proveedores representativos
- Transportes urbanos e interurbanos con velocidad promedio en km/h
- 10 atractivos turísticos clave de La Paz (con coordenadas exactas e imagen_url=None)
"""

from decimal import Decimal
from datetime import time
from app import db
from app.models.categoria import Categoria
from app.models.proveedor import Proveedor
from app.models.transporte import Transporte
from app.models.atractivo import Atractivo


def seed_catalogo():
    """
    Puebla la base de datos con categorías, proveedores, transportes y atractivos iniciales de La Paz.
    Es idempotente: crea o actualiza registros según corresponda.
    """
    print("Iniciando seeder de catálogo...")

    # 1. Categorías
    categorias_data = [
        {
            "nombre": "Cultural",
            "descripcion": "Museos, iglesias coloniales, monumentos históricos y patrimonio cultural de la ciudad."
        },
        {
            "nombre": "Urbano",
            "descripcion": "Calles coloniales, plazas emblemáticas, barrios tradicionales y ferias urbanas."
        },
        {
            "nombre": "Naturaleza",
            "descripcion": "Miradores naturales, formaciones geológicas, parques y paisajes naturales."
        }
    ]

    categoria_map = {}
    for c_data in categorias_data:
        cat = Categoria.query.filter_by(nombre=c_data["nombre"]).first()
        if not cat:
            cat = Categoria(nombre=c_data["nombre"], descripcion=c_data["descripcion"])
            db.session.add(cat)
            db.session.flush()
        else:
            cat.descripcion = c_data["descripcion"]
            cat.deleted_at = None
        categoria_map[c_data["nombre"]] = cat

    # 2. Proveedores
    proveedores_data = [
        {
            "razon_social": "Gobierno Autónomo Municipal de La Paz (GAMLP)",
            "tipo": "Entidad Pública Municipal",
            "contacto_nombre": "Unidad de Turismo GAMLP",
            "contacto_telefono": "+591 2 2650000",
            "contacto_email": "turismo@lapaz.bo",
            "tarifa_especial": Decimal("0.00"),
            "observaciones": "Administración de espacios públicos, miradores y centros patrimoniales municipales."
        },
        {
            "razon_social": "Museo de la Coca",
            "tipo": "Entidad Cultural Privada",
            "contacto_nombre": "Administración Museo",
            "contacto_telefono": "+591 2 2311998",
            "contacto_email": "info@cocamuseum.bo",
            "tarifa_especial": Decimal("5.00"),
            "observaciones": "Convenio institucional para visitas guiadas y tarifas grupales."
        },
        {
            "razon_social": "Operadora Turística Andina Bolivia",
            "tipo": "Agencia Receptiva y Excursiones",
            "contacto_nombre": "Carlos Mendoza",
            "contacto_telefono": "+591 2 2445566",
            "contacto_email": "reservas@andinabolivia.bo",
            "tarifa_especial": Decimal("10.00"),
            "observaciones": "Excursiones urbanas, miradores y circuitos turísticos metropolitanos."
        },
        {
            "razon_social": "Asociación Comunitaria de Turismo Urbano La Paz",
            "tipo": "Servicios de Guiaje y Recorridos",
            "contacto_nombre": "Lucía Flores",
            "contacto_telefono": "+591 73245678",
            "contacto_email": "turismo.comunitario@lapaz.bo",
            "tarifa_especial": Decimal("8.00"),
            "observaciones": "Guías locales acreditados para recorridos temáticos en mercados tradicionales."
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
        else:
            prov.tipo = p_data["tipo"]
            prov.contacto_nombre = p_data["contacto_nombre"]
            prov.contacto_telefono = p_data["contacto_telefono"]
            prov.contacto_email = p_data["contacto_email"]
            prov.tarifa_especial = p_data["tarifa_especial"]
            prov.observaciones = p_data["observaciones"]
            prov.deleted_at = None
        proveedor_map[p_data["razon_social"]] = prov

    # 3. Transportes (usando velocidad_promedio_kmh)
    transportes_data = [
        {
            "nombre": "Mi Teleférico - Red Metropolitana",
            "tipo": "Público",
            "capacidad": 10,
            "horario_inicio": time(6, 0),
            "horario_fin": time(23, 0),
            "costo_por_tramo": Decimal("3.00"),
            "tipo_costo": "por_persona",
            "velocidad_promedio_kmh": Decimal("20.00")
        },
        {
            "nombre": "Bus Turístico Privado",
            "tipo": "Privado",
            "capacidad": 20,
            "horario_inicio": time(6, 0),
            "horario_fin": time(22, 0),
            "costo_por_tramo": Decimal("150.00"),
            "tipo_costo": "por_vehiculo",
            "velocidad_promedio_kmh": Decimal("30.00")
        },
        {
            "nombre": "Caminata / Recorrido Peatonal",
            "tipo": "Público",
            "capacidad": 30,
            "horario_inicio": time(6, 0),
            "horario_fin": time(20, 0),
            "costo_por_tramo": Decimal("0.00"),
            "tipo_costo": "por_persona",
            "velocidad_promedio_kmh": Decimal("5.00")
        },
        {
            "nombre": "Taxi / Radiotaxi Urbano",
            "tipo": "Privado",
            "capacidad": 4,
            "horario_inicio": time(5, 0),
            "horario_fin": time(23, 59),
            "costo_por_tramo": Decimal("30.00"),
            "tipo_costo": "por_vehiculo",
            "velocidad_promedio_kmh": Decimal("40.00")
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
                velocidad_promedio_kmh=t_data["velocidad_promedio_kmh"]
            )
            db.session.add(t)
        else:
            t.tipo = t_data["tipo"]
            t.capacidad = t_data["capacidad"]
            t.horario_inicio = t_data["horario_inicio"]
            t.horario_fin = t_data["horario_fin"]
            t.costo_por_tramo = t_data["costo_por_tramo"]
            t.tipo_costo = t_data["tipo_costo"]
            t.velocidad_promedio_kmh = t_data["velocidad_promedio_kmh"]
            t.deleted_at = None

    # 4. 10 Atractivos de La Paz (orden secuencial 1..10, imagen_url=None)
    atractivos_data = [
        {
            "nombre": "Plaza San Francisco",
            "descripcion": "Emblemática plaza histórica del casco urbano central de La Paz, presidida por la majestuosa Basílica y Convento de San Francisco de estilo barroco mestizo.",
            "direccion": "Plaza Mayor de San Francisco, Av. Mariscal Santa Cruz, La Paz",
            "latitud": Decimal("-16.4962000"),
            "longitud": Decimal("-68.1353000"),
            "horario_apertura": time(6, 0),
            "horario_cierre": time(22, 0),
            "costo_entrada": Decimal("0.00"),
            "tiempo_visita_estimado": 45,
            "dias_cerrado": None,
            "categoria": "Cultural",
            "proveedor": "Gobierno Autónomo Municipal de La Paz (GAMLP)"
        },
        {
            "nombre": "Calle Jaén",
            "descripcion": "La calle colonial mejor conservada de La Paz, empedrada y rodeada de casonas coloniales del siglo XVIII que albergan importantes museos y leyendas paceñas.",
            "direccion": "Calle Jaén, entre calles Sucre e Indaburo, Casco Viejo, La Paz",
            "latitud": Decimal("-16.4922000"),
            "longitud": Decimal("-68.1358000"),
            "horario_apertura": time(8, 0),
            "horario_cierre": time(20, 0),
            "costo_entrada": Decimal("0.00"),
            "tiempo_visita_estimado": 60,
            "dias_cerrado": None,
            "categoria": "Urbano",
            "proveedor": "Gobierno Autónomo Municipal de La Paz (GAMLP)"
        },
        {
            "nombre": "Mirador Killi Killi",
            "descripcion": "Mirador estratégico ubicado en el cerro Santa Bárbara que brinda una panorámica de 360 grados sobre la hoyada paceña y el majestuoso nevado Illimani.",
            "direccion": "Av. La Bandera, Villa Pabón, La Paz",
            "latitud": Decimal("-16.4954000"),
            "longitud": Decimal("-68.1273000"),
            "horario_apertura": time(6, 0),
            "horario_cierre": time(21, 0),
            "costo_entrada": Decimal("0.00"),
            "tiempo_visita_estimado": 45,
            "dias_cerrado": None,
            "categoria": "Naturaleza",
            "proveedor": "Gobierno Autónomo Municipal de La Paz (GAMLP)"
        },
        {
            "nombre": "Valle de la Luna",
            "descripcion": "Área protegida municipal caracterizada por sus imponentes formaciones geomorfológicas y pináculos de arcilla esculpidos por la erosión milenaria.",
            "direccion": "Mallasa, Zona Sur, Ciudad de La Paz",
            "latitud": Decimal("-16.5672000"),
            "longitud": Decimal("-68.0944000"),
            "horario_apertura": time(8, 0),
            "horario_cierre": time(17, 30),
            "costo_entrada": Decimal("15.00"),
            "tiempo_visita_estimado": 90,
            "dias_cerrado": None,
            "categoria": "Naturaleza",
            "proveedor": "Gobierno Autónomo Municipal de La Paz (GAMLP)"
        },
        {
            "nombre": "Museo de la Coca",
            "descripcion": "Museo interactivo y cultural dedicado a la historia, botánica, uso tradicional, ritual y valor socioeconómico de la sagrada hoja de coca en los Andes.",
            "direccion": "Calle Linares #906, Zona Rosario, La Paz",
            "latitud": Decimal("-16.4975700"),
            "longitud": Decimal("-68.1383000"),
            "horario_apertura": time(9, 0),
            "horario_cierre": time(19, 0),
            "costo_entrada": Decimal("20.00"),
            "tiempo_visita_estimado": 60,
            "dias_cerrado": None,
            "categoria": "Cultural",
            "proveedor": "Museo de la Coca"
        },
        {
            "nombre": "Cementerio General",
            "descripcion": "Necrópolis histórica fundada en 1831 que alberga mausoleos monumentales, arte funerario neoclásico y una destacada muestra de muralismo urbano contemporáneo.",
            "direccion": "Av. Baptista y calle Picada, Zona Callampaya, La Paz",
            "latitud": Decimal("-16.4969200"),
            "longitud": Decimal("-68.1516800"),
            "horario_apertura": time(8, 0),
            "horario_cierre": time(17, 0),
            "costo_entrada": Decimal("0.00"),
            "tiempo_visita_estimado": 75,
            "dias_cerrado": None,
            "categoria": "Cultural",
            "proveedor": "Gobierno Autónomo Municipal de La Paz (GAMLP)"
        },
        {
            "nombre": "Plaza Murillo",
            "descripcion": "Centro del poder político de Bolivia y corazón histórico de La Paz, rodeada por el Palacio Quemado, la Casa Grande del Pueblo, la Asamblea Legislativa y la Catedral Metropolitana.",
            "direccion": "Plaza Murillo, entre calles Comercio, Socabaya, Ayacucho y Ballivián, La Paz",
            "latitud": Decimal("-16.4957000"),
            "longitud": Decimal("-68.1335000"),
            "horario_apertura": time(6, 0),
            "horario_cierre": time(22, 0),
            "costo_entrada": Decimal("0.00"),
            "tiempo_visita_estimado": 45,
            "dias_cerrado": None,
            "categoria": "Cultural",
            "proveedor": "Gobierno Autónomo Municipal de La Paz (GAMLP)"
        },
        {
            "nombre": "Mercado de las Brujas",
            "descripcion": "Tradicional mercado andino en el barrio de San Sebastián famoso por la venta de hierbas medicinales, amuletos, mesas rituales y artesanías tradicionales.",
            "direccion": "Calle Linares y Calle Sagárnaga, Zona Rosario, La Paz",
            "latitud": Decimal("-16.4959800"),
            "longitud": Decimal("-68.1389000"),
            "horario_apertura": time(8, 30),
            "horario_cierre": time(20, 30),
            "costo_entrada": Decimal("0.00"),
            "tiempo_visita_estimado": 60,
            "dias_cerrado": None,
            "categoria": "Urbano",
            "proveedor": "Asociación Comunitaria de Turismo Urbano La Paz"
        },
        {
            "nombre": "Plaza Abaroa (Sopocachi)",
            "descripcion": "Espacio público y centro neurálgico del barrio bohemio de Sopocachi, homenaje al héroe Eduardo Abaroa, rodeado de cafés, galerías de arte y vida cultural.",
            "direccion": "Plaza Abaroa, entre calles 20 de Octubre, Sánchez Lima y Belisario Salinas, Sopocachi, La Paz",
            "latitud": Decimal("-16.5105700"),
            "longitud": Decimal("-68.1266800"),
            "horario_apertura": time(6, 0),
            "horario_cierre": time(23, 0),
            "costo_entrada": Decimal("0.00"),
            "tiempo_visita_estimado": 45,
            "dias_cerrado": None,
            "categoria": "Urbano",
            "proveedor": "Operadora Turística Andina Bolivia"
        },
        {
            "nombre": "Plaza Humboldt (Calacoto)",
            "descripcion": "Punto de encuentro y feria de arte tradicional en la Zona Sur paceña, donde pintores, escultores y artesanos exhiben sus creaciones al aire libre los fines de semana.",
            "direccion": "Av. Costanera y calle 8 de Calacoto, Zona Sur, La Paz",
            "latitud": Decimal("-16.5419400"),
            "longitud": Decimal("-68.0916300"),
            "horario_apertura": time(7, 0),
            "horario_cierre": time(20, 0),
            "costo_entrada": Decimal("0.00"),
            "tiempo_visita_estimado": 45,
            "dias_cerrado": None,
            "categoria": "Urbano",
            "proveedor": "Operadora Turística Andina Bolivia"
        }
    ]

    for a_data in atractivos_data:
        cat_obj = categoria_map.get(a_data["categoria"])
        prov_obj = proveedor_map.get(a_data["proveedor"])
        if not cat_obj or not prov_obj:
            continue

        a = Atractivo.query.filter_by(nombre=a_data["nombre"]).first()
        if not a:
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
                imagen_url=None,
                id_categoria=cat_obj.id_categoria,
                id_proveedor=prov_obj.id_proveedor
            )
            db.session.add(a)
        else:
            a.descripcion = a_data["descripcion"]
            a.direccion = a_data["direccion"]
            a.latitud = a_data["latitud"]
            a.longitud = a_data["longitud"]
            a.horario_apertura = a_data["horario_apertura"]
            a.horario_cierre = a_data["horario_cierre"]
            a.costo_entrada = a_data["costo_entrada"]
            a.tiempo_visita_estimado = a_data["tiempo_visita_estimado"]
            a.dias_cerrado = a_data["dias_cerrado"]
            a.id_categoria = cat_obj.id_categoria
            a.id_proveedor = prov_obj.id_proveedor
            a.deleted_at = None

    db.session.commit()
    print("Seeder de catálogo ejecutado exitosamente.")
