# GUÍA MAESTRA V4 — Experiencia de uso y diseño (V2: el QUÉ + el CÓMO)

> **Propósito.** Mejorar BandFlow en **coherencia, experiencia de uso, diseño visual y diseño de
> interacción**, en la piel de un músico que se la descarga por primera vez.
>
> **De dónde viene.** V1 (el QUÉ) salió de un estudio visual de las 14 páginas (escritorio + móvil)
> con datos de demo. Esta **V2 añade el CÓMO** a cada punto: solución concreta + ficheros + esfuerzo
> + dependencias. Falta cerrar prioridades contigo y, donde toque, afinar el diseño fino.
>
> **Convenciones.** Prioridad 🔴 alto · 🟠 medio · 🟢 nice-to-have · 🔌 necesita config/infra.
> Tipo [F]uncionalidad · [V]isual · [I]nteracción. Esfuerzo **S** (≤½ día) · **M** (1 día) · **L** (varios).
> Todo **aditivo** y con el bucle de siempre (doctor + test + cachebust + deploy + verificación).
>
> _V2 — 2026-06-24._

---

## 0. Principios de diseño que guían la V4 (acordados antes de tocar)

Para que el CÓMO sea coherente, fijamos estas reglas (van a `design-system.css`):
1. **Un solo lenguaje de iconos:** SVG de `icons.js` (Lucide). Cero emoji en UI de chrome (sí en
   contenido del usuario y estados festivos puntuales).
2. **Densidad cómoda, no vacía:** contenedor de contenido más ancho y rejillas; nada de columnas
   estrechas con medio pantallazo en negro.
3. **Todo lo clicable lo parece:** hover (elevación + borde acento), `:focus-visible`, `cursor`.
4. **Movimiento con propósito:** transiciones 150–200 ms, `prefers-reduced-motion` respetado.
5. **Un acento, dos pesos:** coral `--bf-accent` para acciones primarias; nada de segundos naranjas.
6. **Cada pantalla responde "¿y ahora qué?":** dato principal + acción principal siempre visibles.

---

## 1. Coherencia estructural y navegación

- **1.1** 🟠 [V] **Setlists dentro del shell.** *Hoy:* `setlists.html` usa la top-bar antigua, sin lateral.
  **Cómo (M):** migrar `setlists.html` a la estructura `bf-shell` (como `library.html`): `<div class="bf-shell"><main class="bf-shell-main"><div class="bf-page">…`, cargar `design-system.css`+`shell.css`+`icons.js`+`shell.js`, y mover la cabecera (título + "➕ Nuevo setlist") al patrón `bf-row bf-row--between`. `setlists.js` no cambia de lógica (mismos ids). Quitar los enlaces 🏠/📚 (los da el lateral). El editor y el reproductor **siguen** fuera del shell (pantallas enfocadas).
- **1.2** 🟠 [V] **Terminología unificada → "Colecciones".** *Hoy:* banda dice "Repertorios", personal "Colecciones".
  **Cómo (S):** en el espacio de banda renombrar la pestaña y textos "Repertorio(s)" → "**Colecciones**" (`band.js` TABS label, panel header y textos en `bands.js` `loadCollections`/`newCollection`/empty-states). Dejar la palabra "repertorio" SOLO para "Todas las canciones de la banda" (el pool). Tests e2e que buscan `data-tab="repertorio"` siguen valiendo (cambiamos label visible, no la key). Verificar `test_bands_ui`/`test_band_space` por si asertan el texto.
- **1.3** 🟠 [V] **Iconos SVG en todas partes.** *Hoy:* emoji en reproductor, setlists, perfil, y acciones (🗑️💬📊💾).
  **Cómo (M):** ampliar `icons.js` con los iconos que falten (Lucide: `home, library, printer, guitar/tuner, plus, save, trash, message-circle, download, edit, play, square, maximize`). Reemplazar emoji por `bfIcon('name')` en `index.html`/`app.js` (top+bottom bar), `setlists.html`, `profile.html`, y los botones de acción de `bands.js`. Tooltips (`title=`/`aria-label`) en todos. **Cazar el "🐈"** del reproductor (averiguar qué es y darle icono correcto).
