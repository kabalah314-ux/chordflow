# BandFlow — Especificación de diseño maestra (Fase 13)

> **Fuente de verdad visual** para implementar la Fase 13 (T-073…T-082) en HTML/CSS/JS
> vanilla. Extraída del prototipo de Claude Design (tokens + 19 fragmentos de pantalla).
> Convive con `CLAUDE.md` (reglas operativas) y las guías V2 (dirección de producto).

---

## 1. Resumen y cómo usar este documento

BandFlow es el reskin del SaaS de gestión de bandas sobre la base ya creada en T-073
(`static/design-system.css`, clases `bf-*`). Este doc traduce el prototipo a:

1. Un **sistema de tokens** (sección 2) que se aplica reescribiendo las variables de
   `static/design-system.css`. Los componentes `bf-*` no cambian: heredan de los tokens.
2. Un **app shell** común (sección 3): lateral + banner de banda + slot main.
3. Una **sección por pantalla** (sección 4): propósito, layout, componentes `bf-*`,
   interacciones, mapeo de datos `{{}}` → API real, página destino y avisos.
4. Una **tabla-resumen** (sección 5): pantalla → página static → router(s) → tarea.

**Cómo trabajar con él:**

- Empieza por reescribir los tokens (sección 2 → bloque "Cambios vs design-system.css").
  Tras hacerlo, **toda** la app que ya use `bf-*` adopta el aspecto BandFlow.
- Cada pantalla del prototipo es **markup inline con placeholders** `{{...}}`. Al portar a
  vanilla: sustituir el inline por clases `bf-*` + tokens, sustituir `{{...}}` por datos
  reales de la API (render imperativo con `createElement`/`map().join('')` + `escapeHtml`).
- **Regla XSS (CLAUDE.md):** escapar SIEMPRE texto de usuario (nombres, body de mensajes,
  títulos) antes de inyectar en el DOM.
- **Regla cache-busting:** tras tocar cualquier `.js`/`.css`, ejecutar
  `python harness/cachebust.py`.
- **Regla multi-tenant (oro):** toda ruta de banda valida pertenencia+rol y filtra por
  `band_id`; cada ruta de banda exige test de aislamiento (ajeno → 403/404).
- **La joya intacta:** `sync_engine.js` y `score_render.js` NO se tocan; en el reproductor
  solo se reemplaza el *chrome*/markup.

### Convención de marca (decisión clave a unificar)

El prototipo usa **acento naranja coral** (`#ff6b4a` oscuro / `#ee5530` claro) y conmuta
tema con `data-bf-theme="dark|light"`. El `design-system.css` actual usa **azul** (`#6c8cff`)
y `:root[data-theme="light"]`. **Decisión recomendada:** adoptar el naranja del prototipo
(remapear `--bf-primary`) y **unificar el atributo de tema** (elegir uno; el `toggleTheme`
debe escribir el mismo selector que lee el CSS). El acento es además *overridable por banda*
vía `--accent`/`--accent-weak` inline en el contenedor raíz.

### Identidad tipográfica

**IBM Plex Sans** (UI) + **IBM Plex Mono** (datos numéricos: acordes, BPM, importes, tonos).
El actual usa Inter + Roboto Mono → cargar `@font-face` de IBM Plex.

---

## 2. Sistema de tokens

### 2.1 Color — rol → hex (oscuro) y (claro)

| Rol (variable destino `--bf-*`) | Oscuro (`data-bf-theme=dark`) | Claro (`data-bf-theme=light`) | Notas |
|---|---|---|---|
| `--bf-bg` (app-bg) | `#0d0d10` | `#f5f5f2` (hueso cálido) | no azul-grisáceo |
| `--bf-surface` | `#16161b` | `#ffffff` | paneles/sidebar |
| `--bf-surface-2` | `#1c1c23` | `#fafaf8` | cards, inputs |
| `--bf-surface-3` | `#23232c` | `#f0f0ec` | hover/activo, badges key |
| `--bf-border` | `rgba(255,255,255,.08)` | `rgba(20,20,30,.10)` | |
| `--bf-border-strong` | `rgba(255,255,255,.15)` | `rgba(20,20,30,.18)` | |
| `--bf-text` | `#ededf1` | `#1a1a20` | |
| `--bf-text-muted` | `#9a9aa6` | `#5d5d68` | |
| `--bf-text-faint` | `#6a6a76` | `#8c8c96` | |
| `--bf-primary` (=accent) | `#ff6b4a` | `#ee5530` | **NARANJA** (era azul) |
| `--bf-accent-weak` (nuevo) | `rgba(255,107,74,.16)` | `rgba(238,85,48,.12)` | fondo translúcido del acento |
| `--bf-hover` (nuevo) | `rgba(255,255,255,.05)` | `rgba(20,20,30,.04)` | |
| `--bf-success` | `#2dd4a7` | `#11a37a` | |
| `--bf-success-weak` (nuevo) | `rgba(45,212,167,.15)` | `rgba(17,163,122,.13)` | |
| `--bf-danger` | `#ff5d6c` | `#e0364a` | |
| `--bf-danger-weak` (nuevo) | `rgba(255,93,108,.15)` | `rgba(224,54,74,.12)` | |
| `--bf-warning` | `#f5c518` | `#c08f00` | |
| `--bf-warning-weak` (nuevo) | `rgba(245,197,24,.15)` | `rgba(192,143,0,.14)` | |

**Notas de color:**
- El prototipo **no tiene** `--bf-info` ni `--bf-primary-hover`/`-contrast`. El "primary" ES
  el `accent`. ⚠️ Para hover del acento, usar `filter: brightness(1.07)` (patrón del prototipo)
  en lugar de un token `-hover`, o conservar `--bf-primary-hover` recoloreado al coral.
- **`--bf-on-primary`** se mantiene `#ffffff` (texto/iconos sobre acento).
- **Badges de rol** (`--bf-role-admin/member/guest`): NO existen en el prototipo. Mantenerlos
  como capa propia del proyecto. Si se quieren alinear a la paleta: admin→warning (`#f5c518`),
  member→info/acento, guest→text-muted (`#9a9aa6`). Decisión abierta; por defecto conservar.
- **Color por banda:** `currentBand.color`/`gradient`/`b.color`/`m.color`/`bandBg`/`bandColor`
  son **dinámicos por instancia**, no son tokens. ⚠️ El backend NO expone color de banda hoy
  (ver gaps); derivar determinísticamente en cliente (hash de `band_id`) o añadir columna.

### 2.2 Tipografía

| Aspecto | Valor BandFlow |
|---|---|
| Familia UI (`--bf-font-ui`) | `'IBM Plex Sans', system-ui, sans-serif` |
| Familia mono (`--bf-font-mono`) | `'IBM Plex Mono', ui-monospace, monospace` |
| Pesos UI cargados | 400, 500, 600, 700 (bold máx = **700**) |
| Pesos mono cargados | 400, 500, 600 |
| Tamaño base | **15px** (no 16px/1rem) |
| Render | `-webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility` |

El prototipo **no** define escala de tamaños en variables (aplica px inline por componente).
Conservar la escala `--bf-fs-*` actual del design-system como aproximación, ajustando el
peso bold a 700. Tamaños observados por componente: H1 26px/700 (player/login 27px),
H2 secciones 15px/600, valores KPI 22-23px/700, body 14-15px, labels 13px/600, mono 12px.

### 2.3 Radios

El prototipo **no** define variables de radio (única pista: scrollbar-thumb `8px`); los radios
van inline (~8-12px, lenguaje suave). Conservar la escala actual ajustando el base:

