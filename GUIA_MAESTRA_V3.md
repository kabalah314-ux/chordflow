# 🎸 BandFlow — Guía Maestra V3

> ## ⚠️ HISTORIAL CERRADO — no es la guía vigente (desde 2026-07-03)
> La guía vigente es **[GUIA_MAESTRA_V5.md](GUIA_MAESTRA_V5.md)** (pulido integral, giro de la
> magnitud V2→V3: redefine la app sección a sección). **Todo lo pendiente de esta V3 está
> absorbido y re-ubicado en la V5 §0.2** (tabla de herencia): F6→post-V5, F7-resto→V5 §5/§2,
> F8→V5 §5.6/§10, F10→V5 §5, F11→post-V5. Este archivo se conserva para consultar el detalle de
> las decisiones D1–D9 y de las fases ya implementadas.
>
> **Borrador vivo · creado 2026-06-17.** Dirección de producto de la **V3**: el salto de
> "SaaS aislado de gestión de banda" a **"red musical con un plano público opt-in"**.
> Companion de [GUIA_MAESTRA_V2.md](GUIA_MAESTRA_V2.md) +
> [GUIA_MAESTRA_V2_FUNCIONAL.md](GUIA_MAESTRA_V2_FUNCIONAL.md) (V2 = Fases 7–13, **en producción**).
> Esta V3 es lo que viene **después** de la Fase 13. **Todo aditivo; la V2 no se toca.**
>
> Origen: 3 ideas de Oscar (visión global · ensayo sincronizado · diseño profesional) + un
> catálogo de "siguiente nivel", profundizado por un análisis multiagente (2026-06-17) y
> **pulido punto por punto** con Oscar → **8 decisiones de fondo cerradas (D1–D8)**.

---

## 0. El giro de la V3 en una frase

De **"SaaS aislado de gestión interna de banda"** a **"red musical con un plano público opt-in:
tu banda gestiona en privado, pero puede publicar repertorio, perfil y conciertos al mundo —
y descubrir a otras"**.

**Tensión central:** abrir datos al exterior (biblioteca global, directorio de bandas, página
pública, fans) **sin romper jamás el aislamiento multi-tenant** (la regla de oro de la V2). Todo
lo demás cuelga de cómo se resuelva esa tensión → ver §1.

---

## ✅ Decisiones cerradas (D1–D8)

| # | Decisión | Detalle |
|---|---|---|
| **D1** | **Plano público híbrido** | *Interruptor* `visibility` (`private`/`unlisted`/`public`) para perfil/eventos/EPK **+** *escaparate-copia* (`PublicScore`) para la biblioteca de canciones. Lo privado y lo público **nunca comparten tabla** en lo sensible. |
| **D2** | **Biblioteca: acordes + letra recortada** | El catálogo público muestra acordes + estructura + **letra parcial/recortada**; la letra completa solo en tu copia privada al importar. Mínimo legalmente defendible. |
| **D3** | **Red acotada primero** | v1: perfiles públicos + bolsa de colaboraciones. **Sin mensajería directa abierta** hasta tener capacidad de moderación. |
| **D4** | **Giras tempranas** | Módulo `Tour` aislado y de bajo riesgo, en fase temprana. Co-organización con otra banda en v1 = **solo informativa** (read-only). |
| **D5** | **Ensayo sync v1 = visual + metrónomo** | Sincronía visual perfecta + metrónomo común (clic del director). **Pista de audio común → v2** (depende de Storage). |
| **D6** | **Sala de ensayo efímera** | Sin histórico en v1. La entidad `RehearsalSession` con histórico se difiere. |
| **D7** | **Lucide + marca ligera** | Iconos SVG (Lucide) + quick wins de CSS ahora. Marca a fondo (logo formal, OG, splash) junto a la landing pública. |
| **D8** | **Andamiaje de planes, sin cobrar** | `Band.plan` (Free/Pro) + contadores desde ya, **sin cobro**. Joya + biblioteca comunitaria **gratis para siempre**; se cobrará la gestión avanzada. |
| **D9** | **Biblioteca global = reclamo, contribución por DEFECTO (no opt-in)** | El catálogo global es **el gancho de marketing** de la app: un buscador de **muchos artistas** que crece poco a poco con lo que sube la gente. Al **añadir una canción** (crear o importar de una URL), **se sube al catálogo global por defecto** ("¿no la encuentras? ponla aquí"); el usuario obtiene además su copia para usar/arreglar. Sustituye al "publicar opt-in" de D1 **para canciones** (el `visibility` opt-in sigue para perfiles/eventos). Se mantiene **D2** (acordes + letra recortada en el catálogo público; letra completa al importar). El **plano privado** (arreglos, notas, setlists, finanzas de la banda) sigue intacto y privado. |

