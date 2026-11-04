# AUDITORIA TÉCNICA COMPLETA DEL SISTEMA WEB DE ITINERARIOS TURÍSTICOS
**Proyecto:** Sistema Web de Itinerarios Turísticos Personalizados para la Agencia Buhos Tours (La Paz, Bolivia)  
**Documento Base:** Soporte Técnico Integral para la Redacción del Capítulo III de Proyecto de Grado  
**Fecha de Auditoría:** 2026-10-29  
**Tipo de Inspección:** Estática de Código Fuente y Arquitectura de Software (Solo Lectura)  

---

## 1. Arquitectura y Stack Tecnológico

### 1.1. Lista de Dependencias del Proyecto
A partir del análisis de las importaciones del núcleo de la aplicación, el archivo `README.md`, el entorno virtual y la configuración del sistema, se identifican las librerías principales que componen el stack tecnológico:

| Dependencia / Paquete | Versión Referencial / Propósito Técnico |
| :--- | :--- |
| **Python** | 3.10 / 3.11 — Lenguaje base de ejecución backend. |
| **Flask** | 2.3.x — Framework web WSGI ligero y modular (arquitectura monolítica por capas). |
| **Flask-SQLAlchemy** | 3.1.x — ORM (Object Relational Mapping) para mapeo relacional en PostgreSQL. |
| **Flask-Migrate / Alembic** | 4.0.x — Control de versiones y migraciones estructuradas del esquema de base de datos. |
| **Flask-Login** | 0.6.x — Gestión de ciclo de vida de sesiones, autenticación de usuarios y cookies seguras. |
| **Flask-Mail** | 0.9.x — Envío transaccional y asíncrono de correos electrónicos mediante SMTP. |
| **psycopg2-binary** | Driver nativo en C/Python para comunicación TCP/IP de alto rendimiento con PostgreSQL. |
| **python-dotenv** | Carga de variables de entorno seguras desde archivo `.env`. |
| **Werkzeug** | Funciones criptográficas (`generate_password_hash`, `check_password_hash`) y utilidades WSGI. |
| **pyotp** | Generación y verificación de tokens criptográficos de un solo uso basados en tiempo (TOTP RFC 6238). |
| **qrcode & Pillow (PIL)** | Generación dinámica y renderizado en memoria de imágenes QR para vinculación con Google Authenticator / Authy. |
| **pymoo** | Framework avanzado de algoritmos de optimización multiobjetivo (implementación nativa de NSGA-II, SBX, PM, HV, GD, Spacing). |
| **NumPy** | Operaciones matriciales vectorizadas, cálculo de distancias, normalizaciones y transformaciones numéricas. |
| **Shapely** | Análisis espacial geográfico de geometrías vectoriales (WKT) e intersecciones espaciales con trayectorias. |
| **Requests** | Cliente HTTP síncrono con gestión de timeouts para consumo de APIs REST externas (OSRM, Open-Meteo, BCB). |
| **ReportLab** | Generación de documentos PDF empresariales estructurados mediante el motor Platypus. |
| **Matplotlib** | Generación estática de gráficos estadísticos (barras horizontales y series temporales) en memoria (backend Agg). |
| **Click** | CLI extensible de Flask para scripts de seeding y precalculo de matrices. |

---

### 1.2. Estructura de Carpetas (MVC + Service Layer)
El proyecto implementa una **Arquitectura Monolítica por Capas (Layered Architecture)** acoplada estrictamente al patrón **MVC (Modelo - Vista - Controlador)** junto con una **Capa de Servicios de Negocio (Service Layer)** para aislar la lógica matemática y las integraciones externas de los controladores HTTP.

```text
📁 buhos_tours/
│
├── 📁 app/                                # Núcleo de la aplicación Flask
│   ├── 📄 __init__.py                     # Application Factory (create_app), extensiones, CLI commands, middleware
│   │
│   ├── 📁 models/                         # [Capa de Datos - Modelo (M)] Modelos de SQLAlchemy
│   │   ├── 📄 __init__.py                 # Exportación de entidades
│   │   ├── 📄 rol.py                      # Roles de usuario (admin, agente, turista)
│   │   ├── 📄 usuario.py                  # Credenciales, 2FA, tokens, soft-delete
│   │   ├── 📄 turista.py                  # Perfil de turista y titular de viaje
│   │   ├── 📄 categoria.py                # Clasificación general de atractivos
│   │   ├── 📄 subcategoria.py             # Subclasificación de intereses turísticos
│   │   ├── 📄 proveedor.py                # Operadores de atractivos turísticos
│   │   ├── 📄 transporte.py               # Medios de transporte, costos y capacidades
│   │   ├── 📄 atractivo.py                # Puntos de interés, horarios, costos, sensibilidad climática
│   │   ├── 📄 zona_trafico.py             # Zonas geoespaciales con congestión (WKT)
│   │   ├── 📄 patron_trafico.py           # Franjas horarias y factores de congestión vial
│   │   ├── 📄 generacion.py               # Cabecera de ejecución del algoritmo
│   │   ├── 📄 itinerario.py               # Solución de itinerario generada / guardada
│   │   ├── 📄 itinerario_detalle.py       # Paradas diarias, horas estimadas y clima
│   │   ├── 📄 itinerario_detalle_trafico.py# Tabla asociativa N:M parada-tráfico
│   │   ├── 📄 viaje_turista.py            # Tabla asociativa itinerario-turistas (titular y acompañantes)
│   │   ├── 📄 tipo_cambio.py              # Histórico de tipo de cambio oficial BOB/USD
│   │   ├── 📄 consulta_nsga2.py           # Métricas académicas y caché de resultados
│   │   ├── 📄 distancia_atractivo.py      # Matriz OSRM precalculada de distancias y polylines
│   │   └── 📄 archivo_pareto.py           # Historial acumulado de frente de Pareto no dominado
│   │
│   ├── 📁 controllers/                    # [Capa de Control - Controlador (C)] Rutas y Blueprints
│   │   ├── 📄 __init__.py
│   │   ├── 📄 auth_controller.py          # Autenticación, registro, login, 2FA, cambio forzado de password
│   │   ├── 📄 admin_controller.py         # Dashboard admin, CRUDs maestros y tipo de cambio
│   │   ├── 📄 agente_controller.py        # Dashboard de agente y edición operativa restringida
│   │   ├── 📄 turista_controller.py       # Dashboard y perfil de turista
│   │   ├── 📄 catalogo_controller.py      # Exploración pública de catálogo y mapas
│   │   ├── 📄 itinerario_controller.py    # Generador NSGA-II, guardado, acompañantes y detalle
│   │   ├── 📄 reporte_controller.py       # Métricas de negocio, descarga CSV y PDF Platypus
│   │   └── 📄 usuario_controller.py       # Redirección administrativa
│   │
│   ├── 📁 services/                       # [Capa de Negocio (Service Layer)] Lógica de dominio pura
│   │   ├── 📄 __init__.py
│   │   ├── 📄 nsga2_service.py            # Motor algorítmico NSGA-II multiobjetivo
│   │   ├── 📄 itinerario_service.py       # Orquestador de generación, caché SHA-256, guardado
│   │   ├── 📄 metricas_pareto_service.py  # Hipervolumen (HV), Generational Distance (GD), Spread
│   │   ├── 📄 auth_service.py             # Lógica de seguridad, contraseñas seguras y TOTP
│   │   ├── 📄 usuario_service.py          # Consultas, paginación y estadísticas de usuarios
│   │   ├── 📄 atractivo_service.py        # Validaciones de atractivos, geodatos y Pillow
│   │   ├── 📄 transporte_service.py       # Reglas de negocio de tarifas y flotas
│   │   ├── 📄 categoria_service.py        # Mantenimiento de categorías y soft-delete en cascada
│   │   ├── 📄 subcategoria_service.py     # Mantenimiento de subcategorías
│   │   ├── 📄 proveedor_service.py        # Gestión de proveedores turísticos
│   │   ├── 📄 distance_service.py         # Matriz de distancias BD y cliente OSRM
│   │   ├── 📄 routing_service.py          # Enrutamiento con caché de memoria intra-proceso
│   │   ├── 📄 weather_service.py          # Cliente Open-Meteo, 4 zonas de La Paz, clasificación WMO
│   │   ├── 📄 exchange_service.py         # Cliente API BCB, caché de 1h y conversión monetaria
│   │   ├── 📄 email_service.py            # Envío asíncrono con hilos daemon de Flask-Mail
│   │   └── 📄 reporte_service.py          # Agregaciones SQL y series para dashboards
│   │
│   ├── 📁 utils/                          # Utilidades transversales
│   │   ├── 📄 __init__.py
│   │   └── 📄 decorators.py               # Decoradores @role_required, @admin_required, @require_2fa
│   │
│   ├── 📁 templates/                      # [Capa de Presentación - Vista (V)] Plantillas Jinja2
│   │   ├── 📄 base.html                   # Layout maestro con navbar, sidebar oscura y loaders
│   │   ├── 📁 auth/                       # Login, registro, 2FA, reseteo de claves
│   │   ├── 📁 dashboards/                 # Paneles diferenciados para admin, agente y turista
│   │   ├── 📁 admin/                      # Vistas CRUD de usuarios, categorías, proveedores, etc.
│   │   ├── 📁 agente/                     # Formularios de edición parcial para agentes
│   │   ├── 📁 catalogo/                   # Vistas de catálogo y mapas interactivos
│   │   ├── 📁 itinerarios/                # Generador interactivo, visor de resultados y detalle
│   │   │   └── 📁 partials/               # Paneles modulares (configuración, operadores, resultados)
│   │   ├── 📁 reportes/                   # Dashboard de analítica y reportes
│   │   └── 📁 perfil/                     # Gestión de perfil y seguridad de cuenta
│   │
│   ├── 📁 static/                         # Recursos estáticos servidos por el servidor
│   │   ├── 📁 css/                        # Hojas de estilo personalizadas (styles.css)
│   │   ├── 📁 js/                         # Scripts frontend (itinerario_acompanantes.js)
│   │   ├── 📁 img/                        # Logotipos y recursos visuales
│   │   └── 📁 uploads/                    # Almacenamiento de imágenes subidas de atractivos
│   │
│   └── 📁 seeds/                          # Datos iniciales para la puesta en marcha
│       ├── 📄 rol_seeder.py               # Población de roles (admin, agente, turista)
│       ├── 📄 user_seeder.py              # Usuarios administrativos y agentes semilla
│       └── 📄 catalogo_seeder.py          # Inserción de atractivos y transportes desde CSV
│
├── 📁 migrations/                         # Versiones de migración de esquema SQLAlchemy
├── 📁 tests/                              # Pruebas unitarias automatizadas con unittest
├── 📄 config.py                           # Clase de configuración Config y lectura de variables .env
├── 📄 run.py                              # Script de arranque del servidor (host='0.0.0.0', port=5000)
├── 📄 requirements.txt                    # Lista de paquetes y dependencias del proyecto
└── 📄 README.md                           # Documentación de instalación y arquitectura técnica
```

