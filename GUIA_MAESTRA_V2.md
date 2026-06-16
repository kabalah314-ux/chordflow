# 🎸→🏠 ChordFlow v2 — Guía Maestra del giro a **SaaS de gestión de bandas**

> Continuación de [GUIA_MAESTRA.md](GUIA_MAESTRA.md). Este documento define el **nuevo
> enfoque del producto**: de "lector/teleprompter de partituras de un usuario" a
> **SaaS de gestión para músicos que se mueven en bandas**.
>
> Estado: **núcleo F7–12 IMPLEMENTADO en local** (no desplegado). Fuente de verdad de decisiones
> del giro. Última actualización: 2026-06-16.
> Reglas operativas y bucle de trabajo siguen en [CLAUDE.md](CLAUDE.md).
>
> ✅ Documento **aprobado** (2026-06-15). Decisiones de producto del giro cerradas (§2 y §12).
> **Revisión 2026-06-16:** el **§3 (mapa de navegación)** se reescribe al modelo agregado
> **TÚ/BANDA** (app shell de lateral fijo); es la especificación de UX que materializa la
> **Fase 13** (§10). Siguiente paso de producto: ejecutar la Fase 13 (app shell + sistema de
> diseño + rebranding BandFlow).

---

## 1. Visión y posicionamiento

ChordFlow deja de ser "una app para leer partituras" y pasa a ser **la herramienta con la
que una banda se organiza**: su repertorio, sus setlists, su agenda de ensayos y conciertos,
y sus cuentas. La **partitura sincronizada (el teleprompter) sigue siendo la joya** del
producto, pero ahora vive *dentro* de un flujo mayor.

**Para quién:** músicos que se mueven en bandas. Cada usuario tiene su **espacio personal**
(sus partituras) **y** pertenece a una o varias **bandas** (grupos de usuarios que comparten
toda la información de esa banda).

**Observación estratégica:** este giro convierte a ChordFlow en **la misma forma** que tu
SaaS de tatuadores (multi-tenant de gestión). La correspondencia es casi 1:1:

| ChordFlow (banda) | SaaS tatuadores (estudio) |
|---|---|
| Banda | Estudio |
| Músico / miembro | Tatuador / empleado |
| Repertorio | Catálogo / portfolio |
| Evento (ensayo/concierto) | Cita / sesión |
| Setlist | (plan de sesión) |
| Finanzas con división | Caja / liquidación |
| Chat de banda + comentarios | Chat de estudio + comentarios |
| Invitaciones + roles | Invitaciones + roles |

→ Toda la capa **"Organización + Miembros + Roles + Invitaciones + Agenda + Finanzas"** se
diseña **genérica** y se promueve al **molde** (`../app-skeleton`). Se construye una vez y
sirve para las dos apps. Ver §11.

---

## 2. Decisiones tomadas (acordadas con el usuario)

Estas son firmes (origen: sesión 2026-06-15):

1. **Mix personal + bandas.** Cada usuario tiene partituras personales **y** bandas. El foco
   del producto es la **gestión de banda**.
2. **Roles:** **Admin(s)** (gestionan banda, miembros, agenda y finanzas) **+ Miembros**
   (ven todo, editan repertorio y setlists).
3. **Unirse a una banda:** por **enlace/código de invitación** (no depende de envío de emails,
   que sigue pendiente).
4. **Finanzas:** **bote común estilo Splitwise** — cada movimiento tiene quién pagó/cobró y
   cómo se reparte; la app calcula el **saldo neto** de cada miembro (quién debe y a quién).
   El reparto es **personalizable** por movimiento (no solo a partes iguales).
5. **Agenda:** una sola entidad **Evento** con **tipo** (`ensayo` / `concierto` / `otro`).
   El setlist se adjunta a un evento de tipo concierto; las canciones se adjuntan al setlist.