| Token | Valor sugerido | Uso |
|---|---|---|
| `--bf-radius-sm` | `6px` | badges key, steppers, barra progreso |
| `--bf-radius` | `10px` (ok; ~9-11px del proto) | inputs, botones, avatares cuadrados, chips acorde |
| `--bf-radius-lg` | `16px` (~13-18px del proto) | cards, banners, card de transport |
| `--bf-radius-full` | `999px` | avatares circulares, pills de rol |

### 2.4 Sombras (dependientes de tema — solo 2 niveles)

| Token | Oscuro | Claro |
|---|---|---|
| `--bf-shadow-sm` | `0 1px 2px rgba(0,0,0,.4)` | `0 1px 2px rgba(20,20,30,.06)` |
| `--bf-shadow` | `0 1px 2px rgba(0,0,0,.4), 0 8px 28px rgba(0,0,0,.35)` | `0 1px 2px rgba(20,20,30,.06), 0 10px 30px rgba(20,20,30,.08)` |

⚠️ El prototipo **no tiene** un tercer nivel `lg`. `--bf-shadow` combina una sombra de borde
fina + una de elevación amplia en una sola declaración. Tematizar la sombra en claro (tinte
azul-grisáceo `rgba(20,20,30)`, más difusa). Si se conserva `--bf-shadow-lg`, recolorearlo.

### 2.5 Espaciado

El prototipo **no** define variables de espaciado (todo inline). La escala de 4px actual es
compatible y se conserva tal cual:

`--bf-space-1: .25rem` · `-2: .5rem` · `-3: .75rem` · `-4: 1rem` · `-5: 1.5rem` · `-6: 2rem` · `-8: 3rem`

Layout del shell: `--bf-sidebar-w` (252px en el proto; el actual 248px — ajustar a 252px o
dejar 248px). Contenedores de página centrados con `max-width` 680/760/820/920/1000/1080px
según pantalla (ver cada sección).

### 2.6 Animaciones a portar (no existen en design-system.css)

- `@keyframes bf-eq` — ecualizador (`scaleY 0.35 ↔ 1`), usado en el logo de marca (2 tamaños).
- `@keyframes bf-fade` — entrada (`translateY(8px)` → 0, opacidad).
- `@keyframes bf-pulse` — pulso (badges/indicadores).

### 2.7 Cambios vs `static/design-system.css` actual (lista exacta a reescribir)

> El bloque actual de tokens está en `:root` y `:root[data-theme="light"]` (líneas ~18-108).

**A. ACENTO/MARCA (el cambio más grande)** — actual azul `--bf-primary #6c8cff` / hover `#5a7bff`:
1. `--bf-primary`: `#6c8cff` → **`#ff6b4a`** (claro: `#ee5530`).
2. `--bf-primary-hover`: `#5a7bff` → coral más oscuro **o** eliminar y usar `filter:brightness(1.07)`.
3. Añadir **`--bf-accent-weak`**: `rgba(255,107,74,.16)` (claro `rgba(238,85,48,.12)`).
4. `--bf-primary-contrast`: `#0b0c10` → revisar (queda `--bf-on-primary: #ffffff`, se mantiene).
5. Sustituir el `box-shadow` de focus azul (`0 0 0 3px rgba(108,140,255,.18)`) por coral
   `rgba(255,107,74,.18)` donde aparezca en los componentes `.bf-input`/`.bf-btn`.

**B. TIPOGRAFÍA (cambio de identidad):**
6. `--bf-font-ui`: `'Inter', …` → **`'IBM Plex Sans', system-ui, sans-serif`**.
7. `--bf-font-mono`: `'Roboto Mono', …` → **`'IBM Plex Mono', ui-monospace, monospace`**.
8. Cargar `@font-face` IBM Plex Sans (400/500/600/700) + IBM Plex Mono (400/500/600).
9. `--bf-fw-bold`: `800` → **`700`** (el prototipo solo carga hasta 700).
10. Tamaño base de body: 16px → **15px** (aplicar en el contenedor raíz del shell).

**C. SUPERFICIES (neutro→casi-negro / hueso):**
11. Oscuro: `--bf-bg #0b0c10→#0d0d10`, `--bf-surface #14161d→#16161b`,
    `--bf-surface-2 #1c1f29→#1c1c23`, `--bf-surface-3 #262a36→#23232c`.
12. Claro: `--bf-bg #f6f7f9→#f5f5f2`, `--bf-surface #ffffff` (igual),
    `--bf-surface-2 #f0f2f5→#fafaf8`, `--bf-surface-3 #e4e7ec→#f0f0ec`.

**D. BORDES:**
13. Oscuro `--bf-border-strong`: `.16` → **`.15`**.
14. Claro: tint `rgba(15,18,25,…)` → **`rgba(20,20,30,…)`**; `--bf-border-strong` `.20` → **`.18`**.

**E. TEXTO:**
15. Oscuro: `--bf-text #f2f4f8→#ededf1`, `--bf-text-muted #9aa3b2→#9a9aa6`,
    `--bf-text-faint #6b7280→#6a6a76`.
16. Claro: `--bf-text #14161d→#1a1a20`, `--bf-text-muted #5b6472→#5d5d68`,
    `--bf-text-faint #8a93a3→#8c8c96`.

**F. ESTADOS SEMÁNTICOS:**
17. `--bf-success #34d399→#2dd4a7`, `--bf-danger #f87171→#ff5d6c`, `--bf-warning #fbbf24→#f5c518`.
18. Añadir **`--bf-success-weak` / `--bf-danger-weak` / `--bf-warning-weak`** (ver tabla 2.1).
19. `--bf-info #60a5fa`: no existe en el prototipo → eliminar o conservar como info propio.
20. `--bf-role-admin/member/guest`: no existen en el prototipo → conservar como capa propia.

**G. SOMBRAS:**
21. Reescribir `--bf-shadow-sm` y `--bf-shadow` a los valores de la tabla 2.4 y **tematizarlas**
    en claro (tinte `rgba(20,20,30)`). `--bf-shadow-lg`: eliminar o recolorear (el proto no lo tiene).

**H. NUEVO TOKEN:**
22. Añadir **`--bf-hover`**: `rgba(255,255,255,.05)` (claro `rgba(20,20,30,.04)`).

**I. CONVENCIÓN DE TEMA:**
23. Unificar atributo: prototipo usa `data-bf-theme="dark|light"`; actual `:root[data-theme="light"]`.
    Elegir uno y que `toggleTheme` escriba el mismo selector que lee el CSS.

**NO requieren reescritura (compatibles):** escala `--bf-space-*` (4px), radios (mantener,
ajuste menor), utilidades `.bf-*` (heredan tokens), estructura de componentes. La joya
(`sync_engine`/`score_render`) y `style.css` quedan intactos.

---

## 3. App shell (lateral + banner de banda + slot main)

**Propósito:** cascarón persistente de la app autenticada. Da contexto multi-tenant (TÚ vs
BANDA) y navegación a todo el SaaS.

**Página destino:** NUEVO `static/shell.js` (+ `static/shell.css` o ampliar `design-system.css`),
montado en una página anfitriona (NUEVO `static/app.html` o reusando `index.html`/`bands.html`).
Hoy la navegación vive dispersa en cada página.