---

### 1.3. Configuraciones Clave del Entorno
Leídas directamente desde `config.py` y `app/__init__.py`:

1. **Base de Datos:**
   - URI de conexión: Variable `DATABASE_URL` (por defecto `postgresql://postgres:admin123@localhost:5432/buhos_tours`).
   - `SQLALCHEMY_TRACK_MODIFICATIONS = False` para suprimir sobrecarga de eventos en memoria.
2. **Seguridad y Criptografía:**
   - `SECRET_KEY`: Obtenido de `os.environ.get('SECRET_KEY')` con fallback seguro para desarrollo local.
3. **Servicio de Correo (Flask-Mail):**
   - Servidor SMTP: `MAIL_SERVER = 'smtp.gmail.com'`, puerto `587`.
   - Cifrado: `MAIL_USE_TLS = True`, `MAIL_USE_SSL = False`.
   - Credenciales: Usuario `MAIL_USERNAME` y contraseña de aplicación `MAIL_PASSWORD`.
   - Remitente por defecto: `MAIL_DEFAULT_SENDER = 'alfredocortez12god@gmail.com'`.
   - `MAIL_SUPPRESS_SEND = False` (configurable para tests).
4. **Carga y Manipulación de Archivos:**
   - Límite de carga: `MAX_CONTENT_LENGTH = 5 * 1024 * 1024` (5 MB).
   - Carpeta de almacenamiento: `app/static/uploads/atractivos`.
   - Extensiones permitidas: `{'png', 'jpg', 'jpeg', 'webp'}`.
5. **Configuración de Sesiones y Flask-Login:**
   - Vista de redirección no autorizada: `login_manager.login_view = 'auth.login'`.
   - Mensaje de acceso restringido: `'Por favor inicia sesión para acceder a esta página.'` (categoría `'warning'`).
   - `load_user`: Carga de entidades mediante `db.session.get(Usuario, int(user_id))`.
6. **Middlewares Globales de Aplicación (`@app.before_request`):**
   - `check_schema_updates`: Ejecuta verificaciones DDL dinámicas (`IF NOT EXISTS`) para asegurar compatibilidad de columnas como `snapshot_json`, `num_personas` y la tabla `archivo_pareto`.
   - `enforce_security_policies`: Interceptor de peticiones que fuerza el flujo de cambio obligatorio de clave temporal (`must_change_password`) y la activación de 2FA obligatorio para usuarios con rol `admin` o `agente`.
7. **Procesadores de Contexto y Filtros Jinja2:**
   - Inyección de variables globales: `inject_exchange_rate` disponibiliza `tc_oficial` y `convertir_bs_a_usd` en todas las plantillas.
   - Filtro personalizado `|usd`: Convierte dinámicamente montos de BOB a USD aplicando el tipo de cambio oficial del BCB.

---

## 2. Base de Datos y Modelos (Capa de Datos)

El sistema utiliza **PostgreSQL** como motor relacional, administrado mediante **Flask-SQLAlchemy**. Cuenta con un esquema de 19 modelos persistentes.

### 2.1. Catálogo Completo de Modelos

#### 1. `Rol` (Tabla: `rol`)
- **Propósito:** Catálogo de roles para el control de acceso basado en roles (RBAC).
- **Campos:**
  - `id_rol`: `Integer`, Primary Key, autoincremental.
  - `nombre`: `String(20)`, Unique, Nullable=False (Valores: `'admin'`, `'agente'`, `'turista'`).
- **Relaciones:** `usuarios` (1:N hacia `Usuario`).

#### 2. `Usuario` (Tabla: `usuario`)
- **Propósito:** Entidad de autenticación, control de seguridad, 2FA y auditoría de personal y clientes.
- **Campos:**
  - `id_usuario`: `Integer`, Primary Key, autoincremental.
  - `nombres`: `String(80)`, Nullable=False.
  - `apellidos`: `String(80)`, Nullable=False.
  - `email`: `String(100)`, Nullable=False, Unique, Index=True.
  - `contrasenia`: `String(255)`, Nullable=False (hash generado por Werkzeug).
  - `id_rol`: `Integer`, Foreign Key (`rol.id_rol`), Nullable=False.
  - `fecha_registro`: `Date`, Nullable=False, Default=`datetime.utcnow`.
  - `deleted_at`: `DateTime`, Nullable=True, Default=None (Soft Delete).
  - `two_factor_secret`: `String(32)`, Nullable=True (clave base32 TOTP).
  - `two_factor_enabled`: `Boolean`, Nullable=False, Default=False.
  - `two_factor_confirmed_at`: `DateTime`, Nullable=True.
  - `must_change_password`: `Boolean`, Nullable=False, Default=False.
  - `temp_password_expires_at`: `DateTime`, Nullable=True.
  - `reset_token`: `String(255)`, Nullable=True, Unique, Index=True.
  - `reset_token_expires_at`: `DateTime`, Nullable=True.
  - `reset_token_used`: `Boolean`, Nullable=False, Default=False.
- **Propiedades Especiales:**
  - `is_active`: Retorna `self.deleted_at is None` (bloquea inicio de sesión en Flask-Login si fue eliminado).
  - `is_temp_password_expired`: Evalúa si la clave temporal superó las 24 horas de vigencia.
- **Relaciones:**
  - `rol`: `db.relationship('Rol', backref='usuarios')`.
  - `turista`: Relación 1:1 inversa mediante backref en `Turista`.
  - `generaciones`: Relación 1:N inversa hacia `Generacion`.
  - `tipos_cambio`: Relación 1:N inversa hacia `TipoCambio`.

#### 3. `Turista` (Tabla: `turista`)
- **Propósito:** Perfil turístico de viajeros y pasajeros para formalización de itinerarios y reservas.
- **Campos:**
  - `id_turista`: `Integer`, Primary Key, autoincremental.
  - `id_usuario`: `Integer`, Foreign Key (`usuario.id_usuario`), Nullable=True, Unique=True.
  - `nombres`: `String(80)`, Nullable=False.
  - `apellidos`: `String(80)`, Nullable=False.
  - `nacionalidad`: `String(50)`, Nullable=True.
  - `procedencia`: `String(50)`, Nullable=True (País / Ciudad de origen).
  - `nro_documento`: `String(20)`, Nullable=True, Unique=True (Cédula o Pasaporte).
  - `fecha_nacimiento`: `Date`, Nullable=True.
  - `pasaporte_vencimiento`: `Date`, Nullable=True.
  - `email`: `String(100)`, Nullable=True.
  - `telefono`: `String(20)`, Nullable=True.
- **Relaciones:**
  - `usuario`: `db.relationship('Usuario', backref=db.backref('turista', uselist=False))`.
  - `viajes`: Relación 1:N inversa hacia `ViajeTurista`.

