# ChordFlow Backend - SOP (Standard Operating Procedure)

## 1. Visión General
Este documento es la Fuente de la Verdad para el backend de ChordFlow (API REST). Define las reglas de arquitectura, diseño de base de datos y flujos de trabajo para los scripts en `src/`.

## 2. Objetivos del Sistema
- Proveer una API REST para gestionar canciones (partituras en formato `.chordflow`).
- Servir como backend para sincronización (offline-first con SQLite/PostgreSQL).
- Mantener la estructura modular y determinista.

## 3. Estructura de Base de Datos (Relacional)
El modelo sigue esta jerarquía:
- **Song**: Título, artista, BPM, key, metadatos generales.
- **Section**: Partes de la canción (Intro, Verso, etc.). Pertenece a una `Song`.
- **Line**: Líneas dentro de una sección (lyric, tab, chord_only). Pertenece a una `Section`.
- **ChordMarker**: Acordes asociados a una línea específica. Pertenece a una `Line`.
- **TabLine**: Representación de tablaturas de guitarra asociadas a una `Line`.

**Nota de Diseño:** Los campos complejos como `display_hint`, `finger_diagram`, y `fret_sequence` se almacenan en columnas de tipo `JSON`.

## 4. Estructura de la API
Los endpoints principales (Fase 1) están en `/songs`:
- `GET /songs` -> Lista de canciones.
- `POST /songs` -> Crear canción (acepta un payload con secciones, líneas y acordes anidados).
- `GET /songs/{id}` -> Detalles completos de la canción (con anidamiento).
- `PUT /songs/{id}` -> Actualizar canción completa.
- `DELETE /songs/{id}` -> Borrado de la canción (idealmente soft delete, pero para la Fase 1 puede ser hard delete).

## 5. Reglas y Restricciones (El "Protocolo")
- **Modularidad:** Mantener el código en `src/api` (endpoints), `src/services` (lógica y BD).
- **Manejo de Errores:** Todos los errores HTTP devuelven un código estándar (404, 400, 500) y usan Pydantic para validación.
- **Logging:** Todo el tráfico y errores deben registrarse usando la librería `logging` de Python en un archivo local (p. ej. `logs/app.log`). NUNCA usar solo `print()`.
- **Secretos:** Toda credencial o configuración (ej. DB URL) va en el archivo `.env`.

## 6. Casos Borde y Trampas Conocidas (Registro de Aprendizaje)
*(Esta sección se actualizará si fallan los scripts durante el desarrollo)*
- TBD