**Layout:** contenedor raíz `flex` horizontal, `height:100vh`, `overflow:hidden`, fondo `--bf-bg`.
1. **`<aside>` de 252px** (`--bf-sidebar-w`), columna `flex` altura completa, fondo `--bf-surface`,
   borde derecho `--bf-border`:
   - (a) **Marca** clicable: cuadrado acento 30px radio 9px con 3 barras blancas (anim `bf-eq`)
     + wordmark "BandFlow" 17px/700. → `goHome`.
   - (b) **Zona de contexto condicional:**
     - `is.bandCtx` → **banner de banda compacto**: tarjeta padding 12px radio 13px, fondo/borde
       teñidos del color de banda, avatar 38px iniciales, nombre + género, fila con badge de rol +
       botón "Salir" (`exitBand`).
     - `is.youCtx` → **eyebrow "TÚ"** en mayúsculas (11px/600, `--bf-text-faint`).
   - (c) **Nav scrollable** (`flex:1`): itera `navItems` (icono + label + badge opcional). Item
     activo: fondo `--bf-surface-3`, color `--bf-text`, `aria-current="page"`.
   - (d) **Pie** con separador: tarjeta de perfil (avatar "DV" + "Dani Vega" / "Mi perfil" + icono
     settings → `goPerfil`) y botón de tema full-width (`toggleTheme`).
2. **`<main>`** `flex:1`, `overflow-y:auto`, slot donde se monta cada pantalla.

**Componentes → clases `bf-*`:**

| Componente | Clase / nota |
|---|---|
| Sidebar `<aside>` | sin clase contenedora en DS — estilo de shell propio (`shell.css`) |
| Marca / logo | inline + `@keyframes bf-eq` (portar) |
| Banner de banda (lateral) | variante compacta de `.bf-band-banner` (la existente es horizontal para main) |
| Badge de rol | `.bf-badge` + `.bf-badge--admin/--member/--guest` |
| Botón Salir | `.bf-btn--ghost .bf-btn--sm` |
| Nav item | `.bf-nav-item` (+ `aria-current=page`); badge numérico = pill `--bf-primary`/`#fff` |
| Tarjeta perfil | `.bf-avatar` + texto; hover `--bf-hover` |
| Botón tema | `.bf-btn--ghost` width 100% |

**Datos `{{}}` → API:**

| Placeholder | Fuente real |
|---|---|
| `{{theme}}`, `{{accent}}`, `{{accentWeak}}` | localStorage / cliente (no API) |
| `{{is.bandCtx}}` / `{{is.youCtx}}` | estado de cliente (entrar/salir de banda) |
| `{{currentBand.name}}` | `GET /bands/{id}` (BandResponse.name) |
| `{{currentBand.initials}}` | derivado en cliente de `name` |
| `{{currentBand.roleLabel/roleBg/roleColor}}` | `membership.role` (BandSummary.role) |
| `{{currentBand.color}}`, `{{bandBgValue}}`, `{{bandBorderValue}}` | ⚠️ NO existe color en el modelo Band → derivar de `band_id` o añadir columna |
| `{{currentBand.genre}}` | ⚠️ NO existe en BandResponse (gap) |
| `{{navItems}}`, `{{n.go}}` | construido en cliente (no API) |
| `{{n.badge}}` (no-leídos) | ⚠️ NO hay endpoint de conteo en messages_router (gap) |
| Avatar "DV" / "Dani Vega" | `GET /profile/me` (MusicianProfileResponse.display_name) |

**API consumida:** `GET /bands/` (conmutador), `GET /bands/{id}`, `GET /bands/{id}/members`
(rol — verificar si `/bands/` ya devuelve el rol propio para evitar la llamada extra),
`GET /profile/me`, `GET /config`.

**Avisos de integración ⚠️:**
- Acento azul→naranja (re-tokenizar `--bf-primary`) o el shell desentona.
- Unificar atributo de tema (`toggleTheme` escribe lo que lee el CSS).
- Cargar IBM Plex (ajustar `--bf-font-ui/-mono`).
- **Gap badge no-leídos:** no hay `GET /bands/{id}/messages/unread_count`; omitir o derivar
  con `last_read` local.
- **Gap color/género de banda:** no existen como columnas; derivar color en cliente o migración Alembic.
- Confirmar si `BandSummary` incluye el rol propio (evitar `/members` por render).
- Portar estados `style-hover` (atributo no estándar) a reglas `:hover` reales.
- **Iconos lucide** (`data-lucide`): el repo no incluye lucide → añadir la librería o sustituir
  por SVG/emoji inline. (Aplica a TODAS las pantallas.)
- Aislamiento multi-tenant: toda llamada con `band_id` pasa por `band_auth.py`.

---

## 4. Pantallas

> Convención común a todas: re-tokenizar acento a naranja, cargar IBM Plex, escapar XSS,
> sustituir lucide, correr `cachebust.py` tras tocar js/css. No se repite en cada ficha.

### 4.1 Login / Registro

- **Propósito:** puerta de entrada (auth) antes del shell.
- **Página:** `static/login.html` (reskin; conservar IDs que usa `login.js`).
- **Layout:** `100vh` en dos columnas flex. **Izquierda** (siempre): caja `max-width 380px`
  centrada con marca (logo eq 38px + wordmark 21px/700), H1 "Entra en tu música" (27px/700),
  subtítulo muted, **tab segmentada** Entrar/Crear cuenta, input Email, input Contraseña, CTA
  primaria full-width, enlace "¿Olvidaste tu contraseña?" (faint). **Derecha** (solo
  `data-wide`): panel decorativo con gradiente + equalizer grande 5 barras + eslogan.
- **Componentes → `bf-*`:** logo eq (inline + `bf-eq`); H1 `.bf-h1`; tab segmentada → crear
  `.bf-segment` o reusar `.bf-tabs/.bf-tab` (activo en `--bf-primary`); inputs `.bf-input` +
  `.bf-label`; CTA `.bf-btn .bf-btn--primary` full-width; enlace `.bf-faint`.
- **Interacciones:** tab Entrar/Crear cuenta cambia modo + texto de CTA `{{loginCta}}`; CTA →
  `signInEmail`/`signUpEmail` (Supabase) → redirige a `library.html`.
- **Datos → API:** auth vía **Supabase** (`auth.js`: `signInWithPassword`, `signUp`,
  `signInWithOAuth`); `GET /config` (supabase_url, anon_key, test_mode).
- **Avisos ⚠️:** (1) conservar IDs `#login-form #email #password #btn-login #btn-register
  #login-msg` (o actualizar `login.js`); el proto usa **una** CTA dinámica, el código actual
  tiene **dos** botones + botón Google que el proto no muestra → mantener Google (recomendado)
  bajo la CTA. (2) Portar `@keyframes bf-eq`. (3) No hay componente segmentado en `bf-*` → crear.
  (4) **Gap:** "olvidé contraseña" sin flujo → añadir `resetPasswordForEmail` si se quiere
  funcional. (5) Ocultar panel derecho en móvil (media query). (6) Vaciar valores demo de inputs.
  (7) `login.js` usa `#ff6b6b` hardcodeado para errores → migrar a `var(--bf-danger)`.

### 4.2 Inicio / Dashboard (TÚ) — vista personal multi-banda

- **Propósito:** aterrizaje personal; resumen a través de TODAS las bandas + feeds de eventos y mensajes.
- **Página:** NUEVO `static/inicio.html` (+ `inicio.js`), dentro del shell.
- **Layout:** contenedor `max-width 1080px`, padding 32/38px. (1) Saludo "Hola, {nombre}" +
  subtítulo. (2) Fila de 4 **stat-cards** (grid 4 col, gap 14px): Balance total / Próximo bolo /
  Mis bandas / Canciones. (3) Grid 2 col asimétrico (1.5fr/1fr, gap 18px): izquierda "Próximos
  eventos" (lista de event-cards) + derecha "Últimos mensajes" (panel con filas de conversación).
- **Componentes → `bf-*`:** stat-card `.bf-card` (valor mono `--bf-font-mono`, balance
  `.bf-amount--positive/--negative`); section-header `.bf-row--between` + enlace acción
  `--bf-primary`; event-card `.bf-card`/`.bf-list-item` + badge de banda `.bf-badge`;
  conversation-list `.bf-card` sin padding, filas separadas por border-bottom, avatar `.bf-avatar`,
  badge unread pill `--bf-primary`.