#### 4. `Categoria` (Tabla: `categoria`)
- **Propósito:** Agrupación superior de atractivos (Cultural, Naturaleza, Gastronomía, Urbano, etc.).
- **Campos:**
  - `id_categoria`: `Integer`, Primary Key, autoincremental.
  - `nombre`: `String(50)`, Nullable=False, Unique=True.
  - `descripcion`: `String(200)`, Nullable=True.
  - `deleted_at`: `DateTime`, Nullable=True, Default=None (Soft Delete).
- **Relaciones:**
  - `subcategorias`: Relación 1:N inversa desde `Subcategoria`.

#### 5. `Subcategoria` (Tabla: `subcategoria`)
- **Propósito:** Nivel específico de afinidad turística (Museos, Miradores, Parques, Sitios Patrimoniales).
- **Campos:**
  - `id_subcategoria`: `Integer`, Primary Key, autoincremental.
  - `nombre`: `String(50)`, Nullable=False, Unique=True.
  - `descripcion`: `String(200)`, Nullable=True.
  - `id_categoria`: `Integer`, Foreign Key (`categoria.id_categoria`), Nullable=False.
  - `deleted_at`: `DateTime`, Nullable=True, Default=None (Soft Delete).
- **Relaciones:**
  - `categoria`: `db.relationship('Categoria', backref='subcategorias', lazy=True)`.
  - `atractivos`: Relación 1:N inversa desde `Atractivo`.

#### 6. `Proveedor` (Tabla: `proveedor`)
- **Propósito:** Empresas administradoras o comunitarias de atractivos turísticos.
- **Campos:**
  - `id_proveedor`: `Integer`, Primary Key, autoincremental.
  - `razon_social`: `String(100)`, Nullable=False.
  - `tipo`: `String(50)`, Nullable=True.
  - `contacto_nombre`: `String(100)`, Nullable=True.
  - `contacto_telefono`: `String(20)`, Nullable=True.
  - `contacto_email`: `String(100)`, Nullable=True.
  - `tarifa_especial`: `Numeric(10, 2)`, Nullable=True.
  - `observaciones`: `Text`, Nullable=True.
  - `deleted_at`: `DateTime`, Nullable=True, Default=None (Soft Delete).
- **Relaciones:**
  - `atractivos`: Relación 1:N inversa hacia `Atractivo`.

#### 7. `Transporte` (Tabla: `transporte`)
- **Propósito:** Medios de movilidad disponibles para conectar atractivos (Taxi, Van, Teleférico, Caminata).
- **Campos:**
  - `id_transporte`: `Integer`, Primary Key, autoincremental.
  - `nombre`: `String(100)`, Nullable=False.
  - `tipo`: `String(20)`, Nullable=False (`'Privado'` o `'Público'`).
  - `capacidad`: `Integer`, Nullable=True (capacidad máxima de pasajeros).
  - `horario_inicio`: `Time`, Nullable=True.
  - `horario_fin`: `Time`, Nullable=True.
  - `costo`: `Numeric(10, 2)`, Nullable=False, Default=0.0.
  - `tipo_costo`: `String(20)`, Nullable=False (`'por_dia'` o `'por_persona'`).
  - `velocidad_promedio_kmh`: `Numeric(5, 2)`, Nullable=False, Default=30.0.
  - `deleted_at`: `DateTime`, Nullable=True, Default=None (Soft Delete).
- **Relaciones:**
  - `detalles`: Relación 1:N inversa hacia `ItinerarioDetalle`.

#### 8. `Atractivo` (Tabla: `atractivo`)
- **Propósito:** Puntos geográficos y destinos de visita que componen las paradas de los itinerarios.
- **Campos:**
  - `id_atractivo`: `Integer`, Primary Key, autoincremental.
  - `nombre`: `String(100)`, Nullable=False, Unique=True.
  - `descripcion`: `String(500)`, Nullable=True.
  - `latitud`: `Numeric(10, 7)`, Nullable=True.
  - `longitud`: `Numeric(10, 7)`, Nullable=True.
  - `direccion`: `String(200)`, Nullable=True.
  - `horario_apertura`: `Time`, Nullable=True.
  - `horario_cierre`: `Time`, Nullable=True.
  - `costo_entrada`: `Numeric(10, 2)`, Nullable=False, Default=0.0.
  - `tiempo_visita_estimado`: `Integer`, Nullable=True (en minutos).
  - `dias_cerrado`: `Text`, Nullable=True (días separados por coma, ej. `'Lunes,Martes'`).
  - `imagen_url`: `String(255)`, Nullable=True.
  - `fecha_inicio`: `Date`, Nullable=True (fechas estacionales).
  - `fecha_fin`: `Date`, Nullable=True.
  - `afecta_rutas`: `Boolean`, Nullable=False, Default=False.
  - `sensible_al_clima`: `Boolean`, Nullable=False, Default=False.
  - `tipo_clima_ideal`: `String(100)`, Nullable=True.
  - `id_subcategoria`: `Integer`, Foreign Key (`subcategoria.id_subcategoria`), Nullable=False.
  - `id_proveedor`: `Integer`, Foreign Key (`proveedor.id_proveedor`), Nullable=False.
  - `deleted_at`: `DateTime`, Nullable=True, Default=None (Soft Delete).
- **Relaciones:**
  - `subcategoria`: `db.relationship('Subcategoria', backref='atractivos', lazy=True)`.
  - `proveedor`: `db.relationship('Proveedor', backref='atractivos', lazy=True)`.
  - `detalles`: Relación 1:N hacia `ItinerarioDetalle`.
  - `distancias_salida`: Relación 1:N hacia `DistanciaAtractivo` (origen).
  - `distancias_llegada`: Relación 1:N hacia `DistanciaAtractivo` (destino).

#### 9. `ZonaTrafico` (Tabla: `zona_trafico`)
- **Propósito:** Polígonos o polilíneas espaciales de la ciudad de La Paz con patrones de congestión conocidos.
- **Campos:**
  - `id_zona`: `Integer`, Primary Key, autoincremental.
  - `nombre`: `String(100)`, Nullable=False.
  - `tipo_geometria`: `String(20)`, Nullable=False (`'poligono'`, `'polilinea'`, `'punto'`).
  - `geometria_wkt`: `Text`, Nullable=False (definición geométrica en Well-Known Text).
  - `tipo`: `String(20)`, Nullable=False (`'trafico'`, `'feria'`, `'cierre'`, `'bloqueo'`).
  - `deleted_at`: `DateTime`, Nullable=True, Default=None (Soft Delete).
- **Relaciones:**
  - `patrones`: Relación 1:N hacia `PatronTrafico`.

#### 10. `PatronTrafico` (Tabla: `patron_trafico`)
- **Propósito:** Franjas horarias y coeficientes multiplicadores de retraso vial por día de la semana.
- **Campos:**
  - `id_patron`: `Integer`, Primary Key, autoincremental.
  - `id_zona`: `Integer`, Foreign Key (`zona_trafico.id_zona`), Nullable=False.
  - `dia_semana`: `String(20)`, Nullable=False (ej. `'lunes'`, `'domingo'`, `'todos'`).
  - `hora_inicio`: `Time`, Nullable=False.
  - `hora_fin`: `Time`, Nullable=False.
  - `factor_congestion`: `Numeric(4, 2)`, Nullable=False, Default=1.0.
  - `color_nivel`: `String(20)`, Nullable=False (`'verde'`, `'amarillo'`, `'naranja'`, `'rojo'`).
  - `tipo`: `String(20)`, Nullable=False (`'trafico'`, `'feria'`, `'cierre'`).
  - `deleted_at`: `DateTime`, Nullable=True, Default=None (Soft Delete).
- **Relaciones:**
  - `zona`: `db.relationship('ZonaTrafico', backref='patrones', lazy=True)`.
  - `detalles_trafico`: Relación 1:N hacia `ItinerarioDetalleTrafico`.

#### 11. `Generacion` (Tabla: `generacion`)
- **Propósito:** Registro maestro de cada proceso de optimización multiobjetivo ejecutado por un usuario.
- **Campos:**
  - `id_generacion`: `Integer`, Primary Key, autoincremental.
  - `fecha_generacion`: `DateTime`, Nullable=False, Default=`datetime.utcnow`.
  - `id_usuario`: `Integer`, Foreign Key (`usuario.id_usuario`), Nullable=False.
  - `fecha_inicio_viaje`: `Date`, Nullable=False.
  - `fecha_fin_viaje`: `Date`, Nullable=False.
  - `presupuesto`: `Numeric(10, 2)`, Nullable=False.
  - `cantidad_soluciones`: `Integer`, Nullable=False.
  - `observaciones`: `Text`, Nullable=True.
  - `hora_inicio_dia`: `Time`, Nullable=True.
  - `hora_fin_dia`: `Time`, Nullable=True.
  - `auto_rango_paradas`: `Boolean`, Nullable=False, Default=True.
  - `min_paradas`: `Integer`, Nullable=True.
  - `max_paradas`: `Integer`, Nullable=True.
  - `usar_clima`: `Boolean`, Nullable=False, Default=True.
  - `intereses_json`: `Text`, Nullable=True (payload serializado de preferencias).