**Apuntes técnicos derivados (se aplican por defecto):**
- **RLS de Postgres** como 2ª barrera antes de abrir nada público. ⚠️ *Verificar primero cómo
  conecta el backend* (si usa `service_role`, RLS se ignora → replantear).
- **Rol "usuario-fan"** (cuenta sin banda) solo al llegar a la página pública/fans → revisar los
  guards del shell (hoy se asume "todo usuario tiene banda").
- Ensayo: **reloj de servidor** (`/clock`, estilo NTP) + **tap** para marcar secciones +
  **metrónomo reescrito al patrón *lookahead*** (Web Audio).

---

## 1. La decisión arquitectónica que lo condiciona todo

**Hoy:** cada dato vive bajo un `band_id` y ninguna ruta lo deja salir. La regla de oro garantiza
que **nada se comparte entre bandas ni es público**.

**La V3 introduce un tercer plano: el público/global.** Principio rector (**D1**):

> **Privado por defecto · público por acción explícita · nunca por referencia directa al dato privado.**

Dos mecanismos, **combinados según el caso** (D1):

- **(A) Eje `visibility`** (`private`|`unlisted`|`public`, default `private`) en `Band`, `Event`,
  `MusicianProfile`, EPK. Las rutas privadas **no cambian**; se añaden rutas `/public/...`
  separadas que **solo** sirven filas `public`. → perfil de banda, eventos públicos, directorio,
  fans, compartir por enlace.
- **(B) Publicar = COPIAR a un espacio separado** (no marcar la fila privada). **Obligatorio para
  la biblioteca global:** el catálogo es un **espacio de datos nuevo** (`PublicScore`), no
  "canciones de banda marcadas públicas" (eso obliga a colar `OR is_public=true` en queries que
  hoy filtran estricto → la causa de fugas). Importar de vuelta = copia profunda a tu banda →
  vuelves al plano aislado.

**Reglas duras (no negociables):**
1. **Finanzas, chat, asistencia, repertorio completo, ensayos, notas internas, contactos →
   SIEMPRE privados.** Nunca publicables.
2. **Para canciones (D9): contribuir al catálogo global es el flujo POR DEFECTO** (el reclamo de la
   app), no un opt-in. Para **perfiles/eventos/EPK** sí se mantiene el opt-in explícito y reversible.
3. **Cada ruta/canal público necesita su PROPIO test** ("fila `private` jamás aparece en
   `/public`", "no-participante → 403", "perfil despublicado → 404").
4. **Segundo eje de autorización** (participante-de-hilo, seguidor, visitante anónimo) que
   **convive** con el multi-tenant, no lo reemplaza.
5. **RLS como defensa en profundidad** antes de abrir nada (ver apunte técnico de D1).

> `is_public` actual (hoy muerto en `Song`): **no** reutilizarlo como interruptor del catálogo. A
> lo sumo, puntero de UI ("esta canción tiene una publicación asociada").

---

## 2. Ideas de Oscar, profundizadas

### 2.1 Visión global — Biblioteca global (el RECLAMO de la app, D9)

**Qué es.** El **gancho de marketing** de BandFlow: un **buscador de un catálogo de muchos artistas**
que **crece poco a poco** con lo que sube la gente. El mensaje al usuario es directo: *"busca tu
canción; ¿no está? **ponla aquí**"* — y al añadirla, **se sube al catálogo global por defecto** (no
es un opt-in: es el flujo normal, D9). Catálogo de partituras (acordes + estructura) buscable,
valorable y comentable, con la joya (teleprompter) como visor.