- **Interacciones:** "Ver agenda"→agenda; "Ver chat"/fila→chat; carga = fan-out (solo lectura).
- **Datos → API:** `GET /bands` (counts.bands, "1 como admin"); por cada banda
  `GET /bands/{id}/events` (próximos + próximo bolo), `GET /bands/{id}/messages` (últimos),
  `GET /bands/{id}/balances` (mi saldo → balance total); `GET /songs/` (counts.songs/sheets);
  `GET /profile` (display_name).
- **Avisos ⚠️:** **NO hay endpoint agregado cross-band** → FAN-OUT en cliente (N peticiones);
  tolerar 403/errores parciales por banda sin romper la pantalla. **Gaps:** sin
  `GET /me/dashboard` (recomendable a futuro); `{{c.unread}}` sin read-state en messages
  (omitir o añadir lecturas); balance total y próximo bolo global se calculan en cliente;
  color por banda no existe (derivar). "Sala Apolo" del proto está hardcodeado → viene del agregado.

### 4.3 Biblioteca (TÚ)

- **Propósito:** hub de repertorio del usuario (personal + de bandas); abrir el reproductor.
- **Página:** `static/library.html` (reescribir markup `style.css` → `bf-*`).
- **Layout:** `max-width 1080px`. (1) Cabecera: H1 "Biblioteca" + subtítulo, botón primario
  "Añadir canción". (2) Input búsqueda full-width con lupa. (3) Chips de filtro (wrap).
  (4) Grid `auto-fill minmax(250px,1fr)` gap 13px de tarjetas de canción (avatar banda + play
  circular, título truncado, banda, fila mono key/BPM/duración, badge "PARTITURA" success absoluto).
- **Componentes → `bf-*`:** H1 `.bf-h1`+`.bf-muted`; botón `.bf-btn .bf-btn--primary`; input
  `.bf-input` + wrapper relative; chips `.bf-badge`/pill (activo `--bf-primary`/`--bf-accent-weak`);
  tarjeta `.bf-card.bf-card--interactive`; avatar `.bf-avatar`; play `.bf-btn--icon` redondeado;
  badge key `.bf-badge` (`--bf-surface-3`); metadata `.bf-faint` mono; badge PARTITURA `.bf-badge`
  success (`--bf-success`/`--bf-success-weak`).
- **Interacciones:** Añadir→editor/`POST /songs/`; búsqueda filtra en cliente; chip cambia
  subconjunto; tarjeta/play → reproductor (`index.html?songId=...`).
- **Datos → API:** `GET /songs/` (SOLO personales, band_id IS NULL); `GET /bands/` +
  `GET /bands/{id}/songs/` por banda (fan-out); `GET /songs/{id}` (al reproducir).
- **Avisos ⚠️:** **Gap principal:** `GET /songs/` devuelve solo personales → fan-out para
  "personal Y de tus bandas". Derivar en JS: `{{s.bandName}}` (resolver band_id→nombre, no viene
  en SongSummary), `{{s.dur}}` (de `duration_beats`+bpm; puede ser null), `{{s.sheet}}`/PARTITURA
  (no hay flag; aproximar `section_count>0`), `{{s.bandBg/bandColor}}` (hash de band_id). No
  existe endpoint "todo mi repertorio" (valorar crearlo).

### 4.4 Bandas (lista) — "Mis bandas"

- **Propósito:** listar bandas del usuario; entrar a gestionar o crear nueva.
- **Página:** `static/bands.html` (ya existe; reskin `style.css` → `bf-*`; JS en `bands.js`).
- **Layout:** `max-width 1080px`. (1) Cabecera: H1 "Bandas" + subtítulo + botón "Nueva banda".
  (2) Grid `auto-fill minmax(290px,1fr)` gap 16px de tarjetas: portada de color/gradiente 64px
  alto + avatar 52px solapado (iniciales), cuerpo con nombre + badge rol, meta "{género} · {n}
  miembros", fila inferior instrumento + CTA "Entrar >".
- **Componentes → `bf-*`:** tarjeta `.bf-card.bf-card--interactive` + cabecera de color (CSS
  específico, no hay variante portada+avatar solapado); badge rol `.bf-badge--admin/member/guest`;
  CTA "Entrar" = texto-acento clicable; botón "Nueva banda" `.bf-btn .bf-btn--primary`.
- **Interacciones:** Nueva banda → `promptModal` → `POST /bands/`; tarjeta clicable → `openBand(id)`.
- **Datos → API:** `GET /bands/` (BandSummary: id, name, avatar_url, role, member_count);
  `POST /bands/`; `GET /bands/{id}`.
- **Avisos ⚠️:** derivar `gradient`/`color`/`initials` en cliente (hash id, iniciales name;
  avatar_url tiene prioridad). **Gaps:** `genre` no existe en Band/BandSummary (omitir o añadir
  columna+migración); `instrument` del usuario no está en BandSummary (join con perfil/membresía).
  Conservar estados cargando/vacío/error que el diseño no muestra.

### 4.5 Reproductor / Teleprompter (LA JOYA)

- **Propósito:** reproducir partitura resaltando el acorde activo según BPM con auto-scroll;
  transponer y ajustar tempo en vivo.
- **Página:** `static/index.html` (lógica en `app.js` + `sync_engine.js` + `score_render.js`;
  chrome en `style.css`).
- **Layout:** `100vh` columna. (1) Header fijo: botón volver, título + banda, badge de tono.
  (2) Área de partitura scrollable `max-width 760px` (padding-bottom 220px) con secciones
  (etiqueta uppercase acento) y líneas de segmentos (chip acorde mono + letra 22px). (3)
  **Transport flotante** anclado abajo (gradiente fade, `pointer-events:none` en wrapper / `auto`
  en barra): card redondeada radio 18px con barra de progreso + stepper BPM, Play/Pause circular
  52px acento, stepper Tono, toggle Auto-scroll.
- **Componentes → `bf-*`:** botón volver `.bf-btn--icon`; chip acorde mono (activo
  `--bf-accent-weak`/`--bf-primary`, inactivo `--bf-surface-2`/`--bf-text`); card transport
  `--bf-surface-2`+`--bf-border-strong`+`--bf-shadow`; progreso track `--bf-surface-3`/relleno
  `--bf-primary`; Play/Pause `.bf-btn--primary` circular; steppers (botones 30px radio 8px);
  toggle auto-scroll (on: `--bf-primary` translúcido / off: `--bf-border`).
- **Interacciones:** volver (`closePlayer`); BPM ±1 (`engine.setBpm` + `PATCH /songs/{id}`);
  Play/Pause; Tono ±1 semitono (-11..+11, `PATCH /songs`); auto-scroll toggle.
- **Datos → API:** `GET /songs/{id}` (SongResponse sections→lines→chords); `GET /songs/`
  (fallback); `PATCH /songs/{id}` (bpm/tono); `GET /setlists/{id}` (navegación con `?setlist=`).
- **Avisos ⚠️:** **NO tocar** `sync_engine.js`/`score_render.js` (solo chrome/markup +
  `bf-*`+tokens); `score_render.js` es el único renderer y trabaja con **ids** de acorde.
  **Gap:** `{{player.band}}` no tiene respaldo (player es owner-scoped); solo aplica abriendo
  desde song de banda o contexto de setlist. El proto **omite** controles existentes (Stop,
  Metrónomo, Guardar tono, Imprimir/PDF, navegación de setlist) → **conservarlos** al portar.

### 4.6 Agenda (TÚ, agregada)