- **Relaciones:**
  - `usuario`: `db.relationship('Usuario', backref='generaciones', lazy=True)`.
  - `itinerarios`: Relación 1:N hacia `Itinerario`.
  - `consultas_nsga2`: Relación 1:N hacia `ConsultaNSGA2`.

#### 12. `Itinerario` (Tabla: `itinerario`)
- **Propósito:** Solución concreta (ruta) seleccionada y guardada como reserva formal o borrador de viaje.
- **Campos:**
  - `id_itinerario`: `Integer`, Primary Key, autoincremental.
  - `id_generacion`: `Integer`, Foreign Key (`generacion.id_generacion`), Nullable=False.
  - `numero_solucion`: `Integer`, Nullable=False (índice en el frente de Pareto).
  - `estado`: `String(20)`, Nullable=False, Default=`'Borrador'` (`'Borrador'`, `'Confirmado'`, `'Cancelado'`).
  - `tiempo_total_estimado`: `Numeric(10, 2)`, Nullable=True (minutos).
  - `codigo_confirmacion`: `UUID`, Default=`uuid.uuid4`, Unique=True.
  - `voucher_generado`: `Boolean`, Nullable=False, Default=False.
  - `deleted_at`: `DateTime`, Nullable=True, Default=None (Soft Delete).
  - `afinidad`: `Numeric(5, 4)`, Nullable=True (0.0000 a 1.0000).
  - `costo_total_bob`: `Numeric(10, 2)`, Nullable=True.
  - `costo_entradas_bob`: `Numeric(10, 2)`, Nullable=True.
  - `costo_transporte_bob`: `Numeric(10, 2)`, Nullable=True.
  - `distancia_total_km`: `Numeric(8, 2)`, Nullable=True.
  - `fecha_inicio`: `Date`, Nullable=True.
  - `fecha_fin`: `Date`, Nullable=True.
  - `dias_totales`: `Integer`, Nullable=True, Default=1.
  - `num_personas`: `Integer`, Nullable=False, Default=1.
  - `es_viable`: `Boolean`, Nullable=False, Default=True.
  - `snapshot_json`: `Text`, Nullable=True (fotografía estática del JSON de la solución para garantizar inmutabilidad).
- **Relaciones:**
  - `generacion`: `db.relationship('Generacion', backref='itinerarios', lazy=True)`.
  - `detalles`: `db.relationship('ItinerarioDetalle', backref=db.backref('itinerario', cascade='all, delete-orphan'))`.
  - `viajes_turistas`: `db.relationship('ViajeTurista', backref=db.backref('itinerario', cascade='all, delete-orphan'))`.

#### 13. `ItinerarioDetalle` (Tabla: `itinerario_detalle`)
- **Propósito:** Parada individual de un itinerario en un día específico con horas y condiciones meteorológicas.
- **Campos:**
  - `id_detalle`: `Integer`, Primary Key, autoincremental.
  - `id_itinerario`: `Integer`, Foreign Key (`itinerario.id_itinerario`), Nullable=False.
  - `id_atractivo`: `Integer`, Foreign Key (`atractivo.id_atractivo`), Nullable=False.
  - `id_transporte`: `Integer`, Foreign Key (`transporte.id_transporte`), Nullable=True.
  - `dia`: `Integer`, Nullable=False (1, 2, ...).
  - `orden`: `Integer`, Nullable=False (secuencia dentro del día).
  - `hora_llegada_estimada`: `Time`, Nullable=True.
  - `hora_salida_estimada`: `Time`, Nullable=True.
  - `tiempo_traslado_desde_anterior`: `Integer`, Nullable=True (en minutos).
  - `costo_entrada_bob`: `Numeric(10, 2)`, Nullable=True.
  - `clima_temperatura`: `Numeric(5, 2)`, Nullable=True.
  - `clima_lluvia_mm`: `Numeric(5, 2)`, Nullable=True.
  - `clima_descripcion`: `String(100)`, Nullable=True.
- **Relaciones:**
  - `itinerario`: `db.relationship('Itinerario', backref='detalles')`.
  - `atractivo`: `db.relationship('Atractivo', backref='detalles')`.
  - `transporte`: `db.relationship('Transporte', backref='detalles')`.
  - `traficos`: `db.relationship('ItinerarioDetalleTrafico', backref='itinerario_detalle', cascade='all, delete-orphan')`.

#### 14. `ViajeTurista` (Tabla: `viaje_turista`)
- **Propósito:** Asociación N:M entre itinerarios y turistas para soportar grupos de viaje (titular y acompañantes).
- **Campos:**
  - `id_viaje_turista`: `Integer`, Primary Key, autoincremental.
  - `id_itinerario`: `Integer`, Foreign Key (`itinerario.id_itinerario`), Nullable=False.
  - `id_turista`: `Integer`, Foreign Key (`turista.id_turista`), Nullable=False.
- **Restricciones:**
  - `UniqueConstraint('id_itinerario', 'id_turista', name='uq_viaje_turista_itinerario_turista')`.
- **Relaciones:**
  - `itinerario`: `db.relationship('Itinerario', backref='viajes_turistas')`.
  - `turista`: `db.relationship('Turista', backref='viajes')`.

#### 15. `ItinerarioDetalleTrafico` (Tabla: `itinerario_detalle_trafico`)
- **Propósito:** Registro de las alertas y zonas de tráfico que impactaron en el tramo de una parada.
- **Campos:**
  - `id_detalle`: `Integer`, Foreign Key (`itinerario_detalle.id_detalle`), Primary Key.
  - `id_patron`: `Integer`, Foreign Key (`patron_trafico.id_patron`), Primary Key.
- **Relaciones:**
  - `itinerario_detalle`: `db.relationship('ItinerarioDetalle', backref='traficos')`.
  - `patron_trafico`: `db.relationship('PatronTrafico', backref='detalles_trafico')`.

#### 16. `TipoCambio` (Tabla: `tipo_cambio`)
- **Propósito:** Historial de cotizaciones oficiales de compra y venta del dólar estadounidense (BOB/USD).
- **Campos:**
  - `id_tipo_cambio`: `Integer`, Primary Key, autoincremental.
  - `fecha`: `DateTime`, Nullable=False, Default=`datetime.utcnow`.
  - `valor_compra`: `Numeric(10, 4)`, Nullable=False.
  - `valor_venta`: `Numeric(10, 4)`, Nullable=False.
  - `fuente`: `String(20)`, Nullable=False, Default=`'api'` (`'api'` o `'manual'`).
  - `id_usuario`: `Integer`, Foreign Key (`usuario.id_usuario`), Nullable=True.
- **Relaciones:**
  - `usuario`: `db.relationship('Usuario', backref='tipos_cambio')`.

#### 17. `ConsultaNSGA2` (Tabla: `consulta_nsga2`)
- **Propósito:** Almacén de métricas analíticas, parámetros de ejecución y memoria caché de soluciones del algoritmo.
- **Campos:**
  - `id_consulta`: `Integer`, Primary Key, autoincremental.
  - `fecha`: `DateTime`, Nullable=False, Default=`datetime.utcnow`.
  - `id_generacion`: `Integer`, Foreign Key (`generacion.id_generacion`), Nullable=True.
  - `num_atractivos`: `Integer`, Nullable=False.
  - `num_transportes`: `Integer`, Nullable=False.
  - `presupuesto`: `Numeric(10, 2)`, Nullable=False.
  - `tiempo_disponible_horas`: `Numeric(5, 2)`, Nullable=False.
  - `intereses`: `Text`, Nullable=True.
  - `tamano_poblacion`: `Integer`, Nullable=False.
  - `generaciones`: `Integer`, Nullable=False.
  - `prob_cruce`: `Numeric(4, 2)`, Nullable=False.
  - `prob_mutacion`: `Numeric(4, 2)`, Nullable=False.
  - `num_soluciones`: `Integer`, Nullable=False.
  - `mejor_afinidad`: `Numeric(5, 4)`, Nullable=True.
  - `mejor_tiempo`: `Numeric(10, 2)`, Nullable=True.
  - `soluciones_viables`: `Integer`, Nullable=False.
  - `todas_exceden`: `Boolean`, Nullable=False, Default=False.
  - `tiempo_ejecucion_seg`: `Numeric(6, 2)`, Nullable=True.
  - `convergencia`: `Numeric(5, 4)`, Nullable=True.
  - `diversidad_final`: `Numeric(5, 4)`, Nullable=True.
  - `fecha_inicio_viaje`: `Date`, Nullable=True.
  - `fecha_fin_viaje`: `Date`, Nullable=True.
  - `hora_inicio_dia`: `Time`, Nullable=True.
  - `hora_fin_dia`: `Time`, Nullable=True.
  - `auto_rango_paradas`: `Boolean`, Nullable=False, Default=True.
  - `min_paradas`: `Integer`, Nullable=True.
  - `max_paradas`: `Integer`, Nullable=True.
  - `usar_clima`: `Boolean`, Nullable=False, Default=True.
  - `atractivos_ids_json`: `Text`, Nullable=True.
  - `transporte_ids_json`: `Text`, Nullable=True.
  - `hubo_soluciones_viables`: `Boolean`, Nullable=False, Default=True.
  - `hash_parametros`: `String(64)`, Nullable=True (SHA-256 para búsqueda en caché).
  - `resultados_json`: `Text`, Nullable=True (payload serializado de soluciones para respuesta en 0 segundos).