- **1.4** 🟠 [I] **Pestañas de banda en móvil.** *Hoy:* 9 pestañas con scroll horizontal y las últimas ocultas sin pista.
  **Cómo (S):** en `shell.css`/`design-system.css` (`.bf-tabs`): `overflow-x:auto` + **fade/máscara** en el borde derecho que insinúe scroll + `scroll-snap`. Marcar la pestaña activa siempre visible (scrollIntoView al activar en `band.js`). Alternativa L: agrupar las menos usadas (Giras/Ajustes) en un "⋯ Más".
- **1.5** 🟢 [F] **Acceso a la banda activa desde el lateral.** *Hoy:* Bandas → la banda (2 saltos).
  **Cómo (M):** bajo "Bandas" en `shell.js`, listar mis bandas (avatar + nombre) como sub-items que llevan a `band.html?id=`. Reusa `GET /bands/`. Colapsable si hay muchas.

---

## 2. Paneles que dan valor de un vistazo

- **2.1** 🔴 [V/F] **Inicio = panel de control.** *Hoy:* saludo + eventos + mensajes, pasivo y con mucho vacío.
  **Cómo (M):** rediseñar `home.js` a **rejilla de 2 columnas** (escritorio): (a) **Próximo evento destacado** (card grande: cuenta atrás, sala, tu asistencia con botón "¿Vas?"), (b) **Tu saldo** agregado (reusa `GET /me/balances`, total debes/te deben → enlace a Finanzas), (c) **Accesos rápidos** (chips: "➕ Nueva canción", "🎵 Setlists", "Mi banda"), (d) últimos mensajes (como ahora, más compacto). Nuevo endpoint opcional `GET /me/summary` que agregue todo en una llamada (o componer con los `/me/*` ya existentes). Skeletons ya hay.
- **2.2** 🔴 [V/F] **Resumen de banda útil.** *Hoy:* solo "Sobre la banda" + 2 chips.
  **Cómo (M):** en `band.js` panel `resumen`, montar un dashboard: **próximo evento + confirmados**, **último mensaje del chat**, **saldos resumidos** (3 líneas + "ver finanzas"), **contadores** (canciones / setlists / colecciones), y botones de salto a cada pestaña. Reusa los loaders existentes (`loadAgenda`, `loadFinance`, `messages`, `band_songs`) o un `GET /bands/{id}/summary` nuevo (1 query agregada, sin N+1). Mantener "Sobre la banda" arriba pequeño.
- **2.3** 🟠 [V/F] **Tarjeta de banda enriquecida ("Mis bandas").** *Hoy:* nombre + rol + nº miembros.
  **Cómo (S/M):** en `bands.js` `loadBands`, tarjeta con **avatar/color** de la banda (iniciales sobre color derivado del id), **próximo evento** (texto corto) y **nº de canciones**. El próximo evento por banda → ampliar `GET /bands/` (campo `next_event`) o una llamada ligera. Empty-state ilustrado con CTA (crear / código de invitación) — **2.3b**.
- **2.4** 🟢 [V/F] **Perfil con más cuerpo.** *Hoy:* 2 campos.
  **Cómo (S):** en `profile.html`/`profile.js`, mostrar **avatar** (iniciales/color por ahora), **mis bandas** (chips con rol), e instrumentos como **chips** editables en vez de texto con comas. Avatar subido → **🔌 Storage (V4-F6)**.

---

## 3. Tarjetas, listas y densidad