6. **Mini-chat de banda:** un **chat general** de la banda (cositas, avisos) **+ un hilo de
   comentarios en cada evento** (para el "puedo / no puedo" + proponer alternativas por
   escrito). Empieza **simple** (lista con refresco; tiempo real más adelante). Las **notas**
   importantes son **mensajes fijados** por un admin (sin sección aparte).
7. **Asistencia a eventos:** **sí** — cada miembro marca "voy / no voy / quizás" en cada
   evento (`EventAttendance`), complementado por el hilo de comentarios.
8. **Crear eventos:** **solo admins**. Los miembros ven la agenda, confirman asistencia y
   comentan; proponer un ensayo se hace por chat y lo crea un admin.
9. **Canción personal → banda:** **por copia** — la banda tiene su propia versión
   (autoritativa para la banda); editar la del repertorio no toca tu copia personal.
10. **Liquidación de saldos (settlements):** la Fase 11 **muestra los saldos** (quién debe y a
    quién); registrar las transferencias que ponen los saldos a cero queda como mejora
    posterior.

---

## 3. Arquitectura de la información (mapa de navegación)

> **Rumbo de UX (revisado 2026-06-16).** La navegación se organiza en **dos contextos** con un
> **app shell de lateral fijo**. La base de la app es **el usuario** (vista *agregada* de todas
> sus bandas); entrar en una banda abre su **espacio de gestión propio**, con identidad visual
> inconfundible, donde todo lo que se toca va a **la "carpeta" de esa banda**. Esta es la
> especificación que materializa la **Fase 13** (§10).

### 3.1 Contexto **TÚ** — la base (vista agregada de todas mis bandas)

Es lo que ves al entrar. Lateral fijo; casi todas las secciones **juntan datos de todas las
bandas** a las que perteneces, con **etiqueta de banda** y **filtro por banda**.

```
┌────────────┬──────────────────────────────┐
│  BandFlow  │  contexto: TÚ          ⚙ 👤  │
│            ├──────────────────────────────┤
│ 🏠 Inicio  │  cockpit: lo importante de    │
│ 🎵 Bibliot.│  TODAS tus bandas             │
│ 📅 Agenda  │                              │
│ 💶 Finanzas│                              │
│ 💬 Chat    │                              │
│ 👥 Bandas  │                              │
│────────────│                              │
│ 👤 Perfil  │                              │
└────────────┴──────────────────────────────┘
   en móvil → el lateral se colapsa a nav inferior
```

- **🏠 Inicio** — cockpit: próximos eventos de todas tus bandas, **lo que debes/te deben en
  total**, últimos mensajes, atajos.
- **🎵 Biblioteca** *(biblioteca + repertorio unificados)* — **todas las canciones** (personales
  `band_id=null` + de tus bandas) con **buscador** y filtro **Todas · Personales · [cada banda]**.
  Al elegir una banda se ven **su repertorio y sus setlists**. ▶️ abre el reproductor.
- **📅 Agenda** — **todos los eventos de todas tus bandas**, cada uno con su **etiqueta de banda**;
  filtro por banda; asistencia (voy/no/quizás).
- **💶 Finanzas** — resumen: por cada banda, **tu saldo** (debes/te deben) y el fondo.
- **💬 Chat** — lista de conversaciones, **una por banda** (estilo mensajería) + hilos de evento.
- **👥 Bandas** — tus bandas con **rol, instrumento y capacidad de gestión** (admin/member/guest);
  crear / unirse por código. **Aquí se entra al contexto BANDA.**
- **👤 Perfil** — nombre, instrumentos, avatar.

### 3.2 Contexto **BANDA** — el espacio de gestión de una banda

Al pulsar una banda en **👥 Bandas**, el contenido pasa a esa banda **sin perder el lateral**.
Un **banner de banda** ancho y con identidad propia (avatar + tu rol) hace **imposible
confundir** que estás gestionando *esa* banda; debajo, sus **pestañas**.