- **Propósito:** ensayos y bolos de todas mis bandas en una lista cronológica; confirmar asistencia.
- **Página:** NUEVO `static/agenda.html` (+ `agenda.js`), patrón de `bands.html` pero estrenando
  `design-system.css`.
- **Layout:** `max-width 920px`. (1) H1 "Agenda" + subtítulo. (2) Chips/filtros. (3) Lista
  (gap 12px) de tarjetas de evento: bloque-fecha 50px (dow faint + día 24px), info (título +
  badge banda + badge "Bolo"), botones RSVP a la derecha; borde-izquierdo 3px color de banda.
- **Componentes → `bf-*`:** H1 `.bf-h1`+`.bf-muted`; chips `.bf-tab`/pill; tarjeta `.bf-card`
  (border-left color de banda inline); badge banda `.bf-badge` (color por banda); badge Bolo
  `.bf-badge` acento; RSVP `.bf-btn--sm` (Voy=success, No=danger, Quizás=warning, con `-weak`).
- **Interacciones:** chip filtra (cliente); RSVP → `PUT /bands/{id}/events/{eid}/attendance`;
  tarjeta → detalle.
- **Datos → API:** `GET /bands/` + por cada banda `GET /bands/{id}/events` (mezclar+ordenar en
  cliente por `starts_at`); `PUT .../attendance`.
- **Avisos ⚠️:** **NO hay endpoint agregado** → fan-out N+1 (proponer `GET /me/events`).
  **Gaps:** color por banda no existe (paleta determinística o columna); `EventSummary` NO trae
  `band_name` ni `location` (location está en EventResponse/detalle → ampliar summary o llamar
  detalle); formatear dow/day/time desde `starts_at` en JS; "bolo" = `type=='concert'`. Añadir
  estado vacío. Escapar title/bandName/location.

### 4.7 Finanzas (TÚ, agregada)

- **Propósito:** saldo neto agregado del usuario + saldo por banda (Splitwise personal, solo lectura).
- **Página:** NUEVO `static/finanzas.html` (+ `finanzas.js`).
- **Layout:** `max-width ~920px`. (1) H1 "Finanzas" + subtítulo (código de color). (2) Card
  resumen full-width: cifra neta mono 34px coloreada por signo + icono wallet (acento). (3) Grid
  `auto-fill minmax(260px,1fr)` gap 14px de tarjetas-banda clicables: avatar iniciales + nombre +
  saldo mono 24px coloreado.
- **Componentes → `bf-*`:** card resumen `.bf-card` (cifra `--bf-font-mono` +
  `.bf-amount--positive/--negative`); icono wallet (fondo `--bf-accent-weak`, color `--bf-primary`);
  tarjeta banda `.bf-card.bf-card--interactive`; avatar `.bf-avatar` (color por banda).
- **Interacciones:** tarjeta → finanzas de esa banda; solo lectura/navegación.
- **Datos → API:** `GET /bands/`; por cada banda `GET /bands/{id}/balances` (filtrar
  `participant == mi user_id`); sumar en cliente.
- **Avisos ⚠️:** **NO existe agregado multi-banda** → fan-out N+1 **o** crear `GET /me/balances`
  (recomendado). `BalanceOut` no trae `currency` ni signo precomputado (formato y color en
  cliente). `BandSummary` sin `color` (derivar). user_id desde sesión auth (test_mode = UUID nil).
  Si se crea `/me/balances`, exige test (solo bandas donde soy miembro activo).

### 4.8 Chat (TÚ, agregado) — Chat de banda

- **Propósito:** conversación de la banda en burbujas (propias/ajenas); leer y escribir.
- **Página:** NUEVO `static/chat.html` (+ `chat.js`) **o** (recomendado) pestaña en `bands.html`
  donde el chat YA está cableado en `bands.js`.
- **Layout:** dos columnas `100vh`. **Izquierda 300px:** título "Chat" + lista de conversaciones
  (avatar + nombre/hora + último mensaje + badge no-leídos). **Derecha flex:** cabecera de hilo
  (avatar banda + nombre + "N miembros"), área de mensajes (burbujas L/R, max 72%, avatar
  condicional `showAvatar`, byline), barra inferior input + botón enviar circular.
- **Componentes → `bf-*`:** items `.bf-nav-item`/`.bf-list-item`; avatar `.bf-avatar`; burbuja
  propia `--bf-primary`/`#fff`, ajena `--bf-surface-2/3`/`--bf-text`, radio `--bf-radius-lg`;
  byline `.bf-faint`; input `.bf-input`; enviar `.bf-btn--primary .bf-btn--icon`.
- **Interacciones:** seleccionar hilo; escribir (`onChatInput`/`onChatKey`, Enter envía); enviar
  (`sendMsg` → POST + refresco); auto-scroll al final.
- **Datos → API:** `GET /bands/{id}/messages/` (`?event_id=` opcional); `POST .../messages/`;
  `PATCH .../{mid}` (editar); `DELETE .../{mid}` (borrar); `PATCH .../{mid}/pin` (admin);
  `GET /bands/{id}` + `GET /bands/{id}/members` (cabecera).
- **Avisos ⚠️:** **Gap mayor:** el proto modela INBOX multi-conversación + no-leídos, pero el
  backend tiene **UNA** conversación por banda (+ hilos por evento) y **sin read-state** → colapsar
  la columna izquierda a "General + hilos de eventos" u omitir el concepto DM. `band_id` no viaja
  en la URL del proto → una `chat.html` standalone necesita `?band_id=`. Acciones editar/borrar/pin
  existen en API y faltan en el diseño → añadir menú por burbuja. Tiempo real: empezar con polling
  (`setInterval`); Supabase Realtime después. Aislamiento ya garantizado por `require_band_member`.
  Test e2e + test de aislamiento si se crea `chat.html`.

### 4.9 Perfil (Mi perfil de músico)

- **Propósito:** identidad del músico (nombre, email, avatar), instrumentos y "Mis bandas".
- **Página:** `static/profile.html` (reskin; JS en `profile.js`, ya hace GET/PUT /profile/me).
- **Layout:** `max-width 760px`. (1) H1 "Perfil". (2) Card identidad: avatar circular 76px +
  nombre/email + botón "Editar". (3) Card "Mis instrumentos": chips (icono + nombre) + botón
  dashed "+ Añadir". (4) Card "Mis bandas": filas clicables (mini-avatar cuadrado + nombre/
  instrumento + badge rol).
- **Componentes → `bf-*`:** H1 `.bf-h1`; card identidad `.bf-card`+`.bf-row`; avatar
  `.bf-avatar` (override 76px); botón Editar `.bf-btn` secundario; chip instrumento `.bf-badge`
  acento (variante nueva); botón +Añadir `.bf-btn--ghost` borde dashed; filas `.bf-list-item`/
  `.bf-nav-item`; mini-avatar `.bf-avatar` cuadrado; badge rol `.bf-badge--admin/member/guest`.
- **Interacciones:** Editar → modo edición (display_name, avatar, instruments[]); +Añadir agrega
  instrumento; fila de banda → espacio de banda; guardar `PUT /profile/me` + toast.
- **Datos → API:** `GET /profile/me` (display_name, instruments, avatar); `PUT /profile/me`;
  `GET /bands/` (Mis bandas).
- **Avisos ⚠️:** **Gaps:** email NO está en MusicianProfile → viene de la sesión Supabase
  (`auth.js`); con test_mode no hay email real. `BandSummary` no trae `instrument` ni `color`
  (instrument vive en BandMembership/MusicianProfile, no expuesto en list_my_bands → ampliar;
  color derivar de name). `profile.js` actual edita instrumentos como CSV → reescribir a chips.

### 4.10 Banda · Resumen (dashboard de detalle)