- **3.1** 🟠 [V/I] **Tarjeta de canción con play y jerarquía.** *Hoy:* plana, sin play visible.
  **Cómo (M):** en `library.js` `renderGrid` + `style.css` `.song-card`: en **hover** mostrar un botón **▶** flotante (abre el reproductor) y elevar la card; título más grande, artista atenuado, las pills (BPM/secciones) más sutiles (una sola fila, menos peso). Franja/ío de color por fuente (👤 personal vs 🎸 banda). Acciones (editar/borrar/**añadir a colección**) en esquina, visibles en hover.
- **3.2** 🟠 [I] **Filas de Agenda más limpias.** *Hoy:* asistencia + estado + 💬 + 🗑️ todo en línea.
  **Cómo (M):** en `bands.js` `loadAgenda`, reorganizar la fila: **principal** = icono tipo + título + fecha + tu asistencia (3 botones). **Secundario** (estado de booking admin, 💬 hilo, 🗑️ borrar) detrás de un menú **"⋯"** por evento. La línea de confirmados, debajo, discreta (ya está).
- **3.3** 🟢 [V] **"Quitar" ≠ "Borrar".** *Hoy:* ✕ rojo para quitar de repertorio/setlist.
  **Cómo (S):** quitar (de una lista) usa icono neutro (`minus`/`x` gris); el rojo solo para borrado real (soft delete). Ajuste en `bands.js`/`setlists.js`/`library.js` (clases de botón).
- **3.4** 🟠 [V] **Color de identidad por banda, consistente.** *Hoy:* el banner tiene avatar de color; no se reutiliza.
  **Cómo (S):** función `bandColor(id)` (hash → HSL estable) en un helper compartido; usarla en el avatar del banner, la tarjeta de "Mis bandas", las etiquetas de banda en Inicio/Agenda/Chat. Logo real → 🔌 Storage.

---

## 4. Interacción y "vida"

- **4.1** 🔴 [I] **Hover/active/focus ricos.** **Cómo (S):** en `design-system.css`, estados unificados para `.bf-card`, `.song-card`, `.bf-list-item`, `.setlist-song`, `.bf-tab`: hover = `translateY(-1px)` + borde `--bf-accent-weak` + sombra; `:focus-visible` claro; `cursor:pointer`. Una sola fuente de verdad.
- **4.2** 🟠 [I] **Transiciones suaves.** **Cómo (S):** `transition` en tabs (subrayado deslizante), modales (fade+scale de `.modal-overlay`/`.modal-card`), y aparición de listas. Guard `@media (prefers-reduced-motion: reduce)`.
- **4.3** 🟠 [I] **Microinteracciones de feedback.** **Cómo (M):** al añadir/guardar, animación breve en el elemento (no solo toast); al marcar "Voy", transición de color. Pequeña librería de keyframes en `design-system.css` (`bf-pop`, `bf-flash`).
- **4.4** 🟠 [I] **Skeletons en todas las vistas.** *Hoy:* solo Inicio; Giras y otras muestran "Cargando…".
  **Cómo (S):** reutilizar `.bf-skeleton` en `band.js` (giras, agenda, finanzas, repertorio…), `agenda.js`, `finanzas.js`, `chat.js`, `library.js`. Helper `bfSkeletonList(n)`.
- **4.5** 🟢 [I/F] **Drag & drop para reordenar setlist.** **Cómo (M):** en el editor de setlist (`bands.js`/`setlists.js`), HTML5 drag (o pointer events) sobre `#sl-selected`; al soltar, reordenar el array `selected` y `render()`. El PATCH ya acepta el nuevo orden (`items` en orden). Touch-friendly.
- **4.6** 🟢 [I] **Hoja de atajos.** **Cómo (S):** un botón "?" en el reproductor que abre un modal con los atajos (espacio, flechas/pedalera, Esc).

---

## 5. La joya — reproductor en directo

- **5.1** 🔴 [V] **Iconos del reproductor a SVG.** (Ver 1.3.) **Cómo (M):** `index.html`/`app.js`: top-bar (BPM, tono, herramientas, navegación) y bottom-bar (transporte) con `bfIcon`. Identificar el 🐈 y el 🔧 y nombrarlos bien (afinador, diagramas…). Tooltips + `aria-label`.
- **5.2** 🟠 [V] **Top-bar ordenada.** **Cómo (M):** agrupar en 3 zonas con separadores: **transporte/tempo** (BPM, tono), **herramientas** (afinador, diagramas, imprimir, vídeo ref.), **navegación** (inicio, biblioteca, +). En móvil, colapsar herramientas en un "⋯".
- **5.3** 🟠 [V/I] **Más espectacular en escenario.** **Cómo (M):** en `style.css` (modo escenario/`stage-mode`): acordes más grandes y con más contraste, transición suave al cambiar de línea activa, animación de la "bolita" de posición, y un **modo alto contraste** para poca luz. La lógica de la joya (`sync_engine.js`/`score_render.js`) **no se toca**, solo CSS/clases.
- **5.4** 🟢 [F] **Loop A-B / metrónomo audible / autoscroll fino.** **Cómo (L):** requieren tocar el motor (seek/bucle) → **se hace en V3-F6**, no en V4. Anotado para no perderlo.

---

## 6. Onboarding y primera impresión

- **6.1** ✅ [F] **Inicio sin bandas → "Primeros pasos"** (hecho). Mantener; revisar visual al rediseñar Inicio (2.1).
- **6.2** 🟠 [V] **Login pulido.** **Cómo (S/M):** revisar `login.html`/`login.js`: branding (logo BandFlow), claim claro ("Gestiona tu banda: repertorio, bolos y cuentas"), botón Google prominente, y modo oscuro coherente. (No lo vimos en el estudio por el modo test.)
- **6.3** 🟢 [F] **Tour la primera vez en una banda.** **Cómo (M):** tooltips secuenciales (qué es cada pestaña) la 1ª visita, guardados en `localStorage`. Sin dependencias.
- **6.4** 🟢 [V] **Todos los vacíos con CTA.** **Cómo (S):** auditar empty-states; usar siempre `bfEmpty(icono, título, texto, {cta})` con botón de acción (no solo texto).

---

## 7. Sistema de diseño y acabado fino

- **7.1** 🟠 [V] **Aprovechar el ancho.** **Cómo (M):** subir el `max-width` del `.bf-page`/contenedor y usar rejillas (`grid` 2–3 col) en Inicio, Bandas, Explorar, Perfil. Definir un ancho de contenido estándar en `design-system.css`. Revisar que no rompa lectura en pantallas anchas.
- **7.2** 🟢 [V] **Un solo acento.** **Cómo (S):** localizar los botones con naranja "brillante" (p. ej. "Buscar" en `biblioteca-global.html`, "Importar con IA" en `editor.html`) y pasarlos a `--bf-accent`. Quitar colores hardcodeados.
- **7.3** 🟢 [V] **Escala tipográfica.** **Cómo (S):** revisar tokens de tamaño/peso (h1/h2/h3/body/small/badge) en `design-system.css` para una escala consistente; aplicarla donde haya tamaños sueltos.
- **7.4** 🟢 [V] **Modo claro a la par.** **Cómo (S):** auditar todas las páginas en `data-theme="light"` (capturas) y corregir contrastes/colores sueltos.
- **7.5** 🟢 [♿] **Accesibilidad.** **Cómo (M):** pasada con la checklist WCAG AA (contraste de grises secundarios, foco visible, objetivos táctiles ≥44px, `aria-label` en iconos). Se puede apoyar en la skill `design:accessibility-review`.

---

## 8. Funcionalidad detectada

- **8.1** 🟢 [F] **"Añadir a colección/setlist" desde la tarjeta** de canción. **Cómo (M):** botón en `.song-card` (Biblioteca) → modal con mis colecciones/setlists (checkbox) → PATCH. Reusa endpoints existentes.
- **8.2** 🟢 [F] **Buscador en repertorio de banda y setlists.** **Cómo (S):** input de filtro cliente en `bands.js` (repertorio) y en `setlists.js`.
- **8.3** 🟢 [F] **Reordenar dentro de colección/setlist.** (Ver 4.5; en colecciones es opcional por ser "sin orden".)
- **8.4** 🔌 [F] **Avatar/logo de banda y perfil.** **Cómo (L):** **Storage** (Supabase bucket + políticas) → subir imagen → `Band.logo_url`/`MusicianProfile.avatar_url` (migración). **V4-F6.**
- **8.5** 🔌 [F] **Notificaciones/recordatorios** (email/push). **V4-F6** (infra de envío).
- **8.6** 🔌 [F] **Página pública/EPK (V3-F8)** y **ensayo en tiempo real (V3-F6).** Fuera de V4 (fases V3 grandes).
- **8.7** 🟢 [F] **Caché por temporada.** **Cómo (M):** agregación por rango de fechas en finanzas/giras.
- **8.8** 🟢 [F] **Duplicar** canción/setlist/colección. **Cómo (S):** botón → POST con los datos del original.

---

## 9. Plan por fases (propuesta para aplicar)

> Orden por **impacto/esfuerzo** y **sin dependencias externas primero**. Cada fase = varias tareas
> T-NNN en `TASKS.md`, con doctor verde + test + deploy + verificación.

- **V4-F1 — Acabado coherente (S/M, solo front/CSS, alto impacto visual):**
  1.3 iconos SVG (incl. reproductor 5.1) · 1.1 setlists al shell · 1.2 terminología "Colecciones" ·
  7.2 un solo acento · 4.1 hover/focus · 4.2 transiciones · 3.3 quitar≠borrar. → *La app se siente
  "de una pieza".*
- **V4-F2 — Paneles de control (M, algo de backend agregado):**
  2.2 Resumen de banda útil · 2.1 Inicio panel de control · 2.3 tarjeta de banda + 2.3b empty-state ·
  3.4 color de banda consistente. → *Cada pantalla da valor al entrar.*
- **V4-F3 — Tarjetas, densidad y carga (S/M, front):**
  3.1 tarjeta de canción con play · 3.2 agenda más limpia · 4.4 skeletons en todo · 7.1 ancho/rejillas ·
  4.3 microinteracciones. → *Más bonita y con vida.*
- **V4-F4 — La joya en directo (M, CSS + algo de JS):**
  5.2 top-bar ordenada · 5.3 escenario espectacular · 4.5 drag&drop setlist · 4.6 atajos · 6.4 vacíos con CTA.
- **V4-F5 — Funcionalidad y remate (S/M):**
  8.1 añadir-a desde tarjeta · 8.2 buscadores · 8.8 duplicar · 1.4 pestañas móvil · 1.5 banda en lateral ·
  6.2 login · 6.3 tour · 7.3 tipografía · 7.4 modo claro · 7.5 accesibilidad · 8.7 caché por temporada.
- **V4-F6 — Lo que necesita tu config (🔌):**
  8.4 avatares/logos (Storage) · 2.4 avatar perfil · 8.5 notificaciones · 8.6 EPK/realtime (V3).

> **Recomendación:** empezar por **V4-F1** (rápida, se nota muchísimo, cero backend) y **V4-F2**
> (convierte las pantallas vacías en útiles). Con eso la app pega un salto de percepción.

---

## 10. Proceso

1. **(Esta V2.)** Oscar la repasa: confirma/ajusta el CÓMO y el orden de fases.
2. **V3 (si hace falta):** afinar diseño fino de los puntos 🔴 (bocetos/decisiones concretas).
3. **Aplicar fase a fase** con el bucle de siempre. Cada tarea cierra con su test + deploy + verificación.