- **Relaciones:**
  - `generacion`: `db.relationship('Generacion', backref='consultas_nsga2')`.

#### 18. `DistanciaAtractivo` (Tabla: `distancia_atractivo`)
- **Propósito:** Matriz geodésica y vial precalculada para evitar peticiones en caliente a servicios externos de ruteo.
- **Campos:**
  - `id_distancia`: `Integer`, Primary Key, autoincremental.
  - `id_atractivo_origen`: `Integer`, Foreign Key (`atractivo.id_atractivo`), Nullable=False.
  - `id_atractivo_destino`: `Integer`, Foreign Key (`atractivo.id_atractivo`), Nullable=False.
  - `distancia_km`: `Numeric(8, 3)`, Nullable=False.
  - `duracion_min`: `Numeric(6, 2)`, Nullable=False.
  - `polyline_coords`: `Text`, Nullable=True (JSON array con pares `[[lat, lon], ...]`).
  - `fuente`: `String(20)`, Nullable=False, Default=`'osrm'` (`'osrm'` o `'manual'`).
  - `fecha_calculo`: `DateTime`, Nullable=False, Default=`datetime.utcnow`.
- **Restricciones:**
  - `UniqueConstraint('id_atractivo_origen', 'id_atractivo_destino', name='uq_distancia_origen_destino')`.
- **Relaciones:**
  - `atractivo_origen`: `db.relationship('Atractivo', foreign_keys=[id_atractivo_origen], backref='distancias_salida')`.
  - `atractivo_destino`: `db.relationship('Atractivo', foreign_keys=[id_atractivo_destino], backref='distancias_llegada')`.

#### 19. `ArchivoPareto` (Tabla: `archivo_pareto`)
- **Propósito:** Archivo acumulativo de soluciones de Pareto no dominadas para el cálculo de métricas de calidad de optimización (Generational Distance y Spacing).
- **Campos:**
  - `id_archivo`: `Integer`, Primary Key, autoincremental.
  - `hash_problema`: `String(64)`, Nullable=False, Unique=True, Index=True.
  - `ref_point_json`: `Text`, Nullable=False (vector del punto de referencia para Hipervolumen).
  - `valores_json`: `Text`, Nullable=False (matriz JSON de frentes acumulados).
  - `num_puntos`: `Integer`, Nullable=False, Default=0.
  - `fecha_actualizacion`: `DateTime`, Nullable=False, Default=`datetime.utcnow`, OnUpdate=`datetime.utcnow`.

---

### 2.2. Patrón de Eliminación Lógica (Soft Delete)
El sistema implementa de forma consistente el patrón **Soft Delete** a través de la columna:
```python
deleted_at = db.Column(db.DateTime, nullable=True, default=None)
```
- **Modelos que lo implementan:** `Usuario`, `Categoria`, `Subcategoria`, `Proveedor`, `Transporte`, `Atractivo`, `ZonaTrafico`, `PatronTrafico`, `Itinerario`.
- **Mecánica Operativa:**
  - Cuando se solicita una eliminación, el registro no se destruye con `DELETE FROM`. En su lugar, el servicio ejecuta:
    ```python
    entidad.deleted_at = datetime.utcnow()
    db.session.commit()
    ```
  - Cada modelo cuenta con la propiedad calculada `@property def is_deleted(self): return self.deleted_at is not None`.
  - En `Usuario`, la integración con Flask-Login valida la propiedad `is_active`:
    ```python
    @property
    def is_active(self):
        return self.deleted_at is None
    ```
    Esto garantiza que si un usuario es dado de baja, sus cookies o sesiones activas quedan invalidadas de inmediato.
  - Las consultas del catálogo, del generador NSGA-II y de los dashboards filtran sistemáticamente `Model.deleted_at.is_(None)`, asegurando la integridad referencial histórica en itinerarios ya guardados.
  - Existe soporte de **Restauración (`restaurar_entidad`)**, permitiendo al Administrador revertir bajas lógicas estableciendo `deleted_at = None`.

---

## 3. Capa de Negocio (Servicios)

La capa de servicios (`app/services/`) desacopla la lógica de optimización, matemáticas y persistencia del ciclo de petición HTTP.

### 3.1. Catálogo de Servicios y Funcionalidades Principales

| Archivo de Servicio | Funciones Principales | Resumen de Lógica de Negocio |
| :--- | :--- | :--- |
| `nsga2_service.py` | `ejecutar_nsga2`, `ItinerarioVariableProblem`, `SamplerDiversificado`, `MutacionCompuesta`, `detectar_trafico_tramo`, `evaluar_capacidad_transporte`, `asignar_transporte_tramo` | Núcleo matemático de optimización multiobjetivo con Pymoo. Decodificación de cromosomas, evaluación de funciones objetivo (afinidad y tiempo), simulación de congestión con Shapely y ventanas horarias multi-día. |
| `itinerario_service.py` | `generar_itinerarios`, `preparar_datos_nsga2`, `guardar_itinerario`, `listar_itinerarios_guardados`, `obtener_detalle_itinerario`, `buscar_turista`, `agregar_acompanante`, `calcular_faltantes` | Orquestador de optimización. Manejo de caché SHA-256 (24h), rate limiting (3s), persistencia con snapshot inmutable en JSON, vinculación de titulares y control de cupos de acompañantes. |
| `metricas_pareto_service.py` | `calcular_y_actualizar_metricas_pareto`, `calcular_hash_problema`, `_filtrar_no_dominados` | Cálculo de indicadores de calidad del frente de Pareto: Hipervolumen (HV), Generational Distance (GD) y Spread/Spacing, manteniendo un archivo histórico de referencia no dominado en BD. |
| `weather_service.py` | `consultar_clima`, `asignar_zona_clima`, `clasificar_wmo`, `_clasificar_hora`, `obtener_clima_parada` | Consulta la API de Open-Meteo para las 4 zonas climáticas de La Paz. Clasifica condiciones en bueno/moderado/adverso según umbrales de lluvia, viento y visibilidad; pre-filtra atractivos sensibles. |
| `distance_service.py` | `obtener_distancia`, `consultar_osrm`, `precalcular_matriz_completa` | Acceso a la matriz de distancias precalculada en BD. Garantiza cero llamadas a OSRM durante la generación de itinerarios para máxima velocidad. |
| `routing_service.py` | `obtener_ruta_real` | Wrapper de enrutamiento con caché intra-proceso en memoria (`_ROUTING_CACHE`) para distancias y polylines geoespaciales por calles. |
| `exchange_service.py` | `obtener_tc_actual`, `obtener_tc_oficial`, `convertir_bs_a_usd`, `obtener_tc_api`, `guardar_tc_desde_api`, `guardar_tc_manual` | Consulta el tipo de cambio del Banco Central de Bolivia (BCB) con caché de 1 hora. Aplica jerarquía de fallback: API -> BD -> Valores oficiales por defecto (6.96 / 7.06). |
| `email_service.py` | `enviar_correo`, `enviar_bienvenida`, `enviar_credenciales_temporales`, `enviar_reset_password_link` | Despacho de correos HTML responsivos en segundo plano mediante hilos (`Thread(daemon=True)`) para evitar latencias en la interfaz. |
| `auth_service.py` | `register_user`, `validate_user_login`, `generate_2fa_setup`, `verify_totp_code`, `validate_password_strength`, `generate_random_password` | Validación de fortaleza de contraseñas (8 caracteres turista, 12 agentes/admin), generación de secretos TOTP y códigos QR base64, autenticación en dos pasos. |
| `usuario_service.py` | `get_usuarios_paginados`, `get_total_estadisticas`, `create_user_by_admin`, `update_user_by_admin`, `soft_delete_user`, `restore_user`, `admin_reset_password` | CRUD administrativo de usuarios, generación de contraseñas temporales con expiración a 24 horas y filtros avanzados. |
| `atractivo_service.py` | `listar_atractivos`, `obtener_atractivo`, `crear_atractivo`, `actualizar_atractivo`, `eliminar_atractivo`, `guardar_imagen_atractivo`, `get_estadisticas_atractivos` | Gestión de atractivos turísticos, procesamiento y optimización de imágenes con Pillow (máx 1200px) y control de edición restringida para agentes. |
| `transporte_service.py` | `listar_transportes`, `obtener_transporte`, `crear_transporte`, `actualizar_transporte`, `eliminar_transporte`, `get_estadisticas_transportes` | Catálogo de transportes con validación de tipo de costo (`por_dia` / `por_persona`) y capacidades de vehículos. |
| `categoria_service.py` | `listar_categorias`, `obtener_todas_activas`, `crear_categoria`, `actualizar_categoria`, `eliminar_categoria`, `restaurar_categoria` | Gestión de categorías con validación de unicidad y control de dependencias. |
| `subcategoria_service.py` | `listar_subcategorias`, `obtener_todas_activas`, `crear_subcategoria`, `actualizar_subcategoria`, `eliminar_subcategoria`, `restaurar_subcategoria` | Gestión de subcategorías vinculadas a categorías maestras. |
| `proveedor_service.py` | `listar_proveedores`, `obtener_todos_activos`, `crear_proveedor`, `actualizar_proveedor`, `eliminar_proveedor`, `restaurar_proveedor` | Gestión de operadores de servicios turísticos y tarifas especiales. |
| `reporte_service.py` | `obtener_metricas_negocio`, `obtener_metricas_algoritmo` | Agregaciones estadísticas en SQL para el dashboard ejecutivo, KPIs de viabilidad, top 10 atractivos y series temporales. |