- **Propósito:** identidad de la banda + KPIs (próximo bolo, miembros, repertorio, caja) + próximos eventos.
- **Página:** `static/bands.html` (contenedor `#band-detail`; lógica `bands.js`).
- **Layout:** `max-width 1000px`. (1) Hero 140px gradiente de banda. (2) Cabecera solapada
  (margin-top -44px): avatar cuadrado 84px (borde 4px color app) + nombre H1 + badge rol +
  "{género} · {N} miembros". (3) Grid 4 col gap 13px de KPIs (próximo bolo, miembros, repertorio,
  caja mono coloreada). (4) H2 "Próximos eventos". (5) Filas-evento (bloque fecha + divisor +
  título/meta + badge Bolo).
- **Componentes → `bf-*`:** hero inline (sin token); avatar `.bf-avatar.bf-avatar--lg` (override
  84px cuadrado); badge rol `.bf-badge--{role}`; KPI `.bf-card`; valor caja `--bf-font-mono` +
  success/danger; fila evento `.bf-card`/`.bf-list-item`; badge Bolo `.bf-badge` acento.
- **Interacciones:** KPIs navegables (miembros/repertorio/finanzas/evento); fila evento → detalle;
  se renderiza al seleccionar banda (mostrar `#band-detail`).
- **Datos → API:** `GET /bands/{id}` (identidad); `GET /bands/` (role, member_count);
  `GET /bands/{id}/members`; `GET /bands/{id}/events` (próximos + próximo bolo);
  `GET /bands/{id}/songs` (count); `GET /bands/{id}/balances` o `/transactions` (caja).
- **Avisos ⚠️:** dashboard agregado sin endpoint único → fan-out **o** crear
  `GET /bands/{id}/summary` (recomendado). **Gaps:** BandResponse sin `genre` ni `color`/`gradient`
  (derivar/omitir); `isBolo` de `Event.type` (revisar EventType, p.ej. 'gig'/'concert');
  place/time no en EventSummary; signo de caja desde BalanceOut del participante 'fund'.

### 4.11 Banda · Miembros

- **Propósito:** integrantes con instrumento y rol; el admin invita por enlace.
- **Página:** `static/bands.js` (sección dentro del detalle de banda; host `bands.html`).
- **Layout:** `max-width 820px`. (1) Cabecera: H1 "Miembros" + subtítulo "{n} personas en
  {banda}" + botón primario "Invitar". (2) Card única (lista flush): filas (avatar circular 42px +
  nombre + icono music+instrumento + badge rol).
- **Componentes → `bf-*`:** H1 `.bf-h1`+`.bf-muted`; botón Invitar `.bf-btn .bf-btn--primary`;
  card `.bf-card` (variante **flush** — filas con border-bottom, sin gap → conviene `.bf-list--flush`);
  fila `.bf-list-item`; avatar `.bf-avatar` (color por miembro); badge rol `.bf-badge--{role}`.
- **Interacciones:** Invitar (`generateInvite(bandId)` → `POST /bands/{id}/invites` + enlace
  `join.html?code=...`); mostrar solo si `is_me && role==='admin'`.
- **Datos → API:** `GET /bands/{id}/members` (display_name, role, status, instrument, is_me);
  `GET /bands/{id}` (name); `POST /bands/{id}/invites` (admin); `GET /invites/{code}` +
  `POST /invites/{code}/accept` (en `join.html`).
- **Avisos ⚠️:** mapeo a profile_router/memberships es **incorrecto**: la lista la sirve
  `bands_router` (join a MusicianProfile.display_name). **Gap:** el diseño muestra el INSTRUMENTO
  prominente, pero `list_members` NO rellena `instrument` (campo existe en BandMembershipResponse
  pero ningún endpoint lo escribe; `MusicianProfile.instruments` no se une) → ampliar `list_members`.
  `m.color`/`m.initials` son de frontend. El backend soporta PATCH/DELETE/reactivate de members que
  el diseño omite.

### 4.12 Banda · Agenda

- **Propósito:** agenda de la banda; RSVP por miembro; ver fecha/hora/lugar y setlist asignado.
- **Página:** `static/bands.html` + `bands.js` (función `loadAgenda`, contenedor `#b-agenda`).
- **Layout:** `max-width ~820px`. (1) H1 "Agenda de {banda}". (2) Lista (gap 12px) de tarjetas:
  borde-izq 3px color de banda; fila superior (bloque fecha 48px + título/meta + RSVP); fila
  inferior (border-top) meta setlist (icono list-music + "Setlist asignado · N canciones").
- **Componentes → `bf-*`:** H1 `.bf-h1`; tarjeta `.bf-card` (border-left color banda/`--bf-primary`);
  RSVP `.bf-btn--sm` (Voy=success, Quizás=warning, No=danger con `-weak`; inactivo border
  `--bf-border`); pie setlist border-top `--bf-border` + icono `--bf-primary`; botón crear (admin)
  `.bf-btn--primary`; estado vacío `.bf-muted`.
- **Interacciones:** RSVP → `PUT .../attendance`; admin crear/editar/borrar (`POST`/`PATCH`/`DELETE`
  `.../events`); tarjeta → detalle; meta setlist → setlist asignado.
- **Datos → API:** `GET /bands/{id}/events/` (EventSummary + my_status); `PUT .../attendance`;
  `GET .../events/{eid}` (detalle, location/setlist_id); `POST/PATCH/DELETE .../events`;
  `GET /bands/{id}` (name).
- **Avisos ⚠️:** mapeo CORRECTO (`bands.js` ya tiene `loadAgenda`). **Gaps:** EventSummary NO
  incluye `location` ni conteo de canciones del setlist (ampliar summary con `location` +
  `setlist_song_count`, o GET de detalle por tarjeta). ⚠️ **CORREGIDO:** `Band` **NO** tiene
  `color_tag` (eso es de `Section`, color de sección de canción, `models.py:99`); `Band`
  (`models.py:214`) solo tiene `name/description/avatar_url/currency/created_by`. El acento por
  banda debe **derivarse en cliente** (hash de `band_id` → `--accent` inline, fallback
  `--bf-primary`) o añadir columna+migración. Conservar
  separación próximos/pasados y botón crear que el proto omite. Escapar title/place.

### 4.13 Banda · Repertorio

- **Propósito:** repertorio (canciones autoritativas por band_id) como rejilla; abrir reproductor; añadir.
- **Página:** `static/bands.js` (`loadRepertoire`; hoy lista `<li>`, reescribir a rejilla; host
  `bands.html`).
- **Layout:** `max-width 1000px`. (1) Cabecera: H1 "Repertorio" + subtítulo "Canciones de {banda}"
  + botón "Añadir". (2) Rejilla `auto-fill minmax(250px,1fr)` gap 13px de tarjetas (avatar banda +
  play circular, título, fila mono key/BPM/duración).
- **Componentes → `bf-*`:** botón Añadir `.bf-btn .bf-btn--primary`; rejilla `.bf-grid`; tarjeta
  `.bf-card` (hover `--bf-border-strong`); avatar/icon-tile `.bf-avatar` (fallback
  `--bf-accent-weak`/`--bf-primary`); play `.bf-btn--icon`/`bf-play-fab`; pill key `.bf-badge`
  (`--bf-surface-3`); metadata `--bf-font-mono` `.bf-faint`.
- **Interacciones:** tarjeta/play → `index.html?songId=<id>`; Añadir → crear (`POST`) o copiar
  personal (`POST .../copy`, `copyFromPersonal`); quitar (`DELETE`, existe en repo, no en proto).
- **Datos → API:** `GET /bands/{id}/songs/` (SongSummary); `POST .../songs/`; `POST .../songs/copy`;
  `DELETE .../songs/{sid}`; `GET /songs/{id}` (reproductor); `GET /songs/` (selector de copia).
