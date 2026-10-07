import os
import sys
import csv
from decimal import Decimal
from datetime import time, date

# Agregar la raíz del proyecto al sys.path para ejecución directa
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import db
from app.models.categoria import Categoria
from app.models.subcategoria import Subcategoria
from app.models.proveedor import Proveedor
from app.models.transporte import Transporte
from app.models.atractivo import Atractivo
from app.models.zona_trafico import ZonaTrafico
from app.models.patron_trafico import PatronTrafico

CSV_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'csv'))

def parse_decimal(val, decimals=None):
    if val is None or str(val).strip() == '':
        return None
    cleaned = str(val).strip().replace(',', '.')
    d = Decimal(cleaned)
    if decimals is not None:
        return round(d, decimals)
    return d

def parse_time(val):
    if val is None or str(val).strip() == '':
        return None
    parts = str(val).strip().split(':')
    if len(parts) >= 2:
        h = int(parts[0])
        m = int(parts[1])
        s = int(parts[2]) if len(parts) >= 3 else 0
        return time(h, m, s)
    return None

def parse_date(val):
    if val is None or str(val).strip() == '':
        return None
    parts = str(val).strip().split('-')
    if len(parts) == 3:
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    return None

def parse_bool(val):
    if val is None or str(val).strip() == '':
        return False
    return str(val).strip().lower() in ['true', '1', 't', 'si', 'yes']

def parse_str(val):
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None

def parse_int(val):
    if val is None or str(val).strip() == '':
        return None
    return int(str(val).strip())

