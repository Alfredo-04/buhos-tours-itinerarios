# 🗺️ Sistema Web de Itinerarios Turísticos Personalizados

![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3.x-green?logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-En%20Desarrollo-orange)

## 📖 Descripción del Proyecto

Sistema web de nivel empresarial diseñado para la planificación automatizada de itinerarios turísticos personalizados, aplicando el algoritmo genético multiobjetivo **NSGA-II**. El sistema optimiza los procesos de diseño de rutas para la **agencia de viajes Buhos Tours** en la ciudad de La Paz, Bolivia.

El núcleo matemático genera itinerarios optimizados que equilibran múltiples criterios en conflicto:

- **Afinidad:** Sincronización con perfiles específicos del turista (cultural, aventura, gastronomía, naturaleza, urbano).
- **Minimización:** Reducción del tiempo total de traslado entre atractivos turísticos.
- **Viabilidad operativa:** Respeto estricto de horarios de apertura, disponibilidad de transporte y presupuestos.

> **Impacto del Negocio:** Reduce el tiempo de planificación de 30-35 minutos por consulta a tan solo **5-10 minutos**, incrementando la capacidad de respuesta y la competitividad comercial.

---

## ⚙️ Características Principales

- **🔐 Autenticación y Control:** Acceso para agentes y administradores con roles diferenciados.
- **🏛️ Panel Administrativo (CRUD):** Gestión completa de atractivos turísticos y medios de transporte.
- **🧠 Motor Multiobjetivo (NSGA-II):** Generación de un frente de Pareto con múltiples opciones no dominadas.
- **🗺️ Visualización Dual:** Itinerarios estructurados en formato texto día por día y renderizados sobre mapas interactivos (**Leaflet + OpenStreetMap**).
- **🌦️ Filtrado Climático:** Integración con la API de **OpenWeatherMap** para exclusión automatizada de atractivos por condiciones adversas.
- **📊 Métricas y Reportes:** Almacenamiento de tiempos de ejecución y exportación de reportes internos en formatos **PDF** y **CSV**.

---

## 🛠️ Tecnologías Utilizadas

| Componente             | Tecnología                         | Versión       |
| :--------------------- | :--------------------------------- | :------------ |
| **Lenguaje**           | Python                             | 3.10 / 3.11   |
| **Framework Web**      | Flask                              | 2.3.x         |
| **Base de Datos**      | PostgreSQL                         | 16+           |
| **ORM / Migraciones**  | Flask-SQLAlchemy / Flask-Migrate   | 3.1.x / 4.0.x |
| **Autenticación**      | Flask-Login                        | 0.6.x         |
| **Cálculos (NSGA-II)** | NumPy                              | 1.26.x        |
| **Consumo de APIs**    | Requests                           | 2.31.x        |
| **Reportes (PDF/CSV)** | ReportLab / Pandas                 | 4.2.x / 2.2.x |
| **Frontend**           | HTML5, CSS3, JavaScript, Bootstrap | Moduled       |

---

## 🏗️ Arquitectura del Sistema

El sistema implementa una **Arquitectura Monolítica por Capas (Layered Architecture)** acoplada al patrón **MVC (Modelo-Vista-Controlador)** junto con una **Capa de Servicios (Service Layer)** para aislar el comportamiento del algoritmo genético.

```text
📁 buhos_tours/
├── 📁 app/                  # Núcleo de la aplicación
│   ├── 📁 models/           # (MVC - Modelo) Tablas y esquemas de base de datos.
│   ├── 📁 controllers/      # (MVC - Controlador) Rutas y lógica de peticiones endpoints.
│   ├── 📁 services/         # (Capa de Negocio) Algoritmos NSGA-II, consumo de APIs y reportes.
│   ├── 📁 templates/        # (MVC - Vista) Plantillas HTML renderizadas.
│   └── 📁 static/           # Archivos públicos estáticos (CSS, JS, imágenes).
├── 📁 migrations/           # Control de versiones de la base de datos (Flask-Migrate).
├── 📄 config.py             # Configuración del entorno de la aplicación.
├── 📄 .env                  # Variables de entorno críticas (excluido en producción).
├── 📄 requirements.txt      # Dependencias y librerías del proyecto.
├── 📄 run.py                # Punto de entrada para el servidor web.
└── 📄 .gitignore            # Archivos y directorios excluidos de Git.
```

---

## 📋 Requisitos Previos

Antes de configurar el proyecto localmente, asegúrate de tener instalado:

- **Python:** Versión 3.10 o 3.11.
- **PostgreSQL:** Versión 16 o superior (con pgAdmin para administración visual).
- **Git:** Para la gestión del código fuente.

---

## 🚀 Instalación y Configuración

Sigue estos pasos detallados para desplegar el entorno de desarrollo local:

### 1. Clonar el repositorio

```bash
git clone https://github.com/Alfredo-04/buhos-tours-itinerarios.git
cd buhos-tours-itinerarios
```

### 2. Crear y activar el entorno virtual

```bash
# Crear entorno aislado con Python 3.10
py -3.10 -m venv venv

# Activar el entorno (En Windows)
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea un archivo llamado `.env` en la raíz del proyecto con la siguiente estructura:

```env
SECRET_KEY=mi_clave_super_secreta_123
DATABASE_URL=postgresql://postgres:admin123@localhost:5432/buhos_db
OPENWEATHER_API_KEY=tu_api_key_aqui
```

> _Nota: Modifica las credenciales de `DATABASE_URL` de acuerdo a la configuración local de tu gestor de PostgreSQL._

### 5. Inicializar la Base de Datos

1. Abre pgAdmin o tu terminal de PostgreSQL y crea una base de datos limpia con el nombre `buhos_db`.
2. Corre las migraciones correspondientes para construir el esquema de tablas:

```bash
flask db init
flask db migrate -m "Inicialización de tablas"
flask db upgrade
```

### 6. Ejecutar el servidor de desarrollo

```bash
python run.py
```

El sistema se desplegará localmente en la dirección: **`http://localhost:5000`**

---

## 👨‍💻 Autores y Créditos Académicos

Este sistema se desarrolló formalmente como **Proyecto de Grado** para la **Universidad Privada del Valle (UNIVALLE)**, dentro de la Facultad de Informática y Electrónica para la carrera de Ingeniería de Sistemas Informáticos (Año 2026).

| Nombre                                 | Rol                                  | Contacto                                |
| :------------------------------------- | :----------------------------------- | :-------------------------------------- |
| **Alfredo Alejandro Cortez Fernandez** | Postulante / Desarrollador principal | [GitHub](https://github.com/Alfredo-04) |
| **Ing. Julio Cesar Irahola Flores**    | Tutor de Proyecto de Grado           | -                                       |

### 🙏 Agradecimientos

- A la agencia **Buhos Tours**, de manera especial a su gerente, **Sofia Isabella Castro Silva**, por proveer los accesos de información, requerimientos técnicos y el contexto operacional real del sector.
- A mi familia por el apoyo incondicional durante todo el proceso de formación académica y profesional.

---

## 📜 Licencia

Este proyecto se distribuye bajo los términos de la **Licencia MIT**. Puedes revisar el archivo `LICENSE` para mayores detalles normativos.