- **Avisos ⚠️:** **Gaps:** SongSummary sin `key` formateado ni `dur` mm:ss (derivar de
  key_root/key_mode y duration_beats+bpm; ocultar duración si null); color por banda (fallback
  `--bf-accent-weak`/`--bf-primary`). Conservar estados vacío/carga/error y botón quitar del repo.

### 4.14 Banda · Setlist (detalle/orden del bolo)

- **Propósito:** orden de canciones de un setlist; reordenar arrastrando; añadir del repertorio.
- **Página:** `static/bands.js` — sección Setlists. Hoy solo lista setlists + editor de creación;
  el **detalle con drag-and-drop es NUEVO** (añadir `openBandSetlist`); host `bands.html`.
- **Layout:** `max-width 680px`. (1) Cabecera: H1 "Setlist · {nombre}" + contador mono
  (`{{setlistTotal}}`). (2) Ayuda "Arrastra para reordenar". (3) Card-lista (radio 14px, overflow
  hidden) con filas (handle grip + nº orden mono + título + badge key + duración). (4) Botón
  full-width dashed "Añadir canción".
- **Componentes → `bf-*`:** cabecera `.bf-row--between` + `.bf-h1`; contador `.bf-faint` mono;
  card `.bf-card`/`.bf-list`; fila `.bf-list-item` (border-bottom); handle `.bf-faint` (cursor grab);
  badge key `.bf-badge`; botón añadir `.bf-btn--ghost` full-width borde dashed.
- **Interacciones:** drag handle → reordenar → `PATCH .../setlists/{id}` con `{song_ids:[...]}`
  (reemplaza lista completa); Añadir → selector repertorio → mismo PATCH.
- **Datos → API:** `GET /bands/{id}/setlists/{sid}` (items[]: song_id, position, title, artist,
  bpm, note); `PATCH .../setlists/{id}` (`song_ids`); `GET /bands/{id}/songs` (selector);
  `GET /setlists/{id}` (reusado por el reproductor).
- **Avisos ⚠️:** **Gaps:** SetlistItemOut NO tiene `key` ni `duración` (`{{x.key}}`/`{{x.dur}}` sin
  origen → mostrar bpm/note o ampliar modelo); `setlistTotal` se calcula en cliente (items.length;
  duración total no calculable sin dato). Detalle drag-and-drop es nuevo. Ocultar handle/Añadir a
  `guest` (`_deny_guests` → 403; `bands.js` ya tiene `iAmGuest`/`canEdit`). Icono `grip-vertical`.

### 4.15 Banda · Finanzas

- **Propósito:** caja común + saldos por miembro (Splitwise) + movimientos; admin registra/liquida.
- **Página:** `static/bands.js` (`loadFinance` en `#b-finance`; modales `newTransaction`/
  `newSettlement`; host `bands.html`). YA implementado parcialmente (en `style.css`, no `bf-*`).
- **Layout:** `max-width 920px`. (1) Cabecera: H1 "Finanzas de la banda" + subtítulo; botones
  "Liquidar" (secundario) + "Registrar" (primario). (2) Grid 2 col (1fr/1.2fr, gap 18px): izquierda
  card "Caja de la banda" (cifra mono 28px) + card "Saldo por miembro" (filas avatar/nombre/importe);
  derecha card "Movimientos" (filas icono tipo + descripción + meta autor·fecha + importe).
- **Componentes → `bf-*`:** cabecera `.bf-row--between` + `.bf-h1`; Liquidar `.bf-btn` secundario;
  Registrar `.bf-btn--primary`; cards `.bf-card`; cifras `--bf-font-mono` + `.bf-amount--positive/
  --negative`; filas `.bf-list-item`; avatar `.bf-avatar`; icono movimiento chip 34px
  (`--bf-success-weak`/`--bf-danger-weak`).
- **Interacciones:** Registrar → modal → `POST .../transactions` (admin); Liquidar → modal →
  `POST .../settlements` (admin); borrar → `DELETE .../transactions/{tid}` (soft, admin); recargar
  `loadFinance`; ocultar acciones a no-admin.
- **Datos → API:** `GET .../balances` (BalanceOut; is_fund=true → caja, false → miembros);
  `GET .../transactions` (TransactionSummary); `POST .../transactions`; `POST .../settlements`;
  `DELETE .../transactions/{tx_id}`; (`GET/DELETE .../settlements` existen, sin UI aún).
- **Avisos ⚠️:** YA existe UI funcional en `style.css` → reescribir a `bf-*`. **Gaps:** card "Caja"
  (KPI del fondo) no se muestra hoy (derivar de BalanceOut is_fund=true, sin endpoint nuevo); la
  fila de movimiento pide autor (`{{m.by}}`) pero **TransactionSummary NO expone `created_by`** ni
  nombre de autor → exponer created_by+display_name o GET por fila (caro). Importes mono, formato
  euros locale es-ES. Ocultar acciones admin a no-admin (backend ya valida `require_band_admin`).

### 4.16 Banda · Chat

- **Propósito:** chat de la banda en burbujas messenger (propias derecha, ajenas izquierda).
- **Página:** `static/bands.js` (`loadChat`/`initChat` en `#b-chat`; host `bands.html`). YA
  implementado como lista plana → rediseño visual a burbujas.
- **Layout:** `100vh` columna 3 regiones. (1) Cabecera: avatar banda 36px + nombre + "N miembros".
  (2) Cuerpo scrollable (gap 12px): burbujas con `align-self` por autor (max 72%), avatar circular
  28px condicional (`showAvatar`), byline. (3) Barra: input + botón enviar 44px.
- **Componentes → `bf-*`:** avatar banda `.bf-avatar` (color dinámico); burbuja propia
  `--bf-primary`/`#fff`, ajena `--bf-surface-2/3`/`--bf-text`; byline `.bf-faint`; input `.bf-input`;
  enviar `.bf-btn--primary .bf-btn--icon`; estado vacío `.bf-faint`.
- **Interacciones:** `onChatInput`/`onChatKey` (Enter envía); `sendMsg` (POST + refresco); autoscroll;
  pin/borrar/editar (en API y repo, no en el fragment → conservar); refresco `setInterval`.
- **Datos → API:** `GET .../messages/` (`?event_id=`); `POST .../messages/`; `PATCH .../{mid}`;
  `DELETE .../{mid}`; `PATCH .../{mid}/pin` (admin); `GET /bands/{id}` + miembros (cabecera).
- **Avisos ⚠️:** mapeo CORRECTO y ya implementado (rediseño, no integración nueva). Decidir embebido
  (recomendado) vs vista dedicada. `m.align`/`showAvatar`/`bubbleBg` se derivan en JS (is_mine →
  lado; comparar autor consecutivo → showAvatar). `MessageOut` **sí** trae `author_id`
  (`schemas.py:490`) e `is_mine` (`schemas.py:496`) — usar esos directamente. Conservar pin/borrar/editar.
  Subtítulo "N miembros": reutilizar dato ya cargado, no llamada nueva.

### 4.17 Banda · Ajustes

- **Propósito:** config de banda para admin: editar datos básicos + zona peligrosa (eliminar banda).
- **Página:** `static/bands.js` — **NUEVO** `openBandSettings(id)` en `#band-detail`; host
  `bands.html`. Hoy NO existe subvista de ajustes ni botón eliminar.
- **Layout:** `max-width 680px`. (1) H1 "Ajustes de la banda". (2) Card datos básicos: label+input
  "Nombre", label+input "Género". (3) Card **"Zona peligrosa"** (borde rojo): título rojo + aviso +
  botón rojo "Eliminar banda".