**El bucle de crecimiento (lo importante).**
1. El usuario **busca** un artista/canción en la biblioteca global.
2. **Si está** → la abre / la **importa a su banda** en 1 clic (con la letra completa).
3. **Si NO está** → "**Añádela**" → crea la canción (a mano o **importando de una URL** con la IA que
   ya existe) y **automáticamente pasa a formar parte del catálogo global** para todos.
   → cada usuario que busca y no encuentra **alimenta** el catálogo → más contenido → más usuarios.

**Valor.** Invierte el motor de adquisición: hoy la gestión retiene; **el catálogo atrae** (SEO de
cola larga: una página por canción/artista). Cuantas más bandas lo usan, mejor la biblioteca para
todas — efecto red puro, y la razón para entrar en la app aunque aún no tengas banda.

**Privacidad y derechos (se mantienen).** Lo que sube al catálogo es la **canción** (acordes +
estructura + **letra recortada** en la vista pública, D2; completa al importar). El **plano privado**
de la banda (arreglos propios, notas de ensayo, estado, setlists, finanzas) **sigue privado** y nunca
entra al catálogo. La canción del catálogo es un **snapshot independiente** (copia desacoplada, D1):
publicar/contribuir **no** expone datos internos de la banda.

**Modelo de datos (aditivo, copia desacoplada — D1/D2):**
- `MusicalWork` — la canción abstracta. `norm_title`, `norm_artist`, `UNIQUE(norm_artist,
  norm_title)`. Agrupa N versiones.
- `PublicScore` — una versión publicada. `work_id`, metadatos copiados, `publisher_id →
  MusicianProfile` (atribución), `source_band_id` (auditoría, **nunca** expuesto), `content_json`
  (snapshot inmutable; `score_render.js` ya lo pinta), **letra recortada** (D2), `content_hash`
  (dedupe), `status` (draft/published/hidden/removed), `rating_avg/count`, `import_count`.
- Sociales: `ScoreRating` (UNIQUE por usuario), `ScoreComment` (1 nivel, escapado XSS),
  `ScoreFlag` (notice-and-takedown), votos con UNIQUE anti-inflado.
- Reputación del publicador: **derivada** (vista agregada), no tabla nueva.

**UX.** Botón "Publicar al catálogo" en la canción (1 confirmación). Buscador `/catalog/search`
(título/artista normalizado + filtros key/género/dificultad/bpm, navegable sin login). Ficha de
obra con sus N versiones. "Importar a mi banda" en 1 clic.

**Encaje.** Dirección **nueva y transversal**. Reutiliza `_deep_copy_song` y `content_json`.

**Esfuerzo.** Núcleo (publicar+buscar+importar+rating): **medio**. Moderación/antiabuso: **alto**.
Decisión legal de letras: resuelta en **D2** (letra recortada en público).

**Decisiones menores abiertas.** Snapshot inmutable (rec.) vs editable. `content_json` (rec. v1)
vs tablas espejo.

### 2.2 Visión global — Red de bandas y colaboraciones

> La **gestión de giras** se trata aparte en §4 (es aislada y de bajo riesgo, a diferencia de la red).