```
┌────────────┬──────────────────────────────────────────┐
│  BandFlow  │  ‹ Salir   🎸 LOS TELÚRICOS  bajo · admin │  ← banner inconfundible
│            ├──────────────────────────────────────────┤
│ 🏠 Inicio  │ Resumen│Miembros│Repertorio│Setlists│ ... │  ← pestañas de la banda
│ 🎵 Bibliot.│──────────────────────────────────────────│
│ 📅 Agenda  │   gestión SOLO de esta banda              │
│ 💶 Finanzas│   (todo lo que tocas va a su "carpeta")    │
│ 💬 Chat    │                                          │
│ 👥 Bandas ◄│                                          │
│ 👤 Perfil  │                                          │
└────────────┴──────────────────────────────────────────┘
```

**Pestañas dentro de la banda:** `Resumen` · `Miembros` *(roles, instrumentos, invitaciones —
admin)* · `Repertorio` · `Setlists` · `Agenda` · `Finanzas` · `Chat` · `Ajustes` *(nombre,
divisa, avatar — admin)*. Corresponden 1:1 con lo ya construido en las Fases 7–12.

### 3.3 Principio rector (TÚ agregado vs BANDA con scope)

- **TÚ = todas las bandas juntas** (cockpit transversal: "¿qué tengo esta semana?", "¿cuánto debo
  en total?").
- **BANDA = una sola banda** + lo que **solo existe ahí** (miembros, roles, invitaciones, ajustes).
- Cualquier creación/edición dentro del contexto BANDA escribe **siempre con su `band_id`**: el
  modelo de datos ya lo garantiza (`Song.band_id`, `Setlist.band_id`, y todo lo de banda cuelga de
  `bands`). La UX hace **visible** esa garantía (banner + scope), que es justo la regla de oro
  multi-tenant (§5.2) llevada a la interfaz.
- El **reproductor sincronizado no cambia** y se abre **a pantalla completa** (sin lateral) desde
  cualquier contexto: es el destino al abrir una canción, venga del espacio personal o del
  repertorio de una banda. Eso protege lo que ya está en producción.

---

## 4. Modelo de datos

Diseño **aditivo**: añadimos tablas nuevas y hacemos *nullable* un par de columnas. Lo
existente (`Song`, `Section`, `Line`, `ChordMarker`, `TabLine`, `Setlist`, `SetlistItem`)
**no se rompe**.

### 4.1 Entidades nuevas

**`MusicianProfile`** (perfil del músico)
- `id` (= user_id de Supabase, String36) · `display_name` · `instruments` (JSON) ·
  `avatar_url` · `created_at`.
- Se rellena en el primer login (display_name desde Supabase). Sirve para mostrar nombres
  reales en vez de UUIDs en la lista de miembros, finanzas, asistencia, etc.

**`Band`** (banda)
- `id` · `name` · `description` · `avatar_url` · `created_by` (user_id) · `created_at` ·
  `updated_at` · `deleted_at` (soft delete, como Song).

**`BandMembership`** (pertenencia músico↔banda)
- `id` · `band_id` (FK) · `user_id` · `role` (`admin` | `member`) ·
  `instrument` (en esta banda, opcional) · `joined_at`.
- Único `(band_id, user_id)`. El creador de la banda entra como `admin`.

**`BandInvite`** (invitación por código)
- `id` · `band_id` · `code` (token único) · `created_by` · `role_to_grant` (default `member`) ·
  `expires_at` (opcional) · `max_uses`/`used_count` (opcional) · `created_at`.
- Unirse: el músico (ya registrado) abre el enlace/código → se crea su `BandMembership`.

**`Event`** (agenda — ensayo/concierto/otro)
- `id` · `band_id` · `type` (`rehearsal` | `concert` | `other`) · `title` ·
  `starts_at` · `ends_at` (opcional) · `location` · `notes` · `status`
  (`lead` | `contacted` | `negotiating` | `confirmed` | `done` | `cancelled`).
  Las etapas `lead`/`contacted`/`negotiating` son el **pipeline de booking** y solo aplican a
  `concert`; un `rehearsal`/`other` nace en `confirmed`. (Detalle en
  [GUIA_MAESTRA_V2_FUNCIONAL.md](GUIA_MAESTRA_V2_FUNCIONAL.md), Área 10 y §C.4.)
- Solo concierto: `setlist_id` (FK setlists, nullable) · `is_promoting` (bool) ·
  `promo_notes` (text/JSON con enlaces).
- **Caché del bolo:** NO es un campo del evento; se registra como **ingreso en Finanzas**
  ligado al evento (`event_id`), para que entre en la división automáticamente (§6).

**`EventAttendance`** (confirmación de asistencia)
- `id` · `event_id` · `user_id` · `status` (`yes` | `no` | `maybe`) · `responded_at`.
- Único `(event_id, user_id)`. Cada miembro marca "voy / no voy" en cada evento.

**`Transaction`** (finanzas — movimiento)
- `id` · `band_id` · `type` (`expense` | `income`) · `description` · `amount` ·
  `date` · `category` · `paid_by` (user_id: quién adelantó el gasto / quién cobró el ingreso) ·
  `event_id` (nullable: ligar a un bolo) · `created_by` · `created_at`.

**`TransactionSplit`** (reparto de un movimiento)
- `id` · `transaction_id` (FK) · `user_id` · `share_amount` (lo que le corresponde a ese
  miembro de este movimiento).
- La suma de los `share_amount` = `amount` del movimiento. Default: a partes iguales entre
  miembros activos; **editable** (reparto personalizado) → cumple "que se dividan como quieran".

**`Message`** (mini-chat de banda + comentarios de evento)
- `id` · `band_id` (FK, siempre) · `event_id` (FK `events`, **nullable**) · `author_id`
  (user_id) · `body` (text) · `is_pinned` (bool, default false) · `created_at` ·
  `edited_at` (nullable) · `deleted_at` (nullable, soft delete).
- **Chat general** de la banda = mensajes con `event_id = null`.
- **Hilo de un evento** = mensajes con `event_id` = ese evento (el "puedo/no puedo" + proponer
  alternativas por escrito; complementa la asistencia estructurada de `EventAttendance`).
- **Notas** = mensajes con `is_pinned = true` (un admin fija/desfija; aparecen arriba). No hay
  sección de notas aparte.
- Arranca **simple** (lista que se refresca al abrir y cada pocos segundos); el tiempo real
  (Supabase Realtime) se añade después sin tocar el modelo.

### 4.2 Cambios a entidades existentes (mínimos, no rompen prod)

- **`Song`** → `+ band_id` (nullable, FK `bands`, index).
  `null` = partitura personal (`owner_id`). Con valor = está en el repertorio de esa banda.
- **`Setlist`** → `+ band_id` (nullable, FK `bands`, index).
  `null` = setlist personal. Con valor = setlist de esa banda.

### 4.3 Diagrama de relaciones

```
MusicianProfile ──< BandMembership >── Band ──< BandInvite
                                        │
                                        ├──< Song (band_id)        ← repertorio
                                        │       └──< Section → Line → ChordMarker/TabLine  (sin cambios)
                                        ├──< Setlist (band_id) ──< SetlistItem >── Song
                                        ├──< Event ──(concierto)── setlist_id ─▶ Setlist
                                        │       └──< EventAttendance >── MusicianProfile
                                        ├──< Transaction ──< TransactionSplit >── MusicianProfile
                                        │         └── event_id ─▶ Event (opcional)
                                        └──< Message ── author ─▶ MusicianProfile
                                                  └── event_id ─▶ Event (null = chat general)
```

---

## 5. Roles, permisos y autorización multi-tenant

### 5.1 Matriz de permisos

| Acción | Admin | Miembro |
|---|:---:|:---:|
| Ver todo (repertorio, setlists, agenda, finanzas, miembros) | ✅ | ✅ |
| Reproducir canciones y setlists | ✅ | ✅ |
| Crear/editar repertorio y setlists | ✅ | ✅ |
| Crear/editar/borrar eventos (agenda) | ✅ | ❌ |
| Confirmar asistencia a un evento | ✅ | ✅ |
| Escribir en el chat / comentar eventos | ✅ | ✅ |
| Editar/borrar **su propio** mensaje | ✅ | ✅ |
| Fijar/desfijar mensajes (notas) · borrar cualquiera | ✅ | ❌ |
| Registrar/editar finanzas y repartos | ✅ | ❌ |
| Ver su propio saldo y el de la banda | ✅ | ✅ |
| Invitar / expulsar / cambiar roles | ✅ | ❌ |
| Editar datos de la banda / borrarla | ✅ | ❌ |

> Decisión cerrada: **crear/editar/borrar eventos es solo de admins**. Los miembros ven la
> agenda, confirman asistencia y comentan; proponer un ensayo se hace por chat.

### 5.2 El reto técnico central (y la mayor superficie de riesgo)

El cambio grande **no son las features, es pasar de un solo usuario a multi-tenant
colaborativo**. Hoy cada ruta hace `filter(owner_id == user)`. Ahora hace:
*"¿este usuario es miembro activo de esta banda? ¿con qué rol?"*.

- Dos dependencias nuevas de FastAPI:
  - `require_band_member(band_id)` → 404/403 si no es miembro.
  - `require_band_admin(band_id)` → 403 si no es admin.
- Cada recurso de banda lleva `band_id` y se valida pertenencia + rol antes de tocar nada.
- **Regla de oro nueva:** un fallo aquí = **fuga de datos entre bandas** (un usuario viendo
  la info de una banda que no es suya). Por eso, **cada ruta de banda exige un test
  "usuario ajeno → 403/404"**, igual de obligatorio que el doctor verde. Encaja con la
  cultura de auditoría del proyecto.

---

## 6. Finanzas con división de cuentas (modelo Splitwise)

Cada **movimiento** (`Transaction`) tiene: importe total, **quién puso/recibió el dinero**
(`paid_by`) y un **reparto** (`TransactionSplit`) cuyas partes suman el total.

- **Gasto:** `paid_by` adelantó el dinero; cada miembro "consume" su `share`.
  → Balance: `paid_by += amount`; cada miembro `-= su share`.
- **Ingreso** (p. ej. caché de un bolo): `paid_by` recibió el dinero; cada miembro tiene
  derecho a su `share`.
  → Balance: `paid_by -= amount` (lo tiene, debe repartir); cada miembro `+= su share`.

**Saldo neto de un miembro** = Σ(lo que puso/recibió) − Σ(sus shares).
- Saldo **positivo** → la banda/los demás le deben.
- Saldo **negativo** → él debe a la banda/los demás.

**Reparto personalizable:** por defecto se divide a partes iguales entre miembros activos,
pero se pueden editar los `share_amount` (por importe o por %, convertido a importe) y elegir
**entre qué miembros** se reparte. Esto cubre "que se dividan como quieran".

**Ejemplo:**
> La banda (4 miembros) cobra **400 €** por un bolo → ingreso, `paid_by` = quien cobró,
> reparto 100 €/uno. Antes, el batería puso **60 €** de gasolina → gasto, `paid_by` = batería,
> reparto 15 €/uno. La app muestra: el que cobró debe repartir; el batería tiene +45 € de
> saldo a su favor; etc. Todo cuadra a cero.

*Liquidación (settlements) — decidido:* la primera versión (Fase 11) **muestra los saldos**;
registrar las transferencias reales que ponen los saldos a cero ("X paga a Y 30 €") queda como
**mejora posterior**.

---

## 7. Espacio personal vs banda — cómo se mueven las canciones

- **Mis partituras** = `Song` con `band_id = null`, `owner_id` = yo.
- **Repertorio de banda** = `Song` con `band_id` = la banda (visible/editable por sus miembros).
- **Meter una canción personal en una banda** (decidido): por **copia** — la banda tiene su
  propia versión (autoritativa para la banda); editar la del repertorio no toca tu copia
  personal y viceversa. Es lo más simple y evita líos de permisos.
  - Alternativa (referencia compartida) la descartamos por ahora: complica "¿quién puede
    editar una canción que es de otro pero está en mi banda?".
- **"Que te han enviado"**: en una fase posterior, un músico podrá **enviar** una de sus
  partituras a otro músico o a una banda (= copia en el destino). Se diseña pero no es de las
  primeras fases.

---

## 8. Invitaciones (unirse a una banda)

1. Un **admin** genera una invitación → `BandInvite` con un **código/enlace** único.
2. Comparte el enlace (WhatsApp, etc.).
3. El otro músico, **ya registrado**, abre el enlace → confirma → se crea su `BandMembership`
   con el rol indicado (default `member`).
4. Controles opcionales: caducidad y/o nº máximo de usos del código.

No depende del envío de emails (pendiente, T-046/T-047). Cuando los emails estén, se puede
añadir "invitar por email" como segunda vía sin rehacer el modelo.

---

## 9. Migración sin romper producción

La app está **en vivo** (Vercel + Supabase + Postgres). Todo el giro es **aditivo**:

- **Tablas nuevas:** `musician_profiles`, `bands`, `band_memberships`, `band_invites`,
  `events`, `event_attendance`, `transactions`, `transaction_splits`, `messages`.
- **Columnas nuevas nullable:** `songs.band_id`, `setlists.band_id`.
- **Datos actuales:** todas las canciones y setlists existentes quedan con `band_id = null`
  → se convierten automáticamente en el **espacio personal** de su dueño. **Cero pérdida de
  datos, cero rotura.**
- Cada cambio de esquema → **migración Alembic** revisada + `alembic check` limpio
  (regla de CLAUDE.md §3). Se aplica a Postgres con el **pooler de sesión (5432)**.

---

## 10. Hoja de ruta por fases

Cada fase es un incremento **desplegable** que deja la app **verde** (doctor + tests +
registro), siguiendo el bucle de 7 pasos de CLAUDE.md. No se empieza la siguiente hasta
cerrar la anterior.

| Fase | Nombre | Entrega | Resultado tangible |
|---|---|---|---|
| **7** | **Identidad + núcleo de banda** | `MusicianProfile`, `Band`, `BandMembership`, `BandInvite` · `require_band_member`/`require_band_admin` · migración aditiva · pantalla "Mis bandas" + crear banda + invitar por código + perfil básico | Puedo crear una banda, invitar miembros y entrar. Nada roto. |
| **8** | **Repertorio** | `Song.band_id` · vista de repertorio dentro de la banda · añadir canción (nueva o **copiar** de mis partituras) · permisos | La banda tiene su repertorio compartido. |
| **9** | **Setlists de banda** | `Setlist.band_id` · editor de setlist que tira del repertorio · se preservan los setlists personales | Setlists de concierto por banda. |
| **10** | **Agenda (eventos)** | `Event` (ensayo/concierto/otro) · `EventAttendance` (voy/no voy) · calendario + lista próximos/pasados · adjuntar setlist al concierto | Gestión de ensayos y conciertos. |
| **11** | **Finanzas con división** | `Transaction` + `TransactionSplit` · reparto personalizable · saldo neto por miembro · caché del bolo ligado al evento | Cuentas de la banda y quién debe a quién. |
| **12** | **Comunicación (chat + notas)** | `Message` (chat general + hilos de evento) · publicar/editar/borrar el propio · **fijar** notas (admin) · refresco periódico (tiempo real después) | La banda habla, comenta eventos y fija notas. |
| **13** | **App shell + sistema de diseño + rebranding** | **Reskin completo** sobre el stack actual (no se reescribe a otro framework): **app shell** de lateral fijo con los **dos contextos TÚ/BANDA** (§3), **banner de banda** inconfundible, **sistema de diseño** único (tokens claro/oscuro + componentes) limpio y profesional · **vistas agregadas** (Inicio/Biblioteca unificada/Agenda/Finanzas/Chat de todas las bandas) · **espacio de banda** con pestañas · **dashboard** · **rebranding a BandFlow** | App con aspecto profesional y navegación clara; "estás en una banda" nunca se confunde. |

> La **fundación (Fase 7) va primero** porque todo cuelga de ella. La navegación nueva se
> *diseña* desde ya pero se *implementa* en paralelo: cada sección estrena su sitio cuando
> existe. El detalle de tareas (T-NNN) se abrirá en `harness/ROADMAP.md` **solo cuando
> aprobemos este documento**.

---

## 11. Sinergia con el molde (SaaS de tatuadores)

Al construir la Fase 7 (y 10/11) se diseña la capa genérica **una sola vez** y se promueve al
molde `../app-skeleton`, para que el SaaS de tatuadores la reutilice:

- **Organización + Membresía + Roles + Invitaciones** → `Band` es una instancia; `Estudio`
  será otra. La tabla/lógica no debe hablar de "banda", sino de "organización/tenant".
- **Agenda de eventos** (Evento con tipo) → ensayos/conciertos ↔ citas/sesiones.
- **Finanzas con división** (Transaction + Split + saldos) → caja de la banda ↔ caja del estudio.
- **Chat + comentarios** (`Message` general + por entidad) → chat de banda ↔ chat de estudio.

Regla: cuando un patrón de la Fase 7/10/11 sea claramente agnóstico al dominio musical, se
anota como candidato a molde (igual que se hizo en la Fase M). Ver
[[molde-reutilizable-goal]].

---

## 12. Decisiones cerradas y lo que queda abierto

**✅ Cerradas en esta sesión** (ya reflejadas en el documento):

1. **Asistencia a eventos** (`EventAttendance`): **sí**.
2. **Crear eventos:** **solo admins** (miembros ven, confirman y comentan).
3. **Canción personal → banda:** por **copia**.
4. **Liquidación de saldos:** Fase 11 **muestra saldos**; el *settle* después.

**✅ Cerradas después (2026-06-16):**

5. **Nombre del producto**: **BandFlow** (decidido por el usuario). El rebranding (repo, títulos,
   manifest, marca en emails) se ejecuta en la **Fase 13**; hasta entonces el código sigue como
   `ChordFlow` para no romper nada.
6. **Divisa:** **EUR**, una por banda (`Band.currency` default `EUR`, §C.4.3). Sin multi-divisa en v1.

**⏳ Abiertas (no bloqueantes):**

7. **Notificaciones por email** (invitaciones, recordatorios de evento): ligado a T-046/T-047
   (emails aún no configurados). De momento todo funciona sin email.

---

## 13. Qué NO cambia (y hay que preservar)

- El **motor de sincronización** (`sync_engine.js`) y el **render compartido**
  (`score_render.js`) del reproductor: la joya intacta.
- El **modo test** + BD temporal del harness, el **doctor** y `run_checks`.
- La disciplina: **una tarea no está hecha hasta doctor verde + test que la cubre**
  (CLAUDE.md §2). Con multi-tenant se añade el test obligatorio de **aislamiento entre
  bandas**.
- El despliegue actual (Vercel + Supabase + Postgres) y las reglas de migración.

---

> **Siguiente paso (cuando apruebes este documento):** abrir la **Fase 7** en
> `harness/ROADMAP.md` con sus tareas T-NNN y empezar por la migración aditiva + el núcleo
> `Band`/`BandMembership`/auth multi-tenant. **Hasta entonces, no se toca código.**