- **Componentes → `bf-*`:** H1 `.bf-h1`; cards `.bf-card` (zona peligrosa: override border
  `--bf-danger`/`--bf-danger-weak`); label `.bf-label`; inputs `.bf-input`; aviso `.bf-muted`; botón
  eliminar `.bf-btn .bf-btn--danger`.
- **Interacciones:** editar Nombre → `PATCH /bands/{id}` `{name}` (on blur o botón Guardar); editar
  Género → ⚠️ sin backend; Eliminar → `confirmModal` → `DELETE /bands/{id}` (soft, 204) → `loadBands`;
  solo admin (`iAmAdmin`).
- **Datos → API:** `PATCH /bands/{id}` (name, description, avatar_url — confirmado, admin);
  `DELETE /bands/{id}` (soft, admin); `GET /bands/{id}` (precargar).
- **Avisos ⚠️:** **Gap:** `genre` NO existe en el modelo Band ni schemas → mapear input a
  `description` (reusar PATCH) **o** añadir columna `genre` + migración Alembic + 3 schemas
  (BandCreate/Update/Response); sin eso el input no persiste. Subvista de ajustes y botón eliminar
  son NUEVOS. Eliminar SIEMPRE tras `confirmModal` y solo admin. Recomendable botón "Guardar cambios"
  explícito (`.bf-btn--primary`).

---

## 5. Tabla-resumen: pantalla → página static → router(s) API → tarea

| # | Pantalla | Página `static/` | Router(s) API | Tarea roadmap |
|---|---|---|---|---|
| 0 | Tokens / design-system | `design-system.css` | — | **T-073** (base, hecha) |
| — | App shell | NUEVO `shell.js`/`app.html` (+`shell.css`) | `bands_router`, `profile_router`, `config` | **T-074** |
| 4.1 | Login / Registro | `login.html` | Supabase (`auth.js`) + `GET /config` | T-081 (reskin) |
| 4.2 | Inicio / Dashboard (TÚ) | NUEVO `inicio.html` (+`inicio.js`) | `bands`, `events`, `messages`, `finance`, `songs`, `profile` (fan-out) | T-076 |
| 4.3 | Biblioteca (TÚ) | `library.html` | `songs_router`, `bands_router`, `band_songs_router` | T-081 |
| 4.4 | Bandas (lista) | `bands.html` (+`bands.js`) | `bands_router` | **T-075** |
| 4.5 | Reproductor (joya) | `index.html` | `songs_router`, `setlists_router` | T-081 (solo chrome) |
| 4.6 | Agenda (TÚ, agregada) | NUEVO `agenda.html` (+`agenda.js`) | `bands_router`, `events_router` (fan-out) | T-077 |
| 4.7 | Finanzas (TÚ, agregada) | NUEVO `finanzas.html` (+`finanzas.js`) | `bands_router`, `finance_router` (fan-out) | T-078 |
| 4.8 | Chat (TÚ, agregado) | NUEVO `chat.html` o pestaña `bands.html` | `messages_router`, `bands_router` | T-079 |
| 4.9 | Perfil | `profile.html` (+`profile.js`) | `profile_router`, `bands_router` | T-080 |
| 4.10 | Banda · Resumen | `bands.html` (`#band-detail`, `bands.js`) | `bands`, `events`, `band_songs`, `finance` | **T-075** |
| 4.11 | Banda · Miembros | `bands.js` (`bands.html`) | `bands_router`, `invites_router` | **T-075** |
| 4.12 | Banda · Agenda | `bands.html` (`#b-agenda`, `bands.js`) | `events_router`, `band_setlists_router` | **T-075** |
| 4.13 | Banda · Repertorio | `bands.js` (`loadRepertoire`, `bands.html`) | `band_songs_router`, `songs_router` | **T-075** |
| 4.14 | Banda · Setlist (detalle) | `bands.js` (NUEVO `openBandSetlist`, `bands.html`) | `band_setlists_router`, `band_songs_router` | **T-075** |
| 4.15 | Banda · Finanzas | `bands.js` (`#b-finance`, `bands.html`) | `finance_router` (+ `balances.py`) | **T-075** |
| 4.16 | Banda · Chat | `bands.js` (`#b-chat`, `bands.html`) | `messages_router`, `bands_router` | **T-075** |
| 4.17 | Banda · Ajustes | `bands.js` (NUEVO `openBandSettings`, `bands.html`) | `bands_router` | **T-075** / T-082 |

> Mapeo tarea↔pantalla orientativo (T-074…T-082 = app shell + 1 vista por área); ajustar a
> `harness/ROADMAP.md`/`TASKS.md` al abrir cada tarea. Las pantallas de banda (4.10–4.17) son
> sub-secciones del espacio de banda y caen bajo el bloque de detalle de banda (T-075).

---

## 6. Catálogo de gaps de backend (resumen accionable)

⚠️ Datos que el diseño pide y el backend aún **no** da:

1. **Color/branding por banda** (`color`/`gradient`): NO existe en el modelo Band. Derivar en
   cliente (hash de `band_id`) **o** añadir columna + migración Alembic + schemas. (Afecta 4.2,
   4.4, 4.6, 4.7, 4.10, 4.11, 4.13, shell, **y también 4.12 Banda·Agenda** — sin excepción.)
   ⚠️ **NO confundir con `Section.color_tag`** (`models.py:99`): ese es el color de una sección de
   canción, no de la banda. `Band` (`models.py:214`) no tiene `color_tag`.
2. **Género de banda** (`genre`): NO existe en Band/BandResponse. Mapear a `description` o añadir
   columna+migración. (Afecta 4.4, 4.10, 4.17, shell.)
3. **Endpoints agregados cross-band**: NO existen `GET /me/dashboard`, `/me/events`, `/me/balances`,
   `/bands/{id}/summary`. Hoy → fan-out N+1 en cliente; recomendable crearlos. (Afecta 4.2, 4.6,
   4.7, 4.10.)
4. **Read-state / conteo de no-leídos** en mensajes: NO existe (messages_router solo lista/crea).
   Omitir badge o añadir tabla de lecturas. (Afecta shell `n.badge`, 4.2 `c.unread`, 4.8.)
5. **`instrument` de miembro** en `list_members`/`BandSummary`: el campo existe en
   BandMembershipResponse pero ningún endpoint lo rellena; `MusicianProfile.instruments` no se une.
   Ampliar `list_members`/BandSummary. (Afecta 4.4, 4.9, 4.11.)
6. **`location` en EventSummary**: solo está en EventResponse/detalle → ampliar summary o llamar
   detalle por tarjeta. (Afecta 4.6, 4.12.)
7. **Conteo de canciones del setlist en evento** (`setlist_song_count`): no expuesto. (4.12.)
8. **`key` formateado / `dur` (mm:ss)** en SongSummary y SetlistItemOut: no existen; derivar de
   key_root/key_mode + duration_beats/bpm (puede ser null). (Afecta 4.3, 4.13, 4.14.)
9. **Flag "tiene partitura"** en SongSummary: no existe; aproximar `section_count>0`. (4.3.)
10. **`created_by`/autor en TransactionSummary**: no expuesto → la fila de movimiento no puede
    mostrar autor sin ampliar el schema o GET por fila. (4.15.)
11. **Nombre de banda en el reproductor** (`player.band`): player es owner-scoped; solo aplica
    abriendo desde song de banda o contexto de setlist. (4.5.)
12. **Email del usuario**: no está en MusicianProfile; viene de la sesión Supabase (no del
    backend). (4.9.)
13. **Flujo "olvidé contraseña"**: sin `resetPasswordForEmail` en `auth.js`. (4.1.)
14. **Lista de conversaciones / inbox multi-conversación**: el backend tiene 1 chat por banda +
    hilos por evento, no DM. (4.8.)