def seed_categorias():
    path = os.path.join(CSV_DIR, 'categoria.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo no encontrado: {path}")

    print("\n[1/7] Seedeando CATEGORIA desde categoria.csv...")
    creados = 0
    existentes = 0

    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            nombre = parse_str(row['nombre'])
            cat = Categoria.query.filter_by(nombre=nombre).first()
            if not cat:
                nueva = Categoria(
                    id_categoria=parse_int(row['id_categoria']),
                    nombre=nombre,
                    descripcion=parse_str(row.get('descripcion'))
                )
                db.session.add(nueva)
                creados += 1
                print(f" [+] Categoria creada: {nombre}")
            else:
                existentes += 1
                print(f" [~] Categoria ya existe: {nombre}")

    db.session.commit()
    print(f" -> CATEGORIA finalizado: {creados} creados, {existentes} existentes.")
    return creados, existentes

def seed_subcategorias():
    path = os.path.join(CSV_DIR, 'subcategoria.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo no encontrado: {path}")

    print("\n[2/7] Seedeando SUBCATEGORIA desde subcategoria.csv...")
    creados = 0
    existentes = 0

    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            nombre = parse_str(row['nombre'])
            id_cat = parse_int(row['id_categoria'])

            # Verificar que la categoría padre exista
            cat_padre = db.session.get(Categoria, id_cat)
            if not cat_padre:
                raise ValueError(f"FK Inválida: Categoría id {id_cat} no existe para subcategoría '{nombre}'.")

            subcat = Subcategoria.query.filter_by(nombre=nombre).first()
            if not subcat:
                nueva = Subcategoria(
                    id_subcategoria=parse_int(row['id_subcategoria']),
                    nombre=nombre,
                    descripcion=parse_str(row.get('descripcion')),
                    id_categoria=id_cat
                )
                db.session.add(nueva)
                creados += 1
                print(f" [+] Subcategoria creada: {nombre} (Cat: {cat_padre.nombre})")
            else:
                existentes += 1
                print(f" [~] Subcategoria ya existe: {nombre}")

    db.session.commit()
    print(f" -> SUBCATEGORIA finalizado: {creados} creados, {existentes} existentes.")
    return creados, existentes

def seed_proveedores():
    path = os.path.join(CSV_DIR, 'proveedor.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo no encontrado: {path}")

    print("\n[3/7] Seedeando PROVEEDOR desde proveedor.csv...")
    creados = 0
    existentes = 0

    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            razon_social = parse_str(row['razon_social'])
            prov = Proveedor.query.filter_by(razon_social=razon_social).first()
            if not prov:
                nuevo = Proveedor(
                    id_proveedor=parse_int(row['id_proveedor']),
                    razon_social=razon_social,
                    tipo=parse_str(row.get('tipo')),
                    contacto_nombre=parse_str(row.get('contacto_nombre')),
                    contacto_telefono=parse_str(row.get('contacto_telefono')),
                    contacto_email=parse_str(row.get('contacto_email')),
                    tarifa_especial=parse_decimal(row.get('tarifa_especial')),
                    observaciones=parse_str(row.get('observaciones'))
                )
                db.session.add(nuevo)
                creados += 1
                print(f" [+] Proveedor creado: {razon_social}")
            else:
                existentes += 1
                print(f" [~] Proveedor ya existe: {razon_social}")

    db.session.commit()
    print(f" -> PROVEEDOR finalizado: {creados} creados, {existentes} existentes.")
    return creados, existentes

def seed_transportes():
    path = os.path.join(CSV_DIR, 'transporte.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo no encontrado: {path}")

    print("\n[4/7] Seedeando TRANSPORTE desde transporte.csv...")
    creados = 0
    existentes = 0

    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            nombre = parse_str(row['nombre'])
            t = Transporte.query.filter_by(nombre=nombre).first()
            if not t:
                nuevo = Transporte(
                    id_transporte=parse_int(row['id_transporte']),
                    nombre=nombre,
                    tipo=parse_str(row['tipo']),
                    capacidad=parse_int(row.get('capacidad')),
                    horario_inicio=parse_time(row.get('horario_inicio')),
                    horario_fin=parse_time(row.get('horario_fin')),
                    costo=parse_decimal(row.get('costo'), 2) or Decimal('0.00'),
                    tipo_costo=parse_str(row['tipo_costo']),
                    velocidad_promedio_kmh=parse_decimal(row.get('velocidad_promedio_kmh'), 2) or Decimal('30.00')
                )
                db.session.add(nuevo)
                creados += 1
                print(f" [+] Transporte creado: {nombre} ({nuevo.tipo}, Bs. {nuevo.costo})")
            else:
                existentes += 1
                print(f" [~] Transporte ya existe: {nombre}")

    db.session.commit()
    print(f" -> TRANSPORTE finalizado: {creados} creados, {existentes} existentes.")
    return creados, existentes

def seed_atractivos():
    path = os.path.join(CSV_DIR, 'atractivo.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo no encontrado: {path}")

    print("\n[5/7] Seedeando ATRACTIVO desde atractivo.csv...")
    creados = 0
    existentes = 0

    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            nombre = parse_str(row['nombre'])
            id_subcat = parse_int(row['id_subcategoria'])
            id_prov = parse_int(row['id_proveedor'])

            # Validar FKs
            subcat = db.session.get(Subcategoria, id_subcat)
            if not subcat:
                raise ValueError(f"FK Inválida: Subcategoría id {id_subcat} no existe para atractivo '{nombre}'.")
            prov = db.session.get(Proveedor, id_prov)
            if not prov:
                raise ValueError(f"FK Inválida: Proveedor id {id_prov} no existe para atractivo '{nombre}'.")

            atr = Atractivo.query.filter_by(nombre=nombre).first()
            if not atr:
                nuevo = Atractivo(
                    id_atractivo=parse_int(row['id_atractivo']),
                    nombre=nombre,
                    descripcion=parse_str(row.get('descripcion')),
                    latitud=parse_decimal(row.get('latitud'), 7),
                    longitud=parse_decimal(row.get('longitud'), 7),
                    direccion=parse_str(row.get('direccion')),
                    horario_apertura=parse_time(row.get('horario_apertura')),
                    horario_cierre=parse_time(row.get('horario_cierre')),
                    costo_entrada=parse_decimal(row.get('costo_entrada'), 2) or Decimal('0.00'),
                    tiempo_visita_estimado=parse_int(row.get('tiempo_visita_estimado')),
                    dias_cerrado=parse_str(row.get('dias_cerrado')),
                    imagen_url=parse_str(row.get('imagen_url')),
                    id_subcategoria=id_subcat,
                    id_proveedor=id_prov,
                    fecha_inicio=parse_date(row.get('fecha_inicio')),
                    fecha_fin=parse_date(row.get('fecha_fin')),
                    afecta_rutas=parse_bool(row.get('afecta_rutas')),
                    sensible_al_clima=parse_bool(row.get('sensible_al_clima')),
                    tipo_clima_ideal=parse_str(row.get('tipo_clima_ideal'))
                )
                db.session.add(nuevo)
                creados += 1
                print(f" [+] Atractivo creado: {nombre}")
            else:
                existentes += 1
                print(f" [~] Atractivo ya existe: {nombre}")

    db.session.commit()
    print(f" -> ATRACTIVO finalizado: {creados} creados, {existentes} existentes.")
    return creados, existentes

def seed_zonas_trafico():
    path = os.path.join(CSV_DIR, 'zona_trafico.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo no encontrado: {path}")

    print("\n[6/7] Seedeando ZONA_TRAFICO desde zona_trafico.csv...")
    creados = 0
    existentes = 0

    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            nombre = parse_str(row['nombre'])
            zona = ZonaTrafico.query.filter_by(nombre=nombre).first()
            if not zona:
                # Quitar comillas externas de geometria_wkt si existen
                wkt = parse_str(row['geometria_wkt'])
                if wkt and wkt.startswith('"') and wkt.endswith('"'):
                    wkt = wkt[1:-1]

                nueva = ZonaTrafico(
                    id_zona=parse_int(row['id_zona']),
                    nombre=nombre,
                    tipo_geometria=parse_str(row['tipo_geometria']),
                    geometria_wkt=wkt,
                    tipo=parse_str(row['tipo'])
                )
                db.session.add(nueva)
                creados += 1
                print(f" [+] Zona creada: {nombre} ({nueva.tipo})")
            else:
                existentes += 1
                print(f" [~] Zona ya existe: {nombre}")

    db.session.commit()
    print(f" -> ZONA_TRAFICO finalizado: {creados} creados, {existentes} existentes.")
    return creados, existentes

def seed_patrones_trafico():
    path = os.path.join(CSV_DIR, 'patron_trafico.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo no encontrado: {path}")

    print("\n[7/7] Seedeando PATRON_TRAFICO desde patron_trafico.csv...")
    creados = 0
    existentes = 0

    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            id_zona = parse_int(row['id_zona'])
            dia = parse_str(row['dia_semana'])
            h_ini = parse_time(row['hora_inicio'])
            h_fin = parse_time(row['hora_fin'])

            # Validar que la zona exista
            zona = db.session.get(ZonaTrafico, id_zona)
            if not zona:
                raise ValueError(f"FK Inválida: Zona id {id_zona} no existe para patrón de tráfico.")

            # Idempotencia: Combinación (id_zona, dia_semana, hora_inicio, hora_fin)
            patron = PatronTrafico.query.filter_by(
                id_zona=id_zona,
                dia_semana=dia,
                hora_inicio=h_ini,
                hora_fin=h_fin
            ).first()

            if not patron:
                nuevo = PatronTrafico(
                    id_patron=parse_int(row['id_patron']),
                    id_zona=id_zona,
                    dia_semana=dia,
                    hora_inicio=h_ini,
                    hora_fin=h_fin,
                    factor_congestion=parse_decimal(row.get('factor_congestion'), 2) or Decimal('1.00'),
                    color_nivel=parse_str(row['color_nivel']),
                    tipo=parse_str(row['tipo'])
                )
                db.session.add(nuevo)
                creados += 1
            else:
                existentes += 1

    db.session.commit()
    print(f" -> PATRON_TRAFICO finalizado: {creados} creados, {existentes} existentes.")
    return creados, existentes

def seed_catalogo():
    """
    Función orquestadora que ejecuta los seeders en orden de dependencias FK:
    1. CATEGORIA
    2. SUBCATEGORIA
    3. PROVEEDOR
    4. TRANSPORTE
    5. ATRACTIVO
    6. ZONA_TRAFICO
    7. PATRON_TRAFICO
    """
    print("\n" + "="*50)
    print(" INICIO DE CARGA DE SEEDERS DESDE DATASET CSV")
    print("="*50)

    # 1. CATEGORIA
    seed_categorias()
    # 2. SUBCATEGORIA
    seed_subcategorias()
    # 3. PROVEEDOR
    seed_proveedores()
    # 4. TRANSPORTE
    seed_transportes()
    # 5. ATRACTIVO
    seed_atractivos()
    # 6. ZONA_TRAFICO
    seed_zonas_trafico()
    # 7. PATRON_TRAFICO
    seed_patrones_trafico()

    # Sincronizar secuencias de Postgres si los IDs fueron insertados explícitamente
    print("\n[*] Sincronizando secuencias de PostgreSQL para claves primarias...")
    tablas_secuencias = [
        ('categoria', 'id_categoria'),
        ('subcategoria', 'id_subcategoria'),
        ('proveedor', 'id_proveedor'),
        ('transporte', 'id_transporte'),
        ('atractivo', 'id_atractivo'),
        ('zona_trafico', 'id_zona'),
        ('patron_trafico', 'id_patron')
    ]
    for tabla, id_col in tablas_secuencias:
        try:
            db.session.execute(db.text(f"SELECT setval(pg_get_serial_sequence('{tabla}', '{id_col}'), coalesce(max({id_col}), 1)) FROM {tabla};"))
        except Exception as e:
            print(f" [!] Advertencia al sincronizar secuencia {tabla}: {e}")
    db.session.commit()

    print("\n" + "="*50)
    print(" [OK] CARGA DE SEEDERS CSV COMPLETADA CON ÉXITO")
    print("="*50)

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_catalogo()
