# ChordFlow Frontend - SOP (Standard Operating Procedure)

## 1. Visión General
Define las reglas para la construcción de la interfaz web y el motor de sincronización. El objetivo es una experiencia fluida de lectura de partituras.

## 2. Principios de Diseño (UI/UX)
- **Modo Escuro Nativo:** Fondo oscuro (#0a0a0a) con acentos vibrantes (Teal #00f2ff).
- **Glassmorphism:** Los paneles de control deben usar `backdrop-filter: blur()` y fondos semi-transparentes.
- **Tipografía:** Usar fuentes limpias y sans-serif (Inter/Roboto). Los acordes deben destacar con negrita.
- **Respuesta Visual:** El acorde activo debe tener un escalado suave (1.05x) y un brillo sutil.

## 3. SyncEngine (Lógica Pura)
- **Independencia:** El código en `sync_engine.js` no debe conocer el DOM. Se comunica mediante callbacks o eventos.
- **Precisión:** Utilizar `requestAnimationFrame` para el bucle de sincronización.
- **Estado:** Debe manejar `currentBeat` basado en el tiempo transcurrido y el BPM actual.

## 4. Estructura de Archivos
- `index.html`: Estructura minimalista y semántica.
- `style.css`: Estilos modulares, uso de variables CSS.
- `sync_engine.js`: Clase `SyncEngine`.
- `app.js`: Lógica de orquestación (Fetch API -> Render -> Sync).

## 5. Reglas de Código JS
- Usar ES6+ (arrow functions, template literals).
- Todo el tráfico con la API debe tener manejo de errores (`try/catch`).
- Mantener funciones pequeñas y con una única responsabilidad.

## 6. Estándar de Parsing de Partituras (Alineación)
El sistema de importación de partituras usa el paradigma "Acordes sobre Letra" (formato estándar de Ultimate Guitar, LaCuerda.net, etc.).

**Reglas del Parser:**
- Una línea es "Línea de Acordes" si ≥60% de sus palabras son acordes válidos (regex: `^[A-G]([#b])?(m|maj|min|aug|dim|sus|add)?(\d)?(\/[A-G]([#b])?)?$`).
- Si una "Línea de Acordes" precede a una línea de letra, se crea un par: los acordes se vinculan a la letra en el mismo `char_position` de columna.
- Las líneas con formato `: F#m : C#7 :` se parsean como `chord_only` (Intro/Puente sin letra).
- Las líneas que terminan en `:` y tienen ≤4 palabras son marcadores de sección (ej: "Verso 1:").
- El `textarea` del editor DEBE usar fuente monoespaciada (`Roboto Mono`) para que la alineación visual sea correcta.
- **Trampa conocida:** El formato `[Acorde]Letra` antiguo es incompatible y fue abandonado en favor de este sistema.
