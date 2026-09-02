# 🗺️ Sistema Web de Itinerarios Turísticos Personalizados

![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3.x-green?logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-En%20Desarrollo-orange)

> **Proyecto de Grado** – Universidad Privada del Valle (UNIVALLE)  
> **Carrera:** Ingeniería de Sistemas Informáticos  
> **Año:** 2026

---

## 📖 Descripción del Proyecto

El presente proyecto consiste en el desarrollo de un **sistema web de planificación de itinerarios turísticos personalizados**, aplicando el algoritmo genético multiobjetivo **NSGA-II**. El sistema está diseñado para optimizar el proceso de planificación en la **agencia de viajes Buhos Tours**, ubicada en la ciudad de La Paz, Bolivia.

El sistema permite a los agentes de viaje generar itinerarios optimizados que equilibran múltiples criterios en conflicto, tales como:

- **Afinidad** con los perfiles de interés del turista (cultural, aventura, gastronomía, naturaleza, urbano).
- **Minimización** del tiempo de traslado entre atractivos turísticos.
- **Viabilidad** operativa, respetando horarios de apertura, disponibilidad de transporte y presupuesto del turista.

El objetivo principal es **reducir el tiempo de planificación** de 30-35 minutos por consulta a tan solo 5-10 minutos, mejorando así la capacidad de respuesta y la competitividad de la agencia en el mercado turístico paceño.

---

## ⚙️ Características Principales

El sistema ofrece las siguientes funcionalidades clave:

- **🔐 Autenticación y Gestión de Usuarios:** Control de acceso para agentes y administradores con roles diferenciados.
- **🏛️ Panel Administrativo (CRUD):** Gestión completa de atractivos turísticos y medios de transporte disponibles.
- **🧠 Generación Multiobjetivo (NSGA-II):** Generación de un frente de Pareto con múltiples opciones de itinerario no dominadas, mostrando las compensaciones entre afinidad y tiempo.
- **🗺️ Visualización Dual:** Los itinerarios se presentan en formato texto (estructurado día por día) y sobre mapas interactivos (Leaflet + OpenStreetMap).
- **🌦️ Filtrado por Clima:** Integración con API meteorológica (OpenWeatherMap) para excluir atractivos afectados por condiciones climáticas adversas.
- **📊 Registro de Métricas y Reportes:** El sistema almacena tiempos de generación y permite la exportación de reportes internos en formatos PDF y CSV.
- **🔄 Optimización Continua:** Posibilidad de ajustar los parámetros del algoritmo (tamaño de población, generaciones) para mejorar el rendimiento.

---

## 🛠️ Tecnologías Utilizadas

| Componente             | Tecnología                                   | Versión            |
| :--------------------- | :------------------------------------------- | :----------------- |
| **Lenguaje**           | Python                                       | 3.10 (Recomendada) |
| **Framework Web**      | Flask                                        | 2.3.x              |
| **Base de Datos**      | PostgreSQL                                   | 16 / 17            |
| **ORM**                | Flask-SQLAlchemy                             | 3.1.x              |
| **Migraciones**        | Flask-Migrate                                | 4.0.x              |
| **Autenticación**      | Flask-Login                                  | 0.6.x              |
| **Cálculos (NSGA-II)** | NumPy                                        | 1.26.x             |
| **Consumo de APIs**    | Requests                                     | 2.31.x             |
| **Reportes (PDF)**     | ReportLab                                    | 4.2.x              |
| **Reportes (CSV)**     | Pandas                                       | 2.2.x              |
| **Frontend**           | HTML5, CSS3, JavaScript (Bootstrap, Leaflet) |

---

## 🏗️ Arquitectura del Sistema

El sistema sigue una **Arquitectura Monolítica por Capas (Layered Architecture)** combinada con el **patrón de diseño MVC (Modelo-Vista-Controlador)** y una **capa de servicios (Service Layer)** para aislar la lógica de negocio.

> **Justificación:** Esta arquitectura ha sido seleccionada por su simplicidad, adecuación al alcance del proyecto (una agencia pequeña, un solo desarrollador) y su capacidad de ser mantenible y escalable a futuro. La capa de servicios permite desacoplar el algoritmo NSGA-II de los controladores, facilitando las pruebas y la evolución del sistema.

```text
📁 buhos_tours/
├── 📁 app/                  # Núcleo de la aplicación
│   ├── 📁 models/           # (MVC - Modelo) Tablas de la base de datos.
│   ├── 📁 controllers/      # (MVC - Controlador) Rutas y lógica de peticiones.
│   ├── 📁 services/         # (Capa de Negocio) Algoritmos NSGA-II, APIs y reportes.
│   ├── 📁 templates/        # (MVC - Vista) Plantillas HTML.
│   └── 📁 static/           # Archivos públicos (CSS, JS, imágenes).
├── 📁 migrations/           # Control de versiones de la base de datos.
├── 📄 config.py             # Configuración de la aplicación.
├── 📄 .env                  # Variables de entorno (seguridad).
├── 📄 requirements.txt      # Dependencias del proyecto.
├── 📄 run.py                # Punto de entrada del servidor.
└── 📄 .gitignore            # Archivos excluidos del repositorio.
```
