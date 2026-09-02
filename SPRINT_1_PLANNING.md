# 📋 Sprint Planning Meeting - Sprint 1

**Proyecto:** Sistema Web de Itinerarios Turísticos Personalizados (Buhos Tours)  
**Metodología:** SCRUM  
**Fecha de Planificación:** 02 de septiembre de 2026  
**Sprint:** 1  
**Duración:** 4 semanas (del 02/09 al 30/09)

---

## 🎯 Sprint Goal (Objetivo del Sprint)

> _"Establecer la base de datos relacional, el sistema de autenticación de agentes y el núcleo funcional del algoritmo NSGA-II, permitiendo que el sistema sea capaz de generar un itinerario turístico optimizado básico (aún sin interfaz gráfica) que considere horarios y restricciones de presupuesto."_

---

## 📋 Sprint Backlog (Tareas a desarrollar)

| #   | Tarea                                                                                                         | Prioridad | Estimación (Horas) |
| :-- | :------------------------------------------------------------------------------------------------------------ | :-------- | :----------------- |
| 1   | Implementación física de la base de datos en PostgreSQL (creación de tablas y relaciones)                     | Alta      | 8h                 |
| 2   | Desarrollo del módulo de autenticación y gestión de usuarios (login, roles admin/agente)                      | Alta      | 6h                 |
| 3   | Implementación del panel administrativo (CRUD para atractivos turísticos)                                     | Media     | 6h                 |
| 4   | Implementación del panel administrativo (CRUD para medios de transporte)                                      | Media     | 4h                 |
| 5   | Codificación del algoritmo NSGA-II (operadores de selección, cruce y mutación)                                | Alta      | 10h                |
| 6   | Definición e implementación de las funciones objetivo (Afinidad vs Tiempo de traslado)                        | Alta      | 6h                 |
| 7   | Implementación de restricciones operativas (horarios de apertura, disponibilidad de transporte y presupuesto) | Media     | 5h                 |
| 8   | Sprint Review 1 – Preparación de la presentación de avances                                                   | Alta      | 2h                 |

**Total de Horas Estimadas:** ~47 horas

---

## ✅ Definition of Done (Criterios de Aceptación)

Para que el Sprint 1 se considere **completado**, se deben cumplir los siguientes criterios:

- [ ] **Base de Datos:** PostgreSQL está corriendo y las tablas `usuario`, `atractivo`, `transporte`, `itinerario` y `detalle_itinerario` están creadas y migradas exitosamente.
- [ ] **Autenticación:** Un usuario puede registrarse e iniciar sesión. Los roles (`admin` y `agente`) restringen el acceso a las rutas del panel administrativo.
- [ ] **Panel CRUD:** El administrador puede agregar, editar, ver y eliminar atractivos turísticos y transportes desde la interfaz web.
- [ ] **Algoritmo NSGA-II:** El código en `services/nsga2_engine.py` es capaz de recibir una lista de atractivos y devolver un frente de Pareto (al menos 3 soluciones) utilizando operadores genéticos básicos.
- [ ] **Restricciones:** El algoritmo solo devuelve itinerarios que respeten los horarios de apertura y el presupuesto máximo del usuario (se prueba con datos de prueba en la terminal).
- [ ] **Pruebas unitarias:** Las funciones del NSGA-II pasan pruebas básicas de funcionamiento sin errores.
- [ ] **Código en GitHub:** Todos los cambios están subidos a la rama `develop` con mensajes de commit claros.

---

## 📌 Notas del Equipo (Solo desarrollador)

- Se trabajará con Python 3.10 y Flask.
- Las migraciones de la base de datos se manejarán con Flask-Migrate.
- El algoritmo NSGA-II se probará inicialmente en la terminal/consola antes de integrarlo al frontend.