**Qué es (acotado por D3).** Directorio público buscable de bandas y músicos (ciudad/género/
disponibilidad) + bolsa de colaboraciones ("busco batería sustituto", "busco banda para compartir
cartel"). **Sin DM abierto en v1.**

**Modelo de datos:**
- `Band.is_public` + `public_slug` (único) + `published_at` (opt-in del admin). El directorio es
  una **vista sobre los EPK publicados** (Fase 16), no entidad nueva.
- `MusicianProfile.is_public` + `available_for` (`["sustituto","sesión","refuerzo","miembro"]`) —
  el músico se publica **por decisión propia**, independiente de sus bandas.
- `CollabPost` (anuncio público: `kind`, `instrument`, `genre`, `city`, `expires_at`, soft-delete).
- **Diferido (cuando haya moderación):** `DirectThread`/`DirectMessage` (canal 1-a-1 fuera del
  tenant, 1ª mensaje = solicitud), `Block`, `Report`.

**Encaje.** Dirección **nueva**, dependiente de la **Fase 16 (EPK)**. Introduce el rol fan y el
2º eje de auth.

**Esfuerzo.** Directorio + EPK público + `CollabPost`: **medio**. (Mensajería + moderación: alto,
diferido.)

**Riesgo.** RGPD al publicar datos de personas (app en UE) → consentimiento estricto + derecho a
borrar.

### 2.3 Ensayo sincronizado (local de ensayo)

**Qué es.** Llevar la joya de "un músico, una pantalla" a "una banda, N pantallas con un director":
el director controla play/stop/seek/tempo y todas las pantallas siguen sincronizadas (teleprompter
+ bolita + metrónomo común). **No rompe el aislamiento** (la sala = `band_id` + canción; todos ya
son miembros).

**El corazón NO es la red — es el dato de tiempos.** Hoy no sabemos *cuánto dura cada sección*; sin
eso, la bolita no tiene sobre qué deslizarse. Pieza central = **mapa de arrangement**:
- `ArrangementMap` (cuelga de `Song` → ya filtra por `band_id`): `name`, `source` (tap|bars|auto),
  `base_bpm`, `is_default`.
- `ArrangementSegment`: `section_ref` (apunta a la `Section` existente, **no duplica** contenido),
  `start_ms`, `duration_ms`, `bpm` (cambios de tempo por sección).
- Modo **"Aprender la estructura"**: **tap** (el director pulsa al entrar cada sección — rec.),
  **por compases** (preciso), **reparto automático** (fallback desde `duration_seconds`).

**Roles en la sala:** un **director** (autoridad única de la línea de tiempo, batuta traspasable) +
**seguidores** (todo lo local: volumen, transposición por ids, tamaño). Sala de espera ("3 de 4
listos"), reconexión en caliente, control remoto desde el móvil del director, wake-lock.

**Audio (D5).** v1 = metrónomo + teleprompter. YouTube (`reference_url`) solo como referencia
emitida por el director por los altavoces del local (no sincronía perfecta — ToS/buffering).
**Pista de audio fiable = v2, depende de Storage (Fase 15).**

#### 🔧 Veredicto técnico de viabilidad
- **`sync_engine.js` YA es del tipo correcto** (timestamp + BPM, deriva la posición de un reloj).
  Solo falta que ese reloj sea **común** entre dispositivos. → reaprovechable casi entero.
- **El metrónomo NO sirve tal cual:** hoy suena reactivo (jitter ~16ms). Hay que **reescribirlo al
  patrón *lookahead*** (Web Audio agendando al futuro). Es el grueso del trabajo nuevo — y mejora
  también el modo solitario.
- **Vercel es serverless → no hay WebSocket propio.** Transporte: **Supabase Realtime Broadcast**
  (ya disponible, cero infra nueva) + endpoint `/clock` trivial (Cristian/NTP). La latencia del
  transporte casi no importa (se envía "empieza en T0", no cada beat).
- **Cuello de botella real:** la latencia de salida de audio de cada móvil (20–150ms), no la red.

**Qué se promete (D5):**
- **v1:** ✅ sincronía **visual** excelente (<30ms percibidos) + metrónomo común "suficiente" (clic
  del altavoz del director). ❌ NO clic perfectamente simultáneo en N altavoces ni tocar contra
  pista. ⚠️ Canal namespaced por `band_id` con autorización → **test de aislamiento del canal**.
- **v2:** pista propia (`.mp3` de Storage) en `AudioBuffer` agendada sobre el reloj común.

**Encaje.** Empezar por el **mapa de arrangement + bolita en modo SOLITARIO** (sin red, mejora la
joya para todos), y construir la sala encima.

**Esfuerzo.** Mapa + bolita solitario: **medio**. Sala + metrónomo lookahead: **medio-alto**.
Audio propio: **alto** (atado a Fase 15).

### 2.4 Diseño profesional (D7)

**Qué es.** Subir BandFlow a nivel "producto" **sin framework** — el `design-system.css` ya es
bueno (tokens, dark/light, prefijo `bf-`). Se **rellenan huecos** y se **conecta la joya** a los
mismos tokens.

**Tres deudas concretas:**
1. **Iconografía por emoji** → lo más "amateur". Cambiar a **SVG (Lucide)**, sprite `currentColor`
   = quick win nº1.
2. **El player (`style.css`) vive fuera de los tokens `bf-*`** → la joya no comparte identidad.
   Unificar = coherencia instantánea.
3. **Faltan estados** (`:disabled`, loading, empty, skeleton) → es lo que separa un demo de un
   producto.

**Quick wins priorizados:** estados `:disabled`/`[data-loading]`; iconos SVG Lucide; empty states
`.bf-empty`; skeletons (reusa `bf-pulse`); toasts `aria-live`; números en mono; focus-visible
global + audit AA; modal nativo `<dialog>`; stat cards en el dashboard "TÚ"; avatares con
iniciales+color por hash. **Pieza estrella: teleprompter espectacular** (tokens + acorde activo con
glow/scale + modo escenario/fullscreen + máscara de foco) — solo CSS, con test de que el render no
cambia.

**Encaje.** **No es dirección nueva: fase de pulido transversal**, ANTES de las fases públicas.
Marca a fondo (logo, OG, splash) → diferida a la landing pública (D7).

**Esfuerzo.** Quick wins: **bajo**. Componentes nuevos: bajo-medio. Teleprompter: medio.

---

## 3. Siguiente nivel (catálogo priorizado)

**Lente:** M=músico · R=red · T=técnico/IA · $=monetización.

| Idea | Lente | Impacto | Esfuerzo | Prerequisito | Encaje |
|---|---|---|---|---|---|
| **Storage real (Supabase) + entidad `Asset`** | T/$ | Muy alto | Medio | RLS band_id | **Fase 15 — adelantar** |
| **Supabase Realtime** (canales por band_id) | T | Muy alto | Medio | Auth band_id | Dirección nueva transversal |
| **Modo Directo / concierto a prueba de fallos** | M | Muy alto | Bajo-medio | — | Extiende la joya |
| **Pedalera Bluetooth / teclado (page turner)** | M | Alto | Bajo | — | Extiende la joya |
| **Vídeo de referencia (YouTube) sincronizado** | M/$ | Muy alto | Medio | — | Extiende la joya |
| **Afinador integrado** (Web Audio + YIN) | M | Alto | Medio | — | Extiende la joya, lee `tuning` |
| **Onboarding viral por invitación** | R | Alto | Bajo | — | Endurece Fases 7–13 |
| **Compartir por enlace `unlisted`** | R | Medio-alto | Bajo | eje `visibility` | **Primer efecto red, hacer pronto** |
| **oEmbed de enlaces** (carátula al pegar URL) | R | Medio-alto | Bajo | — | Extiende repertorio/EPK |
| **Implementar `Notification` + Web Push** | M/T | Alto | Medio-alto | sw.js + VAPID | Completa entidad ya diseñada |
| **IA: autodetección tono/BPM (client-side)** | T/M | Alto | Medio | — | Extiende alta de canción |
| **Setlist por duración/energía** (v1 sin IA) | M | Alto | Bajo | — | Extiende setlists |
| **Loop A-B + tempo trainer** | M | Alto | Medio | — | Extiende sync_engine |
| **Vista por rol/instrumento del tema** | M | Medio-alto | Medio | — | Extiende score_render |
| **"Estado de preparación" por miembro** | M | Medio-alto | Medio | test aislamiento | Extiende repertorio |
| **RSVP gratis en eventos públicos** | R/$ | Muy alto | Bajo | `visibility` + rol fan | Fases 14/17 |
| **Asistente/chatbot RAG sobre la banda** | T | Alto | Medio | tool-calling filtrado | Reaprovecha OpenRouter |
| **`Band.plan` (Free/Pro) + contador IA** | $ | Alto | Bajo-medio | — | **D8 — andamiaje ya** |
| **IA: transcripción audio → acordes** | T/M | Muy alto | Alto | Storage + worker no-serverless | Dirección nueva |
| **Test de aislamiento parametrizado** (gate CI) | T | Alto | Bajo-medio | — | Extiende el harness |

---

## 4. Gestión de giras (nuevo de cero)

**No existía en las guías previas** (solo una etiqueta diferida de "presupuesto de gira"). Aquí se
diseña de cero — y, a diferencia de la red, **encaja limpio y aislado** → fase temprana (D4).

Una **gira (`Tour`)** es una colección **ordenada** de paradas (`TourStop`), cada una vinculada a
un `Event(type=concert)` **ya existente**: la gira **no duplica** Agenda ni Finanzas, las **agrega
y enriquece** (ruta + mapa Leaflet/OSM sin API key, presupuesto previsto-vs-real, logística entre
fechas, checklist por parada). El presupuesto (`TourBudgetLine`) es **estimación**; cuando un gasto
ocurre, se crea una `Transaction`+`TransactionSplit` normal y se **enlaza** → `balances.py`
intacto. Materializa el "presupuesto de gira" diferido. Conecta con **Booking (Fase 14)** (cada
parada muestra el `Event.status` del pipeline) y con la **red** (`CollabPost kind=busca_gira`).
**Co-organización con otra banda (D4):** v1 = **informativa** (resumen read-only, cada banda
gestiona su copia, aislamiento intacto); el tour compartido real (2º eje de auth) se difiere.
**Esfuerzo: medio, riesgo arquitectónico bajo.**

---

## 5. Encaje con el roadmap actual (Fases 14–21)

**EXTIENDEN fases ya planificadas:**
- **Storage (Fase 15)** → prerrequisito de audio propio, grabadora, transcripción IA,
  fotos/EPK/merch. **Conviene adelantarla.**
- **EPK (Fase 16)** → cara pública que reutilizan directorio y página pública.
- **Booking (Fase 14)** → las giras agregan su pipeline; RSVP se apoya aquí.
- **Página pública + Fans (Fase 17)** → perfil indexable (SEO), seguir, RSVP. El pulido de diseño
  debe ir **antes**.

**Abren DIRECCIÓN NUEVA:**
- **Capa global/pública** (D1) → prerrequisito de biblioteca global, directorio, fans.
- **Red social acotada** (D3) → prerrequisito Fase 16 + rol fan.
- **Ensayo sincronizado** → prerrequisito Realtime + `/clock` + metrónomo lookahead. (El mapa de
  arrangement no necesita tiempo real.)
- **Gestión de giras** (§4) → aislada, módulo nuevo.
- **Monetización** (`Band.plan`, D8) → andamiaje nuevo.

---

## 6. Orden de fases de la V3 (afinado con D1–D8)

> **V3-F1 → V3-F11.** El detalle T-NNN se abre en `harness/ROADMAP.md` al aprobar cada fase.

1. **V3-F1 · Pulido de diseño** (Lucide + quick wins CSS + teleprompter espectacular). Barato,
   transversal, sube la percepción de todo. **Empezamos aquí.**
2. **V3-F2 · Mapa de estructura + bolita (modo solitario).** Mejora la joya para todos, sin infra,
   riesgo bajo. Valida el modelo de tiempos.
3. **V3-F3 · Habilitadores:** Storage (Fase 15 adelantada) + andamiaje `Band.plan` (D8) + test de
   aislamiento parametrizado.
4. **V3-F4 · Quick wins de directo:** Modo Directo + pedalera + vídeo de referencia sincronizado +
   afinador + metrónomo lookahead.
5. **V3-F5 · Gestión de giras** (§4).
6. **V3-F6 · Realtime + sala de ensayo sincronizada** (sobre el mapa ya validado + Realtime).
7. **V3-F7 · Efecto red sin copyright:** compartir `unlisted` + onboarding viral + oEmbed.
8. **V3-F8 · EPK + página pública + perfil indexable + RSVP + seguir/fans** (entra el rol fan, RLS).
9. **V3-F9 · Biblioteca global** (D1/D2; tras validar el plano público).
10. **V3-F10 · Red acotada** (D3): directorio + bolsa de colaboraciones.
11. **V3-F11 · Monetización de pago** (Stripe/Pro) cuando Storage + web pública den el gancho.

**Lógica:** primero lo que mejora la joya y la imagen **sin infra** (1–2), luego los habilitadores
(3), luego el "wow" sobre la joya (4–6), y al final lo público/red escalonado de menor a mayor
riesgo legal/operativo (7→10), con la monetización montándose encima.

---

## 7. Decisiones menores aún abiertas (no bloquean el arranque)

- **Biblioteca:** snapshot inmutable (rec.) vs editable; `content_json` (rec.) vs tablas espejo.
- **Red:** ¿el actor público es persona (MusicianProfile) o solo banda? (define DM futuro).
- **Giras:** ¿mapa Leaflet+OSM (gratis, rec.) o Google/Mapbox (API key/coste)?
- **Ensayo:** ¿granularidad del mapa por sección (rec.) o por línea? ¿guests pueden unirse a la sala?
- **Infra:** ¿observabilidad mínima (Sentry) ya? ¿cuándo el worker no-serverless para transcripción?
- **Monetización:** precio ancla Pro (6–9 €/mes por banda con PPA LATAM); entradas/merch con
  comisión (Stripe Connect) diferido por coste regulatorio.

---

## 8. Próximos pasos anotados por Oscar (2026-07-01)

> ✅ **Implementadas (2026-07-01)** — T-161 y T-162 en `harness/ROADMAP.md`, `run_checks` TODO VERDE
> (216 unit · 139 e2e). Detalle en `REGISTRO_DE_CAMBIOS.md`. El diseño de abajo se conserva como
> referencia de las decisiones tomadas.
>
> ✅ **T-163 (2026-07-02)** — siguiendo la idea de Oscar de depender lo menos posible de la IA
> externa: CifraClub y LaCuerda ahora tienen **parser propio sin IA** (regex sobre HTML crudo,
> verificado a mano) para buscar e importar; el flujo con IA de §8.2 queda como red de seguridad.
> Detalle completo en `REGISTRO_DE_CAMBIOS.md`.

Dos mejoras pedidas directamente por Oscar, implementadas como **T-161, T-162**
en `harness/ROADMAP.md`, independientes entre sí y de bajo riesgo arquitectónico:

### 8.1 T-161 · Afinador como sección propia del menú principal

Hoy el afinador (`tuner.js`, T-091) solo vive **dentro del player** (botón dentro de `index.html`).
Oscar quiere un acceso directo en la **navegación principal del shell**, justo debajo de "Inicio".

- Añadir un ítem `{ label: 'Afinador', icon: 'tuner'/'mic', href: 'afinador.html' }` en el array de
  navegación de `static/shell.js` (justo tras `Inicio`, antes de `Explorar`).
- Nueva página **standalone** `static/afinador.html` + `afinador_page.js` que reutiliza el panel y
  la detección de tono ya existentes en `tuner.js` (autocorrelación `bfDetectPitch`, Web Audio) sin
  duplicar lógica — se extrae el panel de `tuner.js` a un módulo compartido si hiciera falta, y el
  player lo sigue usando igual (no se toca `sync_engine.js`).
- El acceso desde el player (botón 🎵/afinador dentro de `index.html`) **se mantiene** para afinar
  sin salir de la canción; el nuevo ítem del menú es un atajo adicional para afinar sin tener una
  canción abierta.
- Icono nuevo en `static/icons.js` si no existe uno adecuado ("tuner"/diapasón).
- Test e2e: `test_afinador_accesible_desde_menu` (clic en el ítem del menú → panel visible y detecta
  440 Hz → La4, igual que el test ya existente del player).

### 8.2 T-162 · Búsqueda de canciones por nombre (sin pegar enlace)

**Problema actual:** para importar con IA (`import_router.py` + `importer.py`, T-0xx) hay que pegar
la URL exacta de CifraClub/LaCuerda/Ultimate Guitar. Oscar quiere escribir solo el **nombre de la
canción** (y opcionalmente el artista) en el buscador y que la app le ofrezca una lista de
resultados previos entre los que elegir, antes de hacer la importación completa.

**Cómo lo haría (reaprovechando `importer.py`, sin SDKs nuevos, mismo patrón urllib/Jina Reader):**

1. **Nuevo paso de búsqueda, separado de la extracción.** Se añade `search_song(query: str) -> list[dict]`
   en `src/services/importer.py`:
   - Construye la URL de búsqueda de cada sitio soportado (p. ej.
     `https://www.cifraclub.com/busca/?q=<query>` y el buscador equivalente de LaCuerda).
   - Reutiliza `fetch_page_text`/`_fetch_via_jina` para traer el HTML de la página de resultados
     (mismo mecanismo anti-bloqueo que ya existe para la extracción).
   - Pide al modelo de OpenRouter (mismo `extract_chords`, prompt distinto y más barato) que
     devuelva **una lista JSON** `[{title, artist, url, source}]` a partir del texto de la página de
     resultados — igual que hoy se le pide la partitura completa, pero aquí solo estructura la lista
     de candidatos en vez de las líneas de acordes.
   - Se puede consultar CifraClub y LaCuerda **en paralelo** (2 fetches) y fusionar/ordenar los
     resultados (p. ej. por coincidencia de título) antes de devolverlos.
2. **Nuevo endpoint** `GET /import/search?q=...` en `import_router.py` → devuelve la lista de
   candidatos (máx. ~8), cada uno con `title`, `artist`, `url`, `source` (para mostrar el origen).
   Mismo `Depends(get_current_user)` que el resto de `/songs`.
3. **Frontend:** en la pantalla de importación (`editor.html`/`import.js` o donde viva hoy el campo
   de "pegar enlace"), se añade un campo de texto "Buscar canción" **por encima** del campo de URL
   (el campo de URL se mantiene como alternativa manual/avanzada, no se elimina). Al escribir y
   pulsar buscar (o tras un debounce), se llama a `/import/search` y se pintan tarjetas con
   título + artista + insignia del origen (CifraClub/LaCuerda). Al hacer clic en una tarjeta, se
   rellena el campo de URL con la del resultado elegido y se dispara el flujo de importación normal
   (`import_from_url`) — es decir, el buscador es una **capa de preselección** delante del import ya
   existente, no un import distinto. El usuario puede cambiar de resultado antes de confirmar.
4. **Fuera de alcance ahora (diferido):** paginación de resultados, más sitios que CifraClub/
   LaCuerda, caché de búsquedas repetidas, y rate-limit del endpoint de búsqueda (igual que el
   import de hoy, cada llamada cuesta una petición a OpenRouter — vigilar cuota gratuita del
   modelo, `Band.plan`/D8 ya tiene el andamiaje de contador si hiciera falta limitarlo).
5. **Tests:** unit para `search_song` con HTML de resultados simulado (fixture, sin red real) +
   `test_api_import_search` (mockeando `search_song`) + e2e que escribe un nombre, ve tarjetas y
   confirma que elegir una rellena el campo de URL.

---

> **Estado:** dirección V3 aprobada por Oscar con D1–D8 cerradas. **Arranca V3-F1 (diseño)** por el
> bucle de 7 pasos de `CLAUDE.md`. La V2 (Fases 7–13) sigue intacta y en producción.