---

### 3.2. Implementación Detallada del Algoritmo NSGA-II (`nsga2_service.py`)

El sistema implementa el algoritmo genético **NSGA-II (Non-dominated Sorting Genetic Algorithm II)** adaptado a la optimización combinatoria de rutas turísticas mediante la librería especializada `pymoo`:

1. **Estructura del Cromosoma (Genoma Mixto de Tamaño Variable):**
   - El individuo se representa mediante un vector de números reales continuos en el intervalo $[0.0, 1.0]$ de longitud $N + 1$, donde $N$ es el número total de atractivos candidatos:
     $$\vec{X} = [x_0, x_1, x_2, \dots, x_{N-1}, x_N]$$
   - **Parte 1 (Gen $x_N$):** Determina el número de paradas $K$ a visitar dentro del rango admisible $[K_{min}, K_{max}]$:
     $$K = \text{round}(K_{min} + x_N \cdot (K_{max} - K_{min}))$$
   - **Parte 2 (Genes $x_0 \dots x_{N-1}$):** Codificación por claves aleatorias (**Random Keys**). El orden relativo descendente de los valores reales determina la permutación completa de los atractivos mediante `np.argsort(-prioridades)`.
   - **Decodificación:** Se seleccionan únicamente los primeros $K$ atractivos resultantes de la permutación, respetando ese orden secuencial de visita.

2. **Funciones Objetivo:**
   El problema está planteado formalmente con 2 objetivos en conflicto (ambos formulados internamente como minimización):
   - **Función Objetivo 1 ($f_1$) — Maximizar Afinidad Turística:**
     - En modo $K$ libre, para balancear la cantidad de paradas sin penalizar rutas medianas:
       $$\text{afinidad} = \frac{\sum_{i=1}^{K} w_i}{\sqrt{K}}$$
       Normalizado a $[0, 1]$ con respecto a $\sqrt{K_{max}}$.
     - En modo $K$ fijo: normalizado contra la suma ideal de los $K$ atractivos con mayor peso configurado por el usuario.
     - Se transforma a minimización:
       $$f_1 = -\text{afinidad} + \text{Penalización}$$
   - **Función Objetivo 2 ($f_2$) — Minimizar Tiempo Total de Recorrido:**
     - Suma de tiempos de visita en atractivos más los tiempos reales de traslado por calles (con factor de tráfico aplicado):
       $$T_{total} = \sum_{i=1}^{K} T_{visita}(i) + \sum_{i=1}^{K-1} T_{traslado}(i, i+1)$$
     - Se normaliza contra la ventana horaria total disponible $T_{max\_ref}$:
       $$f_2 = \frac{T_{total}}{T_{max\_ref}} + \text{Penalización}$$

3. **Operadores Genéticos:**
   - **Muestreo Inicial (`SamplerDiversificado`):** Hereda de `FloatRandomSampling`. Garantiza que en la generación 0 la población cubra uniformemente todos los valores enteros de $K$ entre $K_{min}$ y $K_{max}$, evitando sesgos hacia rutas pequeñas o saturadas.
   - **Cruce (`SBX` - Simulated Binary Crossover):** Probabilidad de cruce $p_c = 0.85$, índice de distribución $\eta = 15$.
   - **Mutación Compuesta (`MutacionCompuesta`):** Hereda de `Mutation`. Aplica mutación polinomial (`Polynomial Mutation`, $p_m = 0.15$, $\eta = 20$) sobre las claves aleatorias continuas, y de forma acoplada ejecuta una mutación discreta sobre el gen $x_N$ sumando o restando una parada ($\pm 1$) con probabilidad de $0.15$.
   - **Preservación de Diversidad:** `eliminate_duplicates=True` para descartar genomas idénticos en cada generación.

4. **Restricciones y Penalizaciones:**
   - **Presupuesto Máximo:** La suma de entradas ($C_{entradas} \times \text{num\_personas}$) más tarifas de transporte no debe superar el presupuesto máximo.
   - **Ventana Horaria Diaria:** Las actividades deben iniciar y concluir dentro del rango diario establecido (por defecto 09:00 a 18:00, configurable entre 06:00 y 19:59).
   - **Días Cerrados y Horarios de Apertura/Cierre:** Se descartan o penalizan atractivos cuyos días cerrados coincidan con el día del viaje o cuya hora de visita caiga fuera de sus horarios de atención.
   - **Capacidad de Transporte:** Regla estricta con tolerancia de $+1$ pasajero (aviso de sobrecupo) o cálculo de múltiples vehículos (`ceil(num_personas / capacidad)`).
   - **Penalización Cuadrática/Lineal:** Si una solución excede el tiempo disponible o el presupuesto, se suma una penalización proporcional:
     $$\text{Penalización} = 3.0 \cdot \left(\frac{\text{exceso\_tiempo}}{60}\right) + 3.0 \cdot \left(\frac{\text{exceso\_costo}}{\text{presupuesto\_max}}\right)$$

5. **Cálculo de Tráfico y Clima:**
   - **Tráfico:** Se cargan zonas (`ZonaTrafico`) con geometría WKT y patrones (`PatronTrafico`). Mediante `shapely.geometry.LineString`, se evalúa si el tramo vectorial entre paradas intersecta algún polígono en la franja horaria correspondiente. Se aplica el factor de congestión más desfavorable ($1.0$ a $2.0$), multiplicando la duración base.
   - **Clima:** Pre-filtrado automático con Open-Meteo. Los atractivos marcados como `sensible_al_clima=True` se evalúan contra las horas de visita proyectadas. Si presentan lluvia intensa ($>3.0$ mm/h), tormenta eléctrica o ráfagas ($>60$ km/h), se excluyen antes del proceso de optimización para garantizar la seguridad del turista.

---

### 3.3. Mecanismo de Caché y Rate Limiting (`itinerario_service.py`)

Para garantizar alta escalabilidad, baja latencia y protección contra ataques de denegación de servicio (DoS) o ejecuciones redundantes:

1. **Huella Criptográfica SHA-256 (`hash_actual`):**
   - Antes de ejecutar el motor NSGA-II, el sistema construye un diccionario normalizado con todos los parámetros de entrada:
     - IDs ordenados de atractivos y transportes seleccionados.
     - Presupuesto máximo, número de personas, rango de paradas.
     - Fechas resueltas (fecha inicio calculada, número de días, horas diarias).
     - Diccionario de afinidad/sliders ordenado por clave.
     - Parámetros genéticos (población, generaciones, probabilidades).
   - Se serializa a cadena JSON con claves ordenadas (`json.dumps(payload_dict, sort_keys=True)`) y se computa su digestión:
     $$\text{Hash} = \text{SHA256}(\text{payload\_str})$$

2. **Caché con Expiración a 24 Horas:**
   - Se consulta en la tabla `ConsultaNSGA2` unida con `Generacion` filtrando por el `id_usuario` actual y el `hash_parametros`.
   - **Cache Hit (< 24 horas):** Si existe un registro previo con menos de 86,400 segundos de antigüedad, se deserializa `resultados_json` y se devuelve inmediatamente al usuario en menos de 50 milisegundos, suprimiendo la ejecución del algoritmo.
   - **Cache Expired (>= 24 horas):** Si pasaron más de 24 horas, la caché se invalida para actualizar pronósticos climáticos y tipos de cambio, ejecutando nuevamente NSGA-II.

3. **Rate Limiting por Usuario (3 Segundos):**
   - En peticiones con parámetros nuevos (Cache Miss), el servicio verifica la marca temporal de la última generación del usuario en la tabla `Generacion`.
   - Si la diferencia entre la hora actual y la última consulta es inferior a **3 segundos**, la petición es rechazada inmediatamente con un error controlado:
     ```python
     if segundos_desde_ultima < 3:
         raise ValueError("Por favor, espera unos segundos antes de volver a generar.")
     ```

---

## 4. Capa de Presentación (Controladores y Vistas)

### 4.1. Registro de Blueprints y Rutas del Sistema

A continuación se detalla la matriz de endpoints del sistema con sus métodos HTTP y restricciones de acceso:

| Blueprint | Prefijo | Endpoint / Ruta | Métodos | Control de Acceso / Decorador |
| :--- | :--- | :--- | :--- | :--- |
| `auth` | `/` | `/` | GET | Público (redirecciona a login o dashboard) |
| `auth` | `/` | `/dashboard` | GET | `@login_required` (despacha por rol) |
| `auth` | `/` | `/signup` | GET, POST | Público |
| `auth` | `/` | `/login` | GET, POST | Público |
| `auth` | `/` | `/verificar-2fa` | GET, POST | Sesión temporal pre-2FA |
| `auth` | `/` | `/configurar-2fa` | GET, POST | Usuario autenticado o sesión de configuración |
| `auth` | `/` | `/cambiar-password-obligatorio` | GET, POST | Cambio obligatorio por política |
| `auth` | `/` | `/forgot-password` | GET, POST | Público |
| `auth` | `/` | `/check-email` | GET | Público |
| `auth` | `/` | `/reset-password/<token>` | GET, POST | Público con validación de token temporal |
| `auth` | `/` | `/logout` | GET | `@login_required` |
| `admin` | `/admin` | `/dashboard` | GET | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/usuarios` | GET | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/usuarios/<id>` | GET | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/usuarios/crear` | GET, POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/usuarios/<id>/editar` | GET, POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/usuarios/<id>/eliminar` | POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/usuarios/<id>/restaurar` | POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/usuarios/<id>/reset-password` | POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/atractivos` | GET | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/atractivos/crear` | GET, POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/atractivos/<id>` | GET | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/atractivos/<id>/editar` | GET, POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/atractivos/<id>/eliminar` | POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/atractivos/<id>/restaurar` | POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/transportes` | GET | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/transportes/crear` | GET, POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/transportes/<id>` | GET | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/transportes/<id>/editar` | GET, POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/transportes/<id>/eliminar` | POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/transportes/<id>/restaurar` | POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/categorias` | GET | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/categorias/crear` | GET, POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/categorias/<id>/editar` | GET, POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/categorias/<id>/eliminar` | POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/categorias/<id>/restaurar` | POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/subcategorias` | GET | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/subcategorias/crear` | GET, POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/subcategorias/<id>/editar` | GET, POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/subcategorias/<id>/eliminar` | POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/subcategorias/<id>/restaurar` | POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/proveedores` | GET | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/proveedores/crear` | GET, POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/proveedores/<id>` | GET | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/proveedores/<id>/editar` | GET, POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/proveedores/<id>/eliminar` | POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/proveedores/<id>/restaurar` | POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/tipo-cambio` | GET | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/tipo-cambio/sincronizar` | POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/tipo-cambio/manual` | POST | `@login_required`, `@admin_required` |
| `admin` | `/admin` | `/tipo-cambio/<id>/eliminar` | POST | `@login_required`, `@admin_required` |
| `agente` | `/agente` | `/dashboard` | GET | `@login_required`, `@agente_required` |
| `agente` | `/agente` | `/perfil` | GET | `@login_required`, `@agente_required` |
| `agente` | `/agente` | `/atractivos/<id>/editar` | GET, POST | `@login_required`, `@agente_required` (edición parcial operativa) |
| `agente` | `/agente` | `/transportes/<id>/editar` | GET, POST | `@login_required`, `@agente_required` (edición parcial operativa) |
| `turista` | `/turista` | `/dashboard` | GET | `@login_required`, `@turista_required` |
| `turista` | `/turista` | `/perfil` | GET, POST | `@login_required`, `@turista_required` |
| `turista` | `/turista` | `/desactivar-2fa` | POST | `@login_required`, `@turista_required` |
| `catalogo` | `/catalogo` | `/atractivos` | GET | `@login_required` (todos los roles) |
| `catalogo` | `/catalogo` | `/atractivos/<id>` | GET | `@login_required` (vista adaptada al rol) |
| `catalogo` | `/catalogo` | `/atractivos/mapa` | GET | `@login_required` (mapa general con Leaflet) |
| `catalogo` | `/catalogo` | `/atractivos/<id>/mapa` | GET | `@login_required` (mapa focalizado) |
| `catalogo` | `/catalogo` | `/transportes` | GET | `@login_required` |
| `catalogo` | `/catalogo` | `/transportes/<id>` | GET | `@login_required` |
| `itinerarios`| `/itinerarios`| `/generar` | GET | `@login_required`, `@role_required('admin')` (Vista generador) |
| `itinerarios`| `/itinerarios`| `/generar` | POST | `@login_required`, `@role_required('admin')` (Ejecución NSGA-II API) |
| `itinerarios`| `/itinerarios`| `/guardar` | POST | `@login_required` (Guardado de solución) |
| `itinerarios`| `/itinerarios`| `/lista` | GET | `@login_required` (Lista filtrada por rol) |
| `itinerarios`| `/itinerarios`| `/<id>` | GET | `@login_required` (Detalle visual de itinerario) |
| `itinerarios`| `/itinerarios`| `/<id>/acompanantes` | POST | `@login_required` (Registro de acompañante) |
| `itinerarios`| `/itinerarios`| `/<id>/turistas` | GET | `@login_required` (Conteo y lista de turistas) |
| `turistas_api`| `/turistas` | `/buscar` | GET | `@login_required` (Autocompletado de turista) |
| `reportes` | `/reportes` | `/dashboard` | GET | `@login_required` |
| `reportes` | `/reportes` | `/exportar/csv` | GET | `@login_required` |
| `reportes` | `/reportes` | `/exportar/pdf` | GET | `@login_required` |

---

### 4.2. Templates Principales y Librerías Frontend
1. **Plantilla Maestra (`app/templates/base.html`):**
   - Estructura responsiva con barra lateral oscura colapsable en pantallas móviles mediante overlay backdrop.
   - Tipografía moderna: Google Fonts (`Playfair Display` para encabezados y `Plus Jakarta Sans` para cuerpo).
   - Componentes de interfaz: **Bootstrap 5.3.3** y **Bootstrap Icons 1.11.3**.
2. **Visualización Geoespacial e Interactiva:**
   - **Leaflet 1.9.4:** Renderizado de mapas sobre capas vectoriales de OpenStreetMap.
   - **Leaflet PolylineDecorator (v1.6.0):** Dibujado de flechas direccionales sobre las rutas de las calles para indicar el sentido de circulación del tour.
   - **Leaflet PolylineOffset (v1.1.1):** Separación visual de trazos compartidos de ida y vuelta para evitar superposición de líneas en tramos bidireccionales.
   - Marcadores numéricos personalizados con HTML/CSS (`divIcon`) que reflejan el orden cronológico de las paradas.
3. **Analítica y Gráficos Frontend:**
   - **Chart.js:** Renderizado de gráficos dinámicos en el generador:
     - Frente de Pareto interactivo ($f_1$ vs $f_2$).
     - Curva de convergencia generacional (evolución de la mejor afinidad).
     - Historial de diversidad poblacional a lo largo de las generaciones.

---

### 4.3. Lógica Clave de JavaScript

1. **Persistencia en `localStorage` del Estado del Generador:**
   - En `itinerarios/generar.html`, los datos del formulario y los últimos resultados calculados se sincronizan en el navegador bajo las claves `buhos_form_state_v1` y `buhos_results_state_v1`.
   - Permite que el usuario navegue a otras secciones o refresque la pantalla sin perder el frente de Pareto obtenido ni la configuración de sliders.
   - Botón de **Reinicio Seguro** con confirmación modal (`#modalConfirmarReinicio`) para limpiar la memoria local y reestablecer valores por defecto.
2. **Renderizado de Mapas y Modales:**
   - Inicialización perezosa de mapas Leaflet dentro del modal de detalle de solución (`#modalDetalleItinerario`), ejecutando `mapaActual.invalidateSize()` en el evento `shown.bs.modal` para evitar tiles desalineados.
   - Capas agrupadas por día (`capasPorDia`) con controles de visibilidad para itinerarios multi-día.
   - Muestra de avisos viales contextuales (popups de tráfico con colorimetría verde, amarilla, naranja y roja).
3. **Validaciones Asíncronas y Autocompletado:**
   - En `itinerario_acompanantes.js`, la salida de foco (`blur`) en los campos de documento y procedencia dispara una consulta `fetch('/turistas/buscar')`.
   - Si el turista ya existe, autocompleta nombres, apellidos, teléfono y correo electrónico.
   - Si existe conflicto de procedencia (un documento registrado previamente bajo otro país), alerta al operador para prevenir suplantación o inconsistencia de identidad.
   - Validación estricta con expresiones regulares antes del envío (solo letras en nombres, formato alfanumérico en documentos).

---

## 5. Integraciones Externas

El sistema integra cuatro servicios externos esenciales para su funcionamiento autónomo:

### 5.1. OSRM (Open Source Routing Machine)
- **Endpoint Base:** `https://router.project-osrm.org/route/v1/driving`
- **Propósito:** Cálculo de trayectorias reales sobre la red de calles de La Paz, distancias exactas en kilómetros, duraciones en minutos y geometría vectorial en formato GeoJSON (`overview=full&geometries=geojson`).
- **Mecanismo de Desacople:**
  - El sistema no consulta OSRM en tiempo de ejecución del algoritmo genético.
  - Se ejecuta previamente el comando CLI `flask precalcular-distancias` mediante `distance_service.precalcular_matriz_completa()`.
  - La matriz completa de distancias y polilíneas se almacena en la tabla `DistanciaAtractivo`.
  - En caso de un trayecto invertido no calculado, el sistema invierte automáticamente el polyline guardado (`coords[::-1]`) aplicando simetría vial sin peticiones HTTP externas.

### 5.2. Open-Meteo API
- **Endpoint Base:** `https://api.open-meteo.com/v1/forecast`
- **Propósito:** Obtención de pronósticos meteorológicos horarios de alta resolución (temperatura a 2m, precipitación en mm, códigos de tiempo WMO, velocidad y ráfagas de viento, visibilidad y humedad relativa).
- **Zonificación Climática de La Paz:**
  Debido a la topografía accidentada y diferencias de altitud (3,200 a 4,000 msnm), el servicio divide la ciudad en 4 nodos de pronóstico:
  - **Centro:** $(-16.4988, -68.1282)$
  - **Pura Pura:** $(-16.4599, -68.1490)$
  - **Zona Sur:** $(-16.5276, -68.0759)$
  - **Mallasa:** $(-16.5736, -68.0592)$
- **Clasificación de Estados en 3 Niveles:**
  - **Bueno:** Condiciones estables para visitas turísticas al aire libre.
  - **Moderado:** Precipitación $\ge 0.1$ mm/h, ráfagas $> 40$ km/h o visibilidad $< 2000$ m (genera avisos informativos pero no excluye la parada).
  - **Adverso:** Precipitación $> 3.0$ mm/h, ráfagas $> 60$ km/h, visibilidad $< 500$ m o códigos WMO severos (tormenta eléctrica $95, 96, 97, 99$, lluvia intensa $65, 82$). Excluye preventivamente atractivos sensibles.
- **Caché:** Caché en memoria `_CACHE_CLIMA` con TTL de 3,600 segundos (1 hora).

### 5.3. Banco Central de Bolivia (API BCB)
- **Endpoint Oficial:** `https://apibcb.cucu.bo/api/v1/tc/oficial`
- **Propósito:** Consulta en tiempo real de las cotizaciones oficiales de compra y venta del dólar estadounidense emitidas por el Banco Central de Bolivia.
- **Jerarquía de Fallback (Alta Disponibilidad):**
  1. Consulta a la API REST del BCB (con timeout de 4s y caché en memoria con TTL de 1 hora).
  2. Si la API no responde o da error, busca el último registro persistido en la tabla `TipoCambio` de la base de datos.
  3. Si la base de datos está vacía, recurre a los valores oficiales estables fijados por normativa (Compra: 6.96 BOB, Venta: 7.06 BOB).
- **Sincronización:** El Administrador puede forzar la sincronización y persistencia manual desde el panel `/admin/tipo-cambio`.

### 5.4. Flask-Mail (Notificaciones Transaccionales)
- **Servidor:** Google Workspace / Gmail SMTP (`smtp.gmail.com:587` vía STARTTLS).
- **Lógica de Envío:**
  - Envío desacoplado mediante hilos daemon (`threading.Thread(target=_enviar_async, daemon=True)`), evitando bloqueos en el hilo principal de Flask.
  - Notificaciones operativas:
    1. **Bienvenida al Turista:** Al completar el registro público.
    2. **Credenciales Temporales para Agentes/Admins:** Al ser dados de alta por el Administrador con contraseña provisional aleatoria.
    3. **Recuperación de Contraseña:** Generación de enlaces con tokens criptográficos de autoservicio válidos por tiempo limitado.

---

## 6. Seguridad y Validaciones

### 6.1. Autenticación y Autorización
1. **Flask-Login y Ciclo de Sesión:**
   - Control de sesiones seguras mediante cookies de sesión HTTP-only.
   - Método `get_id` y deserialización de usuarios con protección contra inyecciones.
2. **Autenticación en Dos Factores (2FA TOTP):**
   - Estándar RFC 6238 implementado con la librería `pyotp`.
   - Secretos base32 únicos generados criptográficamente.
   - Códigos QR generados directamente en memoria con `qrcode` y transmitidos en Base64.
   - Ventana de tolerancia temporal `valid_window=1` para compensar desincronizaciones de hasta $\pm 30$ segundos en dispositivos móviles.
   - **Política de 2FA Obligatorio:** Los usuarios con rol `admin` y `agente` tienen la obligación ineludible de configurar 2FA para operar en la plataforma.
3. **Control de Acceso Basado en Roles (RBAC):**
   - Decorador principal `@role_required(*roles)` ubicado en `app/utils/decorators.py`.
   - Decoradores derivados: `@admin_required`, `@agente_required`, `@turista_required`.
   - Si un usuario autenticado intenta ingresar a un recurso no permitido, el sistema aborta con código HTTP `403 Forbidden` y mensaje descriptivo.

### 6.2. Políticas de Contraseñas
- **Turistas (Público):** Mínimo 8 caracteres, al menos 1 mayúscula, 1 minúscula, 1 número y 1 símbolo especial.
- **Agentes y Administradores:** Mínimo 12 caracteres, cumpliendo la misma matriz de complejidad.
- **Contraseñas Temporales:** Generadas mediante `secrets.choice` con longitud de 14 caracteres alfanuméricos y símbolos, marcadas con `must_change_password=True` y vencimiento estricto a las 24 horas.

### 6.3. Validaciones de Integridad
1. **Nivel Backend:**
   - Validación del payload JSON en el generador: verificación de límites de paradas ($K_{min} \le K_{max}$), presupuesto positivo ($> 0$), número de días ($1 \le \text{días} \le 14$) y horario dentro del marco permitido (06:00 a 19:59).
   - Bloqueo en backend contra el guardado de itinerarios inviables (`es_viable == False`).
   - Control de unicidad de documentos y detección de inconsistencias en la procedencia de turistas.
   - Transacciones atómicas de base de datos con sentencias `db.session.rollback()` en todos los bloques `try...except`.
2. **Nivel Frontend:**
   - Validación de formularios HTML5 con atributos `pattern`, `required` y mensajes de error específicos en modales.
   - Bloqueo de botones con estados de carga (spinners) durante peticiones asíncronas para evitar doble clic o reenvíos accidentales.

---

## 7. Funcionalidades Clave Implementadas (Resumen Ejecutivo)

El sistema desarrollado para **Buhos Tours** constituye una solución integral de optimización e ingeniería de software turístico, habiendo alcanzado los siguientes hitos operativos y funcionales:

1. **Motor de Optimización Multiobjetivo (NSGA-II Puro y Calibrado):**
   - Resolución automática de rutas Pareto-óptimas equilibrando afinidad turística y tiempos mínimos de traslado.
   - Rango dinámico y flexible de paradas por viaje.
   - Simulación geoespacial de tráfico real por zonas y franjas horarias con geometrías WKT.
   - Sensibilidad climática contextual para protección del turista ante eventos meteorológicos severos.
2. **Módulo de Caché y Deduplicación Inteligente:**
   - Respuesta instantánea en menos de 50 ms para consultas previamente ejecutadas mediante hash SHA-256.
   - Rate limiting integrado para protección de recursos del servidor.
3. **Gestión Completa de Usuarios y Seguridad Empresarial:**
   - Arquitectura RBAC para Administradores, Agentes y Turistas.
   - Doble factor de autenticación obligatorio para personal operativo.
   - Auditoría de bajas lógicas mediante Soft Delete.
4. **Catálogo Maestro y Panel Administrativo (CRUD):**
   - Mantenimiento centralizado de atractivos, transportes, categorías, subcategorías y proveedores.
   - Procesamiento y redimensionamiento automático de imágenes con Pillow.
   - Edición operativa delegada con permisos restringidos para agentes comerciales.
5. **Formalización y Guardado de Itinerarios con Snapshot Inmutable:**
   - Almacenamiento fiel en JSON de la solución elegida para garantizar que cambios futuros en el catálogo no alteren itinerarios confirmados.
   - Asignación de código único de confirmación UUIDv4.
   - Gestión integral de grupos de turistas: titular de reserva y registro de múltiples acompañantes con validación de capacidad de transporte.
6. **Módulo de Analítica y Reportería Ejecutiva:**
   - Dashboard con métricas de negocio (volumen de itinerarios, presupuestos medios, viabilidad).
   - Métricas académicas de investigación operativa: Hipervolumen (HV), Generational Distance (GD) y Spacing.
   - Exportación de reportes tabulares en formato CSV.
   - Generación de reportes corporativos formales en PDF mediante ReportLab Platypus con gráficos estadísticos embebidos de Matplotlib.
7. **Visualización Geográfica Avanzada:**
   - Integración con Leaflet para navegación interactiva día por día.
   - Trazado de flechas direccionales y compensación de líneas compartidas para una lectura visual clara de los circuitos urbanos.
