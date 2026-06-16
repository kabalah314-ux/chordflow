# 🎸 BandFlow — Especificación funcional completa (por áreas)

> Companion de [GUIA_MAESTRA_V2.md](GUIA_MAESTRA_V2.md). Aquí resolvemos **necesidad por
> necesidad** todo lo que hace una banda, decidiendo para cada una: si entra en la app o se
> descarta/aplaza, cómo se modela (datos) y se ve (UX), y en qué fase encaja.
>
> Estado: **COMPLETO y DESPLEGADO** — las 14 áreas especificadas; **Fases 7–13 (Áreas 1–12)
> implementadas y EN VIVO** (Vercel + Postgres) desde 2026-06-16. Áreas 13–14 (mercado, grabación,
> legal…) quedan para el roadmap posterior.
> Última actualización: 2026-06-17.
>
> Leyenda: ✅ ya existe · 🟡 parcial · ❌ nuevo · ⏳ aplazar.

---

## Área 1 — Repertorio y música

### Tabla de resolución

| # | Necesidad | Decisión | Cómo se resuelve | Fase |
|---|---|---|---|---|
| 1 | Crear/añadir canciones (propias y versiones) | ✅ Ampliar a banda | `Song.band_id` = repertorio compartido de la banda | 8 |
| 2 | Importar partituras/acordes con IA (URL) | ✅ Ya existe | Reusar `importer` dentro del contexto banda | 8 |
| 3 | Transponer al tono de cada cantante | ✅ El motor ya transpone | + guardar **tono preferido** de la banda (`Song.key`) | 8 |
| 4 | Marcar tonalidad / BPM / compás | 🟡 BPM ya existe | + `Song.key`, + `Song.time_signature` | 8 |
| 5 | Definir estructura (intro/estrofa/estribillo/solo/outro) | ✅ Ya existe | Entidad `Section` con nombre | — |
| 6 | Anotar quién toca qué (arreglos, voces, solos) | ❌ Nuevo | **Notas libres** de arreglo: `Song.arrangement_notes` (texto) | 8 |
| 7 | Afinación / capo por tema | ❌ Nuevo | + `Song.tuning`, + `Song.capo` | 8 |
| 8 | Estado de la canción | ❌ Nuevo | + `Song.status` (`learning` / `ready` / `archived`) | 8 |
| 9 | Etiquetar canciones (género, energía, idioma, década…) | ❌ Nuevo | + `Song.tags` (JSON array) | 8 |
| 10 | Adjuntar audio/vídeo de referencia | ❌ Nuevo | **Enlace (URL)** a YouTube/Spotify: `Song.reference_url` | 8 |
| 11 | Adjuntar letras completas (cantante) | 🟡 Verificar modelo actual | Vista **"solo letra"** en el reproductor (verificar `Line`/lyric en implementación) | 8 |
| 12 | Notas de ensayo por canción | ❌ Nuevo | **Campo propio**: `Song.rehearsal_notes` (texto), visible al abrir la canción | 8 |
| 13 | Versionar arreglos (v1, v2, "la acústica") | ⏳ Aplazar | Por **copia** (duplicar la canción, p. ej. "Tema X — acústico") | — |
| 14 | Guardar la duración real del tema | ❌ Nuevo | + `Song.duration_seconds` → alimenta el cálculo de tiempos del setlist (Área 3, #26) | 8/9 |

### Campos nuevos en `Song` (aditivos, todos `nullable`, no rompen producción)

```
Song (+ campos nuevos):
  key              String   nullable   # tono preferido de la banda (p. ej. "G", "Am")
  time_signature   String   nullable   # compás (p. ej. "4/4", "3/4")
  tuning           String   nullable   # afinación (p. ej. "Drop D", "Standard")
  capo             Integer  nullable   # traste del capo (0/null = sin capo)
  status           String   nullable   # learning | ready | archived
  tags             JSON     nullable   # ["rock", "abrir", "español", "alta-energía"]
  duration_seconds Integer  nullable   # duración real, para sumar tiempos de setlist
  reference_url    String   nullable   # enlace YouTube/Spotify de referencia
  arrangement_notes Text    nullable   # "solo de guitarra en el puente; coros Ana+Luis"
  rehearsal_notes  Text     nullable   # "repasar el corte final; subir medio tono"
```

> Estos campos viven en `Song` y, como las canciones de banda son **copias** (decisión §9 de
> la guía V2), cada banda tiene su propio `status`, `tags`, notas, etc. sin afectar a la versión
> personal ni a otras bandas.

### UX

- Al abrir una canción del repertorio se ve una **cabecera con metadatos** (tono, BPM, compás,
  afinación, capo, duración, estado, etiquetas) editable por cualquier miembro.
- **Notas de arreglo** y **notas de ensayo** se muestran en paneles colapsables debajo de la
  cabecera (siempre visibles, no hay que bucear en el chat).
- **Filtros/orden del repertorio** por estado y etiquetas ("ver solo las *ready*", "ver las de
  energía alta para abrir").
- El **enlace de referencia** abre el vídeo/tema original (botón "▶ Referencia").
- La **vista "solo letra"** es un modo del reproductor pensado para el cantante (texto grande,
  sin diagramas de acordes).

### Permisos

Según la matriz de la guía V2: **crear/editar repertorio es de Admin y Miembro** (todos los
miembros editan el repertorio y sus metadatos). Solo lo de banda; el espacio personal sigue
siendo del `owner_id`.

### Aplazado / mejoras futuras (anotadas, fuera de las primeras fases)

- **Versionado real de arreglos** (#13): de momento se resuelve duplicando la canción.
- **Subir archivos de audio propios** (demos, grabaciones de ensayo): requiere Supabase Storage;
  por ahora solo enlace (URL).
- **Reproducción del vídeo de referencia sincronizada con el teleprompter** (idea del usuario):
  que al darle play, el vídeo de YouTube y el resaltado de acordes avancen a la vez. Encaja muy
  bien con la "joya" del producto pero **no es prioritario**; se diseña más adelante sobre el
  motor de sync existente.

---

## Área 2 — Ensayos

> Gran parte se resuelve **reusando la Agenda (Fase 10)**: un ensayo es un `Event` con
> `type=rehearsal`. Lo nuevo es el **orden del día** (qué canciones se trabajan) y las
> **grabaciones**.

### Tabla de resolución

| # | Necesidad | Decisión | Cómo se resuelve | Fase |
|---|---|---|---|---|
| 15 | Convocar un ensayo (fecha, hora, lugar, duración) | ✅ Reusar Agenda | `Event` con `type=rehearsal` (lo crean **solo admins**) · `starts_at`/`ends_at`/`location` | 10 |
| 16 | Confirmar asistencia (voy / no voy / quizás) | ✅ Ya en la guía | `EventAttendance` | 10 |
| 17 | Orden del día (qué canciones se ensayan) | ❌ Nuevo | Tabla **`EventSong`** (evento + canción + orden + estado) | 10 |
| 18 | Reservar / pagar el local de ensayo | ✅ Reusar Finanzas | `Transaction` (gasto) ligada al evento (`event_id`) | 11 |
| 19 | Registrar qué se ensayó y qué quedó pendiente | ❌ Nuevo (ligero) | Estado por canción en `EventSong` (`rehearsed`/`pending`) + `Event.notes` (acta) | 10 |
| 20 | Grabar el ensayo (audio/vídeo) y compartirlo | ❌ Nuevo | **`Attachment`** (enlace) ligado al evento | 10 |
| 21 | "Temas a pulir" / deberes para casa | ✅ Reusar Área 1 | `Song.rehearsal_notes` + `Song.status` (filtrar `learning`) | 8/10 |
| 22 | Histórico de ensayos (cuántos, asistencia) | ✅ Derivado | Vista/consulta sobre `Event` + `EventAttendance` (sin modelo nuevo) | 10 |

### Entidades nuevas

**`EventSong`** (orden del día / canciones de un evento)
```
EventSong:
  id        · event_id (FK events) · song_id (FK songs)
  position  Integer            # orden en el ensayo
  status    String  nullable   # rehearsed | pending  (qué se trabajó y qué quedó)
  note      Text    nullable   # apunte rápido del ensayo para esa canción
  Único (event_id, song_id)
```
> Sirve a la vez para el **orden del día** (antes del ensayo) y para **registrar qué se tocó**
> (durante/después). En conciertos seguimos usando el `setlist_id` reutilizable; `EventSong` es
> la lista *ad-hoc* del ensayo.

**`Attachment`** (adjuntos por enlace — genérico, reutilizable)
```
Attachment:
  id        · band_id (FK, siempre)
  event_id  FK events  nullable   # adjunto de un evento (grabación, contrato, rider…)
  song_id   FK songs   nullable   # adjunto de una canción (si hiciera falta)
  url       String                # enlace (Drive, YouTube no listado, Dropbox…)
  label     String     nullable   # "Grabación 2ª parte", "Contrato sala X"
  kind      String     nullable   # recording | contract | rider | promo | other
  created_by · created_at
```
> Entidad **genérica de adjuntos por enlace**. Aquí cubre las grabaciones del ensayo; en el
> **Área 3** la reutilizamos para contratos, riders y material promocional. Sin subida de
> archivos (solo URL), coherente con la decisión del Área 1.

### Apoyo de UX

- **"Duplicar evento"**: botón para repetir rápido el ensayo de la semana siguiente (sustituye a
  la recurrencia real, aplazada).
- En el ensayo: lista de canciones (orden del día) con casillas **repasada / pendiente**;
  al cerrar, las pendientes se reflejan en `Song.status`/`rehearsal_notes`.
- **Histórico**: en la ficha de la banda, contador de ensayos y % de asistencia por miembro
  (derivado, sin tabla nueva).

### Permisos

- **Crear/editar el ensayo y su orden del día** → solo **Admin** (coherente con la guía V2).
- **Marcar repasada/pendiente** y añadir nota de canción → **cualquier miembro** (es trabajo de
  repertorio).
- **Confirmar asistencia** y **comentar** → cualquier miembro.

### Aplazado / mejoras futuras

- **Eventos recurrentes** (series semanales con excepciones): de momento, duplicar evento.
- **Subida de archivos** de grabaciones (en vez de enlace): requiere Supabase Storage.

---

## Área 3 — Conciertos / bolos

> Un concierto es un `Event` con `type=concert`. Se apoya en `Setlist` (Fase 9), `Transaction`
> (caché, Fase 11) y las entidades nuevas de abajo: `Venue`, `BandResource` (riders/backline) y
> el checklist.

### Tabla de resolución

| # | Necesidad | Decisión | Cómo se resuelve | Fase |
|---|---|---|---|---|
| 23 | Crear evento de concierto | ✅ Reusar Agenda | `Event` con `type=concert` (solo admins) | 10 |
| 24 | Datos del bolo (llegada, soundcheck, hora de tocar, fin) | ❌ Nuevo | Campos horarios en `Event` (concierto) | 10 |
| 25 | Construir setlist (orden + tiempos + total) | ✅ Reusar + duración | `Setlist`/`SetlistItem` + suma de `Song.duration_seconds` | 9 |
| 26 | Calcular si el setlist cuadra con el tiempo asignado | ❌ Derivado | Comparar duración total vs `Event.set_duration_minutes` | 9 |
| 27 | Notas por canción dentro del setlist | ❌ Nuevo | `SetlistItem.note` ("aquí hablo al público", "cambio de guitarra") | 9 |
| 28 | Adjuntar contrato del bolo | ✅ Reusar | `Attachment` (enlace, `kind=contract`) ligado al evento | 10 |
| 29 | Rider técnico (canales, monitores, backline) | ❌ Nuevo | **`BandResource`** reutilizable (texto/imagen) → enlazado al evento | 10 |
| 30 | Rider de hospitality (agua, comida, camerino) | ❌ Nuevo | Igual: `BandResource` reutilizable | 10 |
| 31 | Datos de contacto del promotor/sala | ❌ Nuevo | **`Venue`** reutilizable (`Event.venue_id`) | 10 |
| 32 | Caché y condiciones de cobro | ✅ Reusar Finanzas | `Transaction` (ingreso) ligada al evento + `Event.fee_notes` | 11 |
| 33 | Estado del bolo (propuesto/confirmado/cancelado/hecho) | ✅ Reusar | `Event.status` (el pipeline de booking se amplía en el Área 10) | 10 |
| 34 | Checklist pre-bolo (furgo, baterías, cables, merch…) | ❌ Nuevo | **`ChecklistItem`** por evento + **`ChecklistTemplate`** reutilizable | 10 |
| 35 | Plano de escenario / stage plot | ❌ Nuevo | `BandResource` (`kind=stage_plot`) o `Attachment` | 10 |
| 36 | Registrar cómo fue (público, incidencias, grabaciones) | ✅ Reusar | `Event.notes` + `Event.audience_count` + `Attachment` (grabaciones) | 10 |

### Campos nuevos en `Event` (solo conciertos; aditivos, `nullable`)

```
Event (+ campos de concierto):
  venue_id            FK venues  nullable   # sala (entidad reutilizable)
  load_in_at          DateTime   nullable   # hora de llegada / carga
  soundcheck_at       DateTime   nullable   # prueba de sonido
  set_time_at         DateTime   nullable   # hora de salir a tocar
  end_at              DateTime   nullable   # hora de fin (si difiere de ends_at)
  set_duration_minutes Integer   nullable   # tiempo de set asignado → comparar con el setlist
  fee_notes           Text       nullable   # condiciones de cobro (el importe va en Transaction)
  audience_count      Integer    nullable   # asistencia de público (cómo fue)
```
> El **caché** sigue la decisión de la guía V2: NO es un campo de importe del evento, se registra
> como **ingreso en Finanzas** (`Transaction` con `event_id`) para entrar en la división. En el
> evento solo viven las *condiciones* (`fee_notes`).

### Entidades nuevas

**`Venue`** (sala / promotor — reutilizable por banda)
```
Venue:
  id · band_id (FK)
  name · address · city · nullable
  contact_name · contact_phone · contact_email · nullable
  notes · created_at
```
> Se crea una vez y se reutiliza en cada bolo en esa sala (historial por sala más adelante).

**`BandResource`** (riders / backline / stage plot — reutilizables a nivel banda)
```
BandResource:
  id · band_id (FK)
  kind     String   # technical_rider | hospitality | backline | stage_plot |
                     # photo | promo | video | other   (photo/promo/video = galería EPK, Área 9)
  title    String
  body     Text     nullable   # contenido en texto
  image_url String  nullable   # imagen (enlace; subida de archivo = mejora futura)
  created_by · created_at
```
**`EventResource`** (qué recursos se adjuntan a un concierto)
```
EventResource:  id · event_id (FK) · resource_id (FK band_resources)
  Único (event_id, resource_id)
```
> Resuelve tu petición: un **apartado de la banda** donde subes el backline/rider (texto o
> imagen) **una vez** y lo **enganchas a todos los conciertos** que lo necesiten.

**`ChecklistTemplate` + `ChecklistTemplateItem`** (plantilla reutilizable de checklist)
```
ChecklistTemplate:      id · band_id · name · created_at
ChecklistTemplateItem:  id · template_id (FK) · text · position
```
**`ChecklistItem`** (checklist concreto de un evento)
```
ChecklistItem:  id · event_id (FK) · text · is_done (bool) · position
```
> Flujo: un evento puede **cargar una plantilla** ("mi checklist de bolo de siempre") que copia
> sus ítems al evento; luego cada ítem se marca **hecho/pendiente**.

### Apoyo de UX

- **Ficha de concierto** con cronograma del día (llegada → soundcheck → tocar → fin), sala,
  setlist con duración total y semáforo de si **cuadra** con el tiempo asignado, riders/backline
  adjuntos, contrato, checklist y, tras el bolo, público + grabaciones.
- En el setlist, cada ítem muestra su **nota** (`SetlistItem.note`) en el modo concierto.
- **Apartado "Recursos de la banda"** (riders/backline/stage plot) editable por admins y
  reutilizable en cualquier evento.

### Permisos

- **Crear/editar el concierto, sala, riders, recursos y checklist** → **Admin**.
- **Marcar ítems del checklist** como hechos → cualquier miembro (trabajo de equipo en el bolo).
- **Editar el setlist y sus notas** → cualquier miembro (es repertorio).
- **Confirmar asistencia / comentar** → cualquier miembro.

### Aplazado / mejoras futuras

- **Subida de archivos** (riders en PDF/imagen, grabaciones): por ahora todo por enlace/texto.
- **Historial por sala** (`Venue`): ver todos los bolos tocados en esa sala.
- **Pipeline de booking** (propuesto → negociando → cerrado): se desarrolla en el **Área 10**.

---

## Área 4 — Logística y transporte

> Área ligera: casi todo cuelga del **concierto** (`Event`) y de **Finanzas**. Lo nuevo es
> mínimo: un `assignee` en el checklist, un par de horarios y la foto del recibo.

### Tabla de resolución

| # | Necesidad | Decisión | Cómo se resuelve | Fase |
|---|---|---|---|---|
| 37 | Quién lleva qué material (reparto de carga) | ❌ Nuevo (ligero) | `ChecklistItem.assignee_id` (responsable del ítem) | 10 |
| 38 | Transporte (quién conduce, quién va con quién, alquiler furgo) | ❌ Nuevo (ligero) | Ítems de checklist con `assignee_id` + `Event.logistics_notes` | 10 |
| 39 | Km / gasolina / peajes / parking | ✅ Reusar Finanzas | `Transaction` (gasto manual) ligado al evento + **foto del recibo** (`Attachment`) | 11 |
| 40 | Alojamiento si el bolo es lejos | ✅ Reusar Finanzas | `Transaction` (gasto) + `Event.logistics_notes` | 11 |
| 41 | Horarios de salida y vuelta | ❌ Nuevo | `Event.depart_at`, `Event.return_at` | 10 |
| 42 | Mapa / dirección de la sala con enlace | ✅ Reusar | `Venue.address` → enlace a Google Maps autogenerado | 10 |

### Cambios de modelo (aditivos)

```
ChecklistItem (+ campo):
  assignee_id   user_id  nullable   # responsable de ese ítem (llevar PA, conducir…)

Event (+ campos de logística; nullable):
  depart_at        DateTime   # hora de salida
  return_at        DateTime   # hora de vuelta estimada
  logistics_notes  Text       # transporte, carpooling, alojamiento, observaciones

Attachment (+ campo):
  transaction_id   FK transactions  nullable   # adjuntar foto de recibo/factura a un gasto
```
> Con `Attachment.transaction_id`, el **recibo** (foto) cuelga directamente del gasto. Cubre
> también el Área 6, #58 ("adjuntar tickets/facturas").

### Apoyo de UX

- En la ficha del concierto, el **checklist muestra el responsable** de cada ítem (avatar), de
  modo que "quién lleva qué" y "quién conduce" se ven de un vistazo.
- Bloque **"Logística"** con salida/vuelta, transporte y alojamiento.
- Al registrar un gasto de desplazamiento, botón **"añadir recibo"** (foto/enlace).

### Permisos

- **Editar logística, horarios y asignar responsables** → **Admin**.
- **Marcar su ítem como hecho** → cualquier miembro.
- **Registrar gasto + subir recibo** → **Admin** (coherente con la matriz de Finanzas de la V2).

### Aplazado / mejoras futuras

- **Calculadora de km** (origen→destino × tarifa + peajes que genera el gasto): por ahora el
  importe se mete a mano.
- **Subida real de fotos de recibos** (archivo, no enlace): depende de activar Supabase Storage
  → decisión transversal en el **Área 6 (Finanzas)**.

---

## Área 5 — Equipo y material (inventario)

> Bloque nuevo y **secundario**. Alcance acordado: **inventario mínimo**. No está en el roadmap
> actual (Fases 7–13) → entra en una **fase posterior** (ver nota de roadmap al final del doc).

### Tabla de resolución

| # | Necesidad | Decisión | Cómo se resuelve | Fase |
|---|---|---|---|---|
| 43 | Inventario del material (PA, monitores, cables, micros) | ❌ Nuevo | Entidad **`InventoryItem`** (mínima) | post-13 |
| 44 | De quién es cada equipo (propio vs común) | ❌ Nuevo | `InventoryItem.ownership` (`band`/`member`) + `owner_id` | post-13 |
| 45 | Estado / mantenimiento (cuerdas, parches, baterías) | ❌ Nuevo (ligero) | `InventoryItem.condition` (`ok`/`needs_check`/`broken`) | post-13 |
| 46 | Qué hay que comprar / reponer | ✅ Derivado | `InventoryItem.needs_restock` (bool) → vista "lista de la compra" filtrada | post-13 |
| 47 | Préstamos de material (quién lo tiene ahora) | ❌ Nuevo (ligero) | `InventoryItem.loaned_to_user_id` + `loaned_at` (sin historial) | post-13 |

### Entidad nueva

**`InventoryItem`** (material de la banda — inventario mínimo)
```
InventoryItem:
  id · band_id (FK)
  name        String                # "Mesa Behringer X32", "Micro SM58 #2"
  category    String                # pa | monitor | cable | mic | instrument | accessory | other
  ownership   String                # band (común) | member (de un miembro)
  owner_id    user_id   nullable    # si ownership=member, de quién es
  condition   String                # ok | needs_check | broken
  needs_restock Boolean default false # marca "hay que reponer/comprar"
  loaned_to_user_id user_id nullable  # prestado a quién (null = lo tiene la banda)
  loaned_at   DateTime  nullable     # desde cuándo
  image_url   String    nullable     # foto (enlace; subida real = mejora futura)
  notes       Text      nullable
  created_at
```

### Apoyo de UX

- **Lista de inventario** por categoría, con avatar del dueño si es de un miembro, chip de estado
  (verde/ámbar/rojo) y marca de "prestado a…".
- Vista **"Lista de la compra"** = ítems con `needs_restock = true` (cuerdas, parches que faltan).
- Acción rápida **"prestar a"** / **"devuelto"** en cada ítem.

### Permisos

- **Crear/editar/borrar ítems del inventario** → **Admin**.
- **Marcar "reponer"** y **registrar préstamo/devolución** → cualquier miembro (uso diario).
- **Ver** el inventario → cualquier miembro.

### Aplazado / mejoras futuras

- **Inventario completo**: nº de serie, valor, fecha de compra, ubicación, recordatorios de
  mantenimiento.
- **Historial de préstamos** (quién, cuándo, devuelto): por ahora solo "quién lo tiene ahora".
- Enlazar un ítem roto con su **gasto de reparación/reposición** en Finanzas.

---

## Área 6 — Finanzas

> **Núcleo** ya muy resuelto por la guía V2 (modelo Splitwise: `Transaction` + `TransactionSplit`
> + saldo neto + reparto personalizable). Aquí cerramos lo que faltaba: **liquidación**, **fondo
> común**, **cuotas**, informes y export.

### Tabla de resolución

| # | Necesidad | Decisión | Cómo se resuelve | Fase |
|---|---|---|---|---|
| 48 | Registrar gastos | ✅ Ya en la guía | `Transaction` (`type=expense`) | 11 |
| 49 | Registrar ingresos (cachés, merch, propinas, streaming) | ✅ Ya en la guía | `Transaction` (`type=income`) | 11 |
| 50 | Reparto personalizable de cada movimiento | ✅ Ya en la guía | `TransactionSplit` (editable) | 11 |
| 51 | Saldo neto por miembro (quién debe a quién) | ✅ Ya en la guía | Cálculo de balances | 11 |
| 52 | Liquidar saldos (registrar la transferencia real) | ❌ Nuevo (sube a F11) | Entidad **`Settlement`** | 11 |
| 53 | Bote común / fondo de la banda | ❌ Nuevo | **Fondo como participante** (cuenta virtual de la banda) | 11 |
| 54 | Presupuesto por proyecto (disco, gira) | ⏳ Aplazar | Etiqueta de proyecto + límite (mejora futura) | — |
| 55 | Categorías de gasto + resumen mensual/anual | ✅ Derivado | `Transaction.category` + vistas de informe | 11 |
| 56 | Exportar para impuestos / contabilidad | ❌ Nuevo (ligero) | Export **CSV** de movimientos (filtrable por fecha/categoría) | 11 |
| 57 | Cuotas mensuales de los miembros | ❌ Nuevo | Aportación al **fondo** (`Transaction` ingreso → fondo); recurrencia aplazada | 11 |
| 58 | Adjuntar tickets/facturas | ✅ Ya resuelto (Área 4) | `Attachment.transaction_id` (foto del recibo) | 11 |

### Entidades / cambios

**`Settlement`** (liquidación — pago real que ajusta saldos)
```
Settlement:
  id · band_id (FK)
  from_user_id   user_id            # quién paga
  to_user_id     user_id  nullable  # a quién (null = al fondo)
  to_fund        Boolean  default false   # el pago va al fondo común
  amount · date · note · created_by · created_at
```
> "Ana paga a Juan 30 €" → registra el movimiento y los saldos se acercan a cero. También sirve
> para aportar al fondo (`to_fund = true`).

**Fondo común (cuenta virtual de la banda).** El fondo es **un participante más** en la
contabilidad, no una tabla de movimientos aparte:
- `Transaction.paid_by` puede ser un miembro **o el fondo** (flag `paid_by_fund`) → "esto lo
  pagó el bote".
- Un split puede asignarse al **fondo** (flag `to_fund` en `TransactionSplit`) → "esta parte se
  queda en el bote".
- **Saldo del fondo** = Σ aportaciones (cuotas, ingresos destinados al fondo) − Σ gastos pagados
  desde el fondo. Se muestra junto a los saldos de los miembros.
- **Cuota mensual** (#57) = aportación de cada miembro al fondo (un `Transaction` ingreso cuyo
  destino es el fondo). La **recurrencia automática** queda aplazada (como los eventos): de
  momento se registra/duplica a mano.

```
Transaction (+ flag):     paid_by_fund   Boolean default false
TransactionSplit (+ flag): to_fund        Boolean default false
```

### Apoyo de UX

- **Panel de saldos**: lista de miembros + el **fondo**, cada uno con su saldo (verde a favor /
  rojo en contra) y botón **"liquidar"** que precarga el importe sugerido.
- **Informes**: resumen por categoría y por mes/año; botón **"exportar CSV"**.
- Al registrar un movimiento: elegir `paid_by` (miembro o fondo), reparto y **adjuntar recibo**.

### Permisos

- **Registrar/editar finanzas, repartos, liquidaciones y cuotas** → **Admin** (matriz V2).
- **Ver** su saldo, el de la banda y el del fondo → cualquier miembro.

### Aplazado / mejoras futuras

- **Presupuesto por proyecto** (#54): agrupar movimientos bajo "Disco 2026" / "Gira verano" con
  un límite y seguimiento.
- **Cuotas recurrentes automáticas** (generar la cuota cada mes): por ahora manual/duplicar.

---

## 🔌 Decisión transversal — Subida de archivos (Supabase Storage)

> Acordado **activar almacenamiento real** en una **fase dedicada**. Hasta entonces, los campos
> de tipo `image_url`/`url`/`Attachment` aceptan **enlaces**; al activar Storage, pasan a admitir
> **subida directa** sin cambiar el modelo conceptual.

- **Qué habilita:** fotos de recibos (Área 4/6), imágenes de backline/stage plot (Área 3),
  grabaciones de ensayo (Área 2), avatares (perfil/banda), y futuros adjuntos.
- **Infra:** bucket(s) de Supabase Storage, políticas de acceso **por banda** (mismo principio
  multi-tenant que el resto: solo miembros de la banda acceden a sus archivos), límites de tamaño
  y tipos permitidos.
- **Diseño:** `Attachment` y los campos `*_url` ganan un origen "archivo subido" además de
  "enlace externo". Una sola implementación sirve para todas las áreas.
- **Fase:** nueva fase de infraestructura (ver nota de roadmap al final). Es **prerequisito
  cómodo** de varias features de medios, pero no bloquea el núcleo (que funciona con enlaces).

---

## Área 7 — Comunicación interna

> **Núcleo** ya resuelto por la guía V2 con `Message` (chat general = `event_id null`; hilo de
> evento = `event_id`; notas = `is_pinned`). Aquí añadimos **encuestas**, **menciones** y un
> **centro de notificaciones in-app**.

### Tabla de resolución

| # | Necesidad | Decisión | Cómo se resuelve | Fase |
|---|---|---|---|---|
| 59 | Chat general de la banda | ✅ Ya en la guía | `Message` con `event_id = null` | 12 |
| 60 | Comentarios por evento (puedo/no puedo + alternativas) | ✅ Ya en la guía | `Message` con `event_id` | 12 |
| 61 | Notas fijadas (avisos importantes) | ✅ Ya en la guía | `Message.is_pinned` (admin) | 12 |
| 62 | Encuestas / votaciones | ❌ Nuevo | **`Poll`** + `PollOption` + `PollVote` (dentro del chat) | 12 |
| 63 | Menciones a un miembro (@Ana) | ❌ Nuevo | Parseo de `@` en `Message` → notificación | 12 |
| 64 | Notificaciones (evento nuevo, cambio de hora, alguien no puede) | ❌ Nuevo | **Centro in-app** (`Notification` + campana) | 12 |

### Entidades nuevas

**`Poll` / `PollOption` / `PollVote`** (encuestas en el chat)
```
Poll:
  id · band_id (FK) · message_id (FK, nullable: vive como un mensaje del chat)
  question · created_by · closes_at (nullable) · allow_multiple (bool) · created_at
PollOption:  id · poll_id (FK) · text · position
PollVote:    id · poll_option_id (FK) · user_id · created_at
  Único (poll_id, user_id) salvo que allow_multiple = true
```
> Resuelve "¿qué día ensayamos?" (opciones = días) y "¿aceptamos el bolo?" (sí/no). Los
> resultados se ven en vivo en el chat.

**`Notification`** (centro de avisos in-app)
```
Notification:
  id · band_id (FK) · user_id (destinatario)
  type     String   # new_event | event_changed | event_cancelled | mention |
                     # attendance_change | new_poll | settlement | pinned_note | ...
  title · body · nullable
  ref_type · ref_id · nullable   # a qué apunta (evento, mensaje, transacción…) para enlazar
  is_read  Boolean default false
  created_at
```
> Una **campana con badge** lista los avisos. Se generan en los eventos clave: crear/cambiar/
> cancelar un evento, una @mención, un cambio de asistencia relevante, una nueva encuesta, una
> liquidación, una nota fijada.

**Menciones (#63).** Al guardar un `Message`, se detectan los `@usuario` (miembros de la banda)
y se crea una `Notification` (`type=mention`) para cada mencionado; en el texto se resalta. (Si
hiciera falta, un join `MessageMention(message_id, user_id)`; de inicio basta con generar la
notificación.)

### Apoyo de UX

- **Campana** en la barra superior con contador de no leídas; al pulsar, lista que enlaza a su
  origen (evento, mensaje…).
- En el chat, **crear encuesta** desde el mismo compositor; resultados con barras de % y quién votó.
- Autocompletado de **@miembros** al escribir `@`.

### Permisos

- **Escribir, crear encuestas, votar, mencionar** → cualquier miembro.
- **Fijar/desfijar notas y borrar mensajes ajenos** → **Admin** (matriz V2).
- Cada miembro ve **solo sus** notificaciones.

### Aplazado / mejoras futuras

- **Push del navegador (PWA)**: avisar fuera de la app (claves VAPID + service worker). La app ya
  es PWA, así que es un añadido natural sobre el centro in-app.
- **Notificaciones por email**: dependen de configurar el email del proyecto (T-046/T-047).
- **Tiempo real** del chat (Supabase Realtime): la guía V2 ya lo contempla como mejora posterior
  al refresco periódico.

---

## Área 8 — Miembros y organización

> Invitaciones por código, roles y perfil ya están en la guía V2 (`BandInvite`,
> `BandMembership`, `MusicianProfile`). Aquí añadimos el **rol invitado**, la **baja blanda** con
> histórico, y el rol se amplía a tres.

### Tabla de resolución

| # | Necesidad | Decisión | Cómo se resuelve | Fase |
|---|---|---|---|---|
| 65 | Invitar miembros (por código/enlace) | ✅ Ya en la guía | `BandInvite` | 7 |
| 66 | Roles y permisos | ✅ Ampliar | `BandMembership.role` → `admin` / `member` / **`guest`** | 7 |
| 67 | Perfil de cada músico (instrumentos, rol en la banda) | ✅ Ya en la guía | `MusicianProfile` + `BandMembership.instrument` | 7 |
| 68 | Sustitutos / de refuerzo (deps, invitados) | ❌ Nuevo | Rol **`guest`** (membresía con acceso reducido) | 7 |
| 69 | Expulsar / dar de baja a un miembro | ❌ Nuevo (baja blanda) | `BandMembership.status` = `left` + `left_at` (no se borra) | 7 |
| 70 | Histórico de quién ha estado en la banda | ✅ Derivado | Membresías con `status=left` siguen visibles en histórico | 7 |
| 71 | Disponibilidad recurrente de cada uno | ⏳ Aplazar | Se usa la asistencia por evento (`EventAttendance`) + chat | — |

### Cambios de modelo (aditivos)

```
BandMembership (+ campos / ampliación):
  role     String   # admin | member | guest   (antes solo admin|member)
  status   String   default 'active'   # active | left
  left_at  DateTime nullable            # cuándo causó baja (baja blanda)
```
> **Baja blanda:** al expulsar/darse de baja, `status='left'` + `left_at`. La fila **permanece**
> para que el miembro siga apareciendo en finanzas, eventos y mensajes pasados → **cero
> corrupción de histórico**. El acceso queda cortado (deja de pasar `require_band_member`).

### El rol `guest` (invitado / sustituto)

- Pensado para **deps y refuerzos** de un bolo concreto.
- **Acceso reducido:** ve la **agenda** y el **repertorio/setlists** necesarios para tocar,
  **confirma asistencia** y **comenta**; **no** ve las finanzas completas (sí su propio saldo si
  participa en algún reparto), **no** edita repertorio ni gestiona nada.
- Un admin lo invita igual que a cualquiera (`BandInvite` con `role_to_grant=guest`) y puede
  **promoverlo** a `member` o darle de baja.

### Apoyo de UX

- **Lista de miembros**: activos arriba (con rol e instrumento), invitados marcados como tales,
  y un apartado **"Antiguos miembros"** (los `left`).
- Acciones de admin por miembro: **cambiar rol**, **dar de baja**, **reactivar**.

### Permisos

- **Invitar, expulsar, cambiar roles** → **Admin** (matriz V2).
- Un **guest** no puede gestionar nada; acceso de solo-lectura ampliado a lo imprescindible.

### Aplazado / mejoras futuras

- **Disponibilidad recurrente** (días/franjas habituales): de momento se resuelve con la
  asistencia por evento.
- **Transferir la propiedad / "admin principal"** de la banda; co-fundadores.

---

## Área 9 — Promoción y marketing

> Área **satélite** → fases posteriores. Reusa `BandResource`/`Attachment` para material promo.
> Lo nuevo: **perfil/EPK de la banda** y una **agenda de contactos** (CRM ligero).

### Tabla de resolución

| # | Necesidad | Decisión | Cómo se resuelve | Fase |
|---|---|---|---|---|
| 72 | Calendario de publicaciones en redes | ⏳ Versión futura | — | — |
| 73 | Material promocional del bolo (carteles, flyers, posts) | ✅ Reusar | `BandResource`/`Attachment` (`kind=promo`) en el evento + `is_promoting`/`promo_notes` (V2) | 10 |
| 74 | Press kit / EPK (bio, fotos, vídeos, enlaces) | ❌ Nuevo | **Perfil de banda + EPK** (campos en `Band` + galería `BandResource`) | post-13 |
| 75 | Contactos de prensa / salas / promotores | ❌ Nuevo | Entidad **`Contact`** (CRM ligero); `Venue` enlaza a `Contact` | post-13 |
| 76 | Enlaces a redes sociales y plataformas | ❌ Nuevo | `Band.social_links` (JSON) | post-13 |
| 77 | Seguimiento de seguidores / métricas | ⏳ Versión futura | — (requiere integraciones externas) | — |

### Cambios / entidades

```
Band (+ campos de perfil/EPK; nullable):
  bio           Text     # biografía para el EPK / página pública
  social_links  JSON     # {instagram, youtube, spotify, bandcamp, web, ...}
  # fotos y vídeos del EPK = BandResource (kind=photo / promo / video)

Contact (agenda de contactos — CRM ligero):
  id · band_id (FK)
  name · type (venue | promoter | press | other)
  phone · email · nullable
  notes · created_at

Venue (+ enlace):
  contact_id  FK contacts  nullable   # la sala puede apuntar a un contacto de la agenda
```

### Apoyo de UX

- **Pestaña EPK** de la banda: bio, foto/galería, enlaces a redes/plataformas, vídeos. Reutilizable
  como **página pública** (Área 14).
- **Agenda de contactos** filtrable por tipo (sala/promotor/prensa), con acceso rápido a llamar/
  escribir; desde un bolo se puede enlazar la sala a su contacto.

### Permisos

- **Editar perfil/EPK, contactos y material promo** → **Admin**.
- **Ver** → cualquier miembro (el EPK público, además, sin login en su versión web).

### Aplazado / versión futura

- **Calendario de publicaciones** (#72) y **métricas de seguidores** (#77): gestión de redes ≈
  otro producto; requiere integraciones con APIs externas. Fuera del alcance por ahora.

---

## Área 10 — Booking y contratación

> Se apoya en el **evento** (un bolo potencial es un `Event` en estado temprano) y en la **agenda
> de contactos** (Área 9). Lo nuevo: ampliar el estado, recordatorios y plantillas de email.

### Tabla de resolución

| # | Necesidad | Decisión | Cómo se resuelve | Fase |
|---|---|---|---|---|
| 78 | Pipeline de bolos potenciales (contactado/negociando/cerrado) | ❌ Ampliar | `Event.status` con etapas previas a la confirmación | 10 |
| 79 | Disponibilidad de la banda para ofertar | ✅ Derivado | Huecos de la agenda (días sin eventos) | 10 |
| 80 | Plantillas de email para ofrecerse a salas | ❌ Nuevo | Entidad **`EmailTemplate`** (texto reutilizable) | post-13 |
| 81 | Recordatorios de seguimiento ("volver a escribir") | ❌ Nuevo | `Event.follow_up_at` → genera `Notification` | 10 |

### Cambios / entidades

```
Event (+ ampliación de estado y seguimiento):
  status        String   # lead | contacted | negotiating | confirmed | done | cancelled
                         # (sustituye al scheduled|done|cancelled de la V2; 'confirmed' = agendado)
  follow_up_at  DateTime nullable   # próxima fecha de seguimiento → recordatorio

EmailTemplate (plantillas reutilizables):
  id · band_id (FK) · name · subject · body · created_at
```
> **Pipeline:** un bolo "nace" como `lead`/`contacted`, pasa por `negotiating` y, al cerrarse,
> `confirmed` → ya es un concierto normal con todos sus datos (Área 3). Una **vista tablero**
> (kanban) agrupa los eventos por estado.
> **Recordatorio:** `follow_up_at` dispara una `Notification` ("toca volver a escribir a la sala
> X"), reusando el centro de avisos del Área 7.

### Apoyo de UX

- **Tablero de booking** (columnas por estado) además de la vista calendario/lista de la agenda.
- En cada bolo potencial: contacto de la sala (Área 9), notas de negociación (chat/hilo del
  evento) y **fecha de seguimiento**.
- **Plantillas de email**: se eligen y se copian (o se envían cuando el email esté configurado);
  pueden interpolar datos del bolo (sala, fecha, caché).

### Permisos

- **Gestionar pipeline, recordatorios y plantillas** → **Admin**.
- **Ver** el tablero y los bolos potenciales → cualquier miembro.

### Aplazado / mejoras futuras

- **Envío real de los emails** desde la app: depende de configurar el email (T-046/T-047).
- **Sugerir fechas libres** automáticamente al negociar (a partir de la disponibilidad derivada).

---

## Área 11 — Grabación y producción

> Área satélite → fase posterior. **Módulo ligero**: un `Project` agrupa canciones, tareas y
> adjuntos. Las tareas usan una entidad **`Task` genérica** (sirve para cualquier to-do de la
> banda, no solo grabar).

### Tabla de resolución

| # | Necesidad | Decisión | Cómo se resuelve | Fase |
|---|---|---|---|---|
| 82 | Proyectos de grabación (maqueta/EP/disco/single) | ❌ Nuevo | Entidad **`Project`** + `ProjectSong` | post-13 |
| 83 | Tareas por canción (grabar batería, mezclar, masterizar) | ❌ Nuevo | Entidad **`Task`** genérica (con `assignee_id`) | post-13 |
| 84 | Estado de cada track en producción | ✅ Derivado | `Task.status` por canción del proyecto | post-13 |
| 85 | Subir/compartir tomas y mezclas para feedback | ✅ Reusar | `Attachment` (enlace → archivo con Storage) ligado al proyecto/canción | post-13 |
| 86 | Fechas de lanzamiento y distribución | ❌ Nuevo (ligero) | `Project.release_date` | post-13 |

### Entidades nuevas

**`Project`** (proyecto de grabación)
```
Project:
  id · band_id (FK)
  type        String   # demo | ep | album | single
  title · status (planning | recording | mixing | mastering | released)
  release_date DateTime nullable
  notes · created_at
ProjectSong:  id · project_id (FK) · song_id (FK)   # canciones del proyecto
```

**`Task`** (tarea genérica — reutilizable en toda la app)
```
Task:
  id · band_id (FK)
  title · description (nullable)
  assignee_id  user_id   nullable    # responsable
  status       String                # todo | doing | done
  due_at       DateTime  nullable
  project_id   FK projects  nullable  # ligada a un proyecto de grabación…
  song_id      FK songs     nullable  # …o a una canción…
  event_id     FK events    nullable  # …o a un evento (preparativos, etc.)
  created_by · created_at
```
> **Task vs ChecklistItem:** el `ChecklistItem` (Área 3) es la lista rápida *de un bolo*
> (marcar/llevar cosas el día del concierto); `Task` es la **tarea de trabajo** con responsable,
> estado y fecha, que vive a nivel de banda/proyecto/canción. Tener `Task` genérica abre la
> puerta a un **tablero de tareas** de la banda para cualquier cosa, no solo grabar.

```
Attachment (+ campo):  project_id  FK projects  nullable   # tomas/mezclas del proyecto
```

### Apoyo de UX

- **Ficha de proyecto**: canciones incluidas, tablero de tareas (todo/doing/done) con
  responsables, adjuntos (tomas/mezclas) y fecha de lanzamiento.
- **Tablero de tareas** de la banda (filtrable por proyecto/canción/evento/responsable).

### Permisos

- **Crear proyectos y tareas, asignar** → **Admin**; **mover su tarea** y comentar → cualquier
  miembro. (Ajustable; producción suele coordinarla un admin.)

### Aplazado / mejoras futuras

- **Estados detallados por pista**, versiones de mezcla, distribución automática a plataformas.
- Enlazar el proyecto con su **presupuesto** (retoma el "presupuesto por proyecto" aplazado en
  Finanzas, Área 6, #54).

---

## Área 12 — Legal y administrativo

> Área satélite → fase posterior. Casi todo es **guardar documentos** (reusa `Attachment` como
> repositorio) + unos pocos **datos fiscales de la banda**. Introduce una novedad de permisos:
> contenido **solo-admin** incluso para ver.

### Tabla de resolución

| # | Necesidad | Decisión | Cómo se resuelve | Fase |
|---|---|---|---|---|
| 87 | Datos fiscales de la banda / miembros | ❌ Nuevo (solo banda) | Campos fiscales en `Band` (los de miembros se aplazan) | post-13 |
| 88 | Contratos de actuación firmados | ✅ Reusar | `Attachment` (`kind=contract`), repositorio de documentos | post-13 |
| 89 | Registro de obras (derechos de autor, SGAE) | ✅ Reusar (documento) | `Attachment` (`kind=registration`) | post-13 |
| 90 | Acuerdos internos (reparto, propiedad de canciones) | ✅ Reusar (documento) | `Attachment` (`kind=agreement`) | post-13 |
| 91 | Documentos importantes (seguros, permisos) | ✅ Reusar | `Attachment` (`kind=insurance`/`legal`) | post-13 |

### Cambios / modelo

```
Band (+ datos fiscales; nullable, SENSIBLES → solo-admin):
  legal_name     String   # nombre/razón fiscal
  tax_id         String   # NIF/CIF
  payout_account String   # cuenta para cobrar cachés (IBAN)

Attachment  →  ya soporta band_id + kind: el repositorio de documentos es la vista de
               Attachments de la banda sin event/song/transaction, agrupados por kind
               (contract | registration | agreement | insurance | legal | other).
```

### Novedad de permisos — contenido solo-admin

> Hasta ahora la regla era "los miembros ven todo". Los **datos fiscales y documentos legales**
> son la **excepción**: visibles y editables **solo por admins**. Esto se añade a la matriz como
> una categoría nueva de visibilidad (no todo lo de la banda es para todos los miembros).

### Apoyo de UX

- **Repositorio de documentos** de la banda, agrupado por tipo (contratos, registros, acuerdos,
  seguros), con buscador. Acceso restringido a admins.
- **Datos fiscales** de la banda en ajustes, solo-admin, para autocompletar contratos/facturas.

### Permisos

- **Ver/editar datos fiscales y documentos legales** → **solo Admin**.
- Resto de miembros: **sin acceso** a esta sección (a diferencia del resto de la app).

### Aplazado / mejoras futuras

- **Datos fiscales personales** de cada miembro (para facturar cachés con retención): requiere
  tratamiento de datos personales con más garantías.
- **Créditos/royalty splits estructurados** por canción (quién compuso, %): por ahora, documento.
- **Firma electrónica** de contratos dentro de la app.

---

## Área 13 — Merchandising

> Área satélite → fase posterior. **Módulo ligero**: catálogo con variantes (talla) y stock; las
> **ventas** entran como **ingreso** en Finanzas (reusa la división de cuentas).

### Tabla de resolución

| # | Necesidad | Decisión | Cómo se resuelve | Fase |
|---|---|---|---|---|
| 92 | Catálogo de merch (camisetas, CD, vinilos, pegatinas) | ❌ Nuevo | Entidad **`MerchProduct`** | post-13 |
| 93 | Stock por talla / producto | ❌ Nuevo | **`MerchVariant`** (talla + stock) | post-13 |
| 94 | Ventas en cada bolo y online | ✅ Reusar Finanzas | `Transaction` (ingreso, `category=merch`, `event_id`), desglose opcional | post-13 |
| 95 | Quién custodia / transporta el merch | ✅ Reusar patrón | `MerchProduct.custodian_id` (responsable) | post-13 |

### Entidades nuevas

```
MerchProduct:
  id · band_id (FK)
  name · type (tshirt | cd | vinyl | sticker | other)
  price        Decimal  nullable   # precio de referencia
  custodian_id user_id  nullable   # quién lo custodia/transporta
  image_url    String   nullable
  notes · created_at
MerchVariant:
  id · product_id (FK) · label (talla: S/M/L… o "—" si no aplica) · stock_qty (Integer)
```

### Apoyo de UX

- **Catálogo** con foto, precio, variantes y stock; aviso cuando el stock está bajo.
- Tras el bolo: **"registrar ventas de merch"** → crea el ingreso ligado al evento (con desglose
  opcional por producto) y, si quieres, ajustas el stock a mano.
- Cada producto muestra **quién lo lleva** (custodio).

### Permisos

- **Gestionar catálogo, stock y ventas** → **Admin**.
- **Ver** catálogo/stock → cualquier miembro.

### Aplazado / mejoras futuras

- **Venta por unidad** con descuento automático de stock y **tienda online**.
- Informes de **qué se vende más** y por canal.

---

## Área 14 — Comunidad / fans

> Lo más **hacia fuera** (público, sin login). Reusa el **EPK** (Área 9) y los **eventos
> confirmados** (Área 10). El envío de correos depende del email pendiente.

### Tabla de resolución

| # | Necesidad | Decisión | Cómo se resuelve | Fase |
|---|---|---|---|---|
| 96 | Lista de correo de fans | ❌ Nuevo (captar) | **`FanSubscriber`** (alta desde la web; envío después) | post-13 |
| 97 | Mensajes / solicitudes de fans | ❌ Nuevo | **`FanMessage`** (formulario público → notificación a la banda) | post-13 |
| 98 | Página pública con próximos conciertos | ❌ Nuevo | Web pública por banda (EPK + eventos `confirmed` futuros) | post-13 |

### Cambios / entidades

```
Band (+ campos de publicación; nullable):
  public_slug  String  unique   # /b/<slug> de la página pública
  is_public    Boolean default false   # publicada sí/no

FanSubscriber:
  id · band_id (FK) · email · source (nullable) · created_at
  Único (band_id, email)

FanMessage:
  id · band_id (FK) · name · email · body · is_read (bool) · created_at
```

### Apoyo de UX

- **Página pública** (`/b/<slug>`): bio, fotos, enlaces a plataformas (EPK) + **próximos
  conciertos** (autogenerados de los eventos confirmados, con sala y fecha) + formulario de
  **suscripción** y de **contacto**.
- En la app, bandeja de **mensajes de fans** (genera `Notification`) y lista de **suscriptores**
  (exportable; base de la futura newsletter).

### Permisos

- **Publicar/despublicar la página, ver suscriptores y mensajes** → **Admin**.
- La **página pública** es accesible sin login (respeta `is_public`); solo muestra datos marcados
  como públicos (nunca finanzas, miembros, etc.).

### Aplazado / mejoras futuras

- **Envío de newsletters** a los suscriptores: depende del email (T-046/T-047).
- **Venta de entradas** / RSVP a conciertos desde la página pública.
- Dominio propio para la página de la banda.

---

# 🗺️ Consolidación

## C.1 — Roadmap ampliado y priorización fina

El roadmap de la guía V2 (**Fases 7–13**) es el **núcleo** y va primero, en ese orden, porque
todo cuelga de él. Las áreas satélite añaden las **Fases 14–21**. Las he **reordenado por valor
para una banda y por dependencias**, y para **no repetir trabajo** (hacer la infraestructura justo
antes de quien la necesita).

### Núcleo (sin cambios respecto a la V2)

| Fase | Nombre | Áreas |
|---|---|---|
| 7 | Identidad + núcleo de banda (auth multi-tenant) | 8 (parte) |
| 8 | Repertorio | 1 |
| 9 | Setlists de banda | (setlists) |
| 10 | Agenda (eventos) | 2, 3 (parte) |
| 11 | Finanzas con división | 4, 6 |
| 12 | Comunicación (chat + notas + notificaciones) | 7 |
| 13 | App shell (nav TÚ/BANDA) + sistema de diseño + rebranding BandFlow | — |

### Fases satélite — orden recomendado

| Fase | Nombre | Área | Valor | Depende de | Esfuerzo |
|---|---|---|:---:|---|:---:|
| **14** | **Booking** (pipeline + recordatorios + plantillas) | 10 | 🟢 Alto | F10, F12 (notif.) | Bajo |
| **15** | **Almacenamiento (Supabase Storage)** | transversal | 🟡 Infra | — | Medio |
| **16** | **Promoción + EPK + Contactos** | 9 | 🟢 Alto | F15 (fotos) | Medio |
| **17** | **Página pública + Fans** | 14 | 🟢 Alto | F16 (EPK) | Medio |
| **18** | **Inventario** | 5 | 🟡 Medio | F15 (fotos, opc.) | Bajo |
| **19** | **Producción** (`Project` + `Task`) | 11 | 🟡 Medio | F15 (tomas) | Medio |
| **20** | **Merch** | 13 | 🟡 Medio | F11, F15 (fotos) | Bajo |
| **21** | **Legal/administrativo** | 12 | ⚪ Variable | F15 (documentos) | Bajo |

**Por qué este orden:**
- **Booking primero (14):** lo que más mueve la aguja de una banda es **conseguir bolos**. Casi no
  añade modelo (amplía `Event.status` + `EmailTemplate` + reusa `Notification` de F12). Máximo
  valor, mínimo coste.
- **Storage segundo (15):** es infraestructura. Hacerlo **antes** de las fases con imágenes (EPK,
  inventario, merch, documentos) evita construir la subida con enlaces y **rehacerla** luego →
  cumple tu objetivo de *no repetir tareas*. Booking no usa medios, por eso va antes.
- **EPK (16) → Página pública (17):** presencia exterior; la web pública **reusa** el EPK, así que
  van seguidas.
- **Inventario / Producción / Merch / Legal (18–21):** valor medio o dependiente de la banda; se
  apoyan en Storage ya listo.

> El **detalle T-NNN** se abre en `harness/ROADMAP.md` al aprobar cada fase. El orden 14–21 es
> **reordenable**; Inventario (18) es independiente y puede adelantarse si te corre prisa.

## C.2 — Matriz de permisos actualizada

Amplía la de la guía V2 con el rol **`guest`** y la categoría **solo-admin**.

| Acción | Admin | Miembro | Invitado (guest) |
|---|:---:|:---:|:---:|
| Ver repertorio, setlists, agenda | ✅ | ✅ | ✅ (lo necesario) |
| Reproducir canciones/setlists | ✅ | ✅ | ✅ |
| Crear/editar repertorio y setlists | ✅ | ✅ | ❌ |
| Crear/editar/borrar eventos | ✅ | ❌ | ❌ |
| Confirmar asistencia · comentar · chat · encuestas | ✅ | ✅ | ✅ |
| Marcar ítems de checklist / repasada-pendiente | ✅ | ✅ | ✅ |
| Ver finanzas de la banda | ✅ | ✅ | ❌ (solo su saldo si participa) |
| Registrar/editar finanzas, repartos, liquidaciones | ✅ | ❌ | ❌ |
| Invitar / expulsar / cambiar roles | ✅ | ❌ | ❌ |
| Inventario / merch / proyectos / contactos: crear-editar | ✅ | ❌ | ❌ |
| **Datos fiscales y documentos legales (ver y editar)** | ✅ | ❌ | ❌ |

> **Dos novedades respecto a la V2:** (1) el rol **guest** con acceso reducido; (2) los **datos
> fiscales/legales** son la **excepción** a "los miembros ven todo" → **solo-admin**.

## C.3 — Catálogo de entidades nuevas (todas las áreas)

Resumen para dimensionar el modelo. Todo es **aditivo** sobre la guía V2; nada rompe lo existente.

**Núcleo (guía V2):** `MusicianProfile`, `Band`, `BandMembership`, `BandInvite`, `Event`,
`EventAttendance`, `Transaction`, `TransactionSplit`, `Message` · + `Song.band_id`,
`Setlist.band_id`.

**Añadidas en esta especificación funcional:**

| Entidad | Área | Para qué |
|---|---|---|
| (campos en `Song`) | 1 | key, compás, afinación, capo, estado, tags, duración, referencia, notas |
| `EventSong` | 2 | Orden del día del ensayo / qué se tocó |
| `Attachment` | 2 (genérica) | Adjuntos por enlace/archivo (evento, canción, transacción, proyecto) |
| `Venue` | 3 | Salas reutilizables |
| `BandResource` + `EventResource` | 3 | Riders/backline/stage plot reutilizables |
| `ChecklistTemplate` + `ChecklistTemplateItem` + `ChecklistItem` | 3/4 | Checklist de bolo (con responsable) |
| (campos en `Event`) | 3/4/10 | Cronograma, sala, logística, estado-pipeline, follow-up |
| `Settlement` | 6 | Liquidación de saldos |
| (fondo: flags en `Transaction`/`TransactionSplit`) | 6 | Bote común como participante |
| `Notification` | 7 | Centro de avisos in-app |
| `Poll` + `PollOption` + `PollVote` | 7 | Encuestas en el chat |
| (campos en `BandMembership`) | 8 | Rol `guest`, baja blanda (status/left_at) |
| (campos en `Band`) | 9/12/14 | EPK (bio, social_links), fiscales, public_slug |
| `Contact` | 9 | Agenda de contactos (CRM ligero) |
| `EmailTemplate` | 10 | Plantillas de email |
| `Project` + `ProjectSong` | 11 | Proyectos de grabación |
| `Task` | 11 (genérica) | Tareas con responsable (producción y cualquier to-do) |
| `InventoryItem` | 5 | Inventario de material |
| `MerchProduct` + `MerchVariant` | 13 | Catálogo de merch |
| `FanSubscriber` + `FanMessage` | 14 | Lista de correo y mensajes de fans |

> **Candidatos a molde** (`../app-skeleton`, sinergia con SaaS tatuadores): `Attachment`,
> `Notification`, `Task`, `Contact`, `ChecklistTemplate`, el **fondo común** y el **rol guest +
> baja blanda** son agnósticos al dominio musical → se diseñan genéricos (ver §11 de la guía V2).

---

## C.4 — Revisión crítica (incoherencias, simplificaciones, convenciones)

Repaso del documento completo para dejarlo **pulido antes de tocar código**: resolver
contradicciones, quitar sobre-ingeniería y fijar reglas transversales que **evitan errores y
trabajo repetido**.

### C.4.1 — Incoherencias detectadas y resueltas

| # | Incoherencia | Resolución |
|---|---|---|
| 1 | `Event.status` definido distinto en V2 (`scheduled\|done\|cancelled`) y aquí (`lead…confirmed…`) | **Unificado** al enum ampliado en **ambos** documentos. Semántica **por tipo**: `lead/contacted/negotiating` solo para `concert` (pipeline de booking); `rehearsal`/`other` nacen en `confirmed`. `scheduled` (V2) ≡ `confirmed`. |
| 2 | `BandResource` vs `Attachment` se solapan (stage plot y promo aparecían como "uno u otro") | **Regla fija:** si es **reutilizable** entre varios eventos → `BandResource` (rider, backline, stage plot, galería EPK). Si es un **archivo/enlace puntual** de **una** entidad → `Attachment` (contrato de *este* bolo, grabación de *este* ensayo, recibo de *este* gasto). → **Stage plot = `BandResource`**; **promo de un bolo = `Attachment`** (salvo plantilla reutilizable). |
| 3 | `BandResource.kind` no incluía `photo/promo/video` que usa el EPK (Área 9) | **Enum ampliado** (corregido arriba). |
| 4 | `Event.location` (texto, V2) vs `Event.venue_id` (Área 3) | `venue_id` para **conciertos** (la dirección sale de `Venue`); `location` libre para `rehearsal`/`other`. No duplicar. |
| 5 | Dos formas de colgar canciones de un evento: `EventSong` (ensayo) y `setlist_id`→`SetlistItem` (concierto) | **No se mezclan:** las canciones de un **concierto** = su **setlist**; las de un **ensayo** = `EventSong` (lista ad-hoc). Documentado. |
| 6 | `Song.reference_url` vs `Attachment(song_id)` | `reference_url` = el **enlace canónico** de referencia (1). `Attachment(song)` = material extra. |

### C.4.2 — Simplificaciones (menos riesgo, menos código)

1. **Invitados (`guest`) fuera de finanzas en v1.** Quito el matiz "ve su saldo si participa":
   complica la autorización financiera. En v1 **un guest no participa en repartos**; pagar a un
   dep = **gasto normal con nota** (p. ej. "caché dep batería"), no un split. Si en el futuro hace
   falta, se añade entonces.
2. **`Attachment` con FKs explícitas, no polimórfico.** Mantiene integridad referencial. Regla:
   `band_id` **siempre**; **como mucho uno** de `event_id`/`song_id`/`transaction_id`/`project_id`
   (ninguno = documento a nivel banda, p. ej. legal). Un `CHECK`/validación garantiza esa regla.

### C.4.3 — Convenciones transversales (decididas una vez, aplican a todo)

> Estas reglas **se escriben una sola vez** y se aplican a todas las entidades nuevas. Evitan
> inconsistencias tabla a tabla (la causa nº1 de bugs y de rehacer trabajo).

- **Dinero:** `Decimal(10,2)`, **una sola divisa por banda** → `Band.currency` (default `EUR`).
  Sin multi-divisa en v1. Aplica a `Transaction.amount`, `Settlement.amount`, `MerchProduct.price`,
  `share_amount`.
- **Redondeo de repartos:** al dividir (p. ej. 100 € entre 3), los céntimos sobrantes los **absorbe
  el último split** para que Σ shares = `amount` **exacto**. Regla del servicio de balances.
- **Borrado:** *soft delete* (`deleted_at`) en lo que tiene **valor/histórico**: `Band`, `Song`,
  `Setlist`, `Event`, `Message`, `Transaction`, `Settlement`, `Venue`, `Project`, `MerchProduct`,
  `InventoryItem`. Las **filas hijas/listas** (`*Split`, `*Item`, `*Vote`, `EventAttendance`,
  `EventSong`) se borran en duro con su padre. **Financieros nunca se borran físicamente.**
- **Índices:** `band_id` **indexado en toda tabla con ámbito de banda** (rendimiento + consultas de
  aislamiento). Toda FK, indexada.
- **Multi-tenant (regla de oro, V2 §5):** cada ruta de banda pasa por `require_band_member`/
  `require_band_admin` y filtra por `band_id`. **Test obligatorio de aislamiento** ("usuario ajeno
  → 403/404") por cada ruta.
- **Timestamps:** `created_at`/`updated_at` en todas; en **UTC**. (Zona horaria de visualización =
  futura `Band.timezone`.)
- **Servicio único de balances:** **una sola** función calcula los saldos integrando `Transaction`
  + `TransactionSplit` + flags de **fondo** + `Settlement`. Fórmula documentada y **tests
  obligatorios** con casos: gasto, ingreso, aportación al fondo, gasto pagado por el fondo,
  liquidación → **todo cuadra a cero**. Es la zona de mayor riesgo de bug.

### C.4.4 — Disparadores de notificación (para implementación consistente)

Tabla única para que `Notification` se genere igual en todas las features (Fase 12 en adelante):

| Disparador | Destinatarios | `type` |
|---|---|---|
| Evento creado | Miembros de la banda | `new_event` |
| Evento cambiado (hora/lugar) o cancelado | Miembros (o quien confirmó) | `event_changed` / `event_cancelled` |
| @mención en un mensaje | El/los mencionados | `mention` |
| Alguien marca "no puedo" en un evento | Admins | `attendance_change` |
| Nueva encuesta | Miembros | `new_poll` |
| Liquidación que te afecta | `from_user` y `to_user` | `settlement` |
| Nota fijada | Miembros | `pinned_note` |
| `follow_up_at` de un bolo vencido | Admins | `follow_up` |
| Mensaje de fan (web pública) | Admins | `fan_message` |

### C.4.5 — Huecos anotados (no bloqueantes)

- **Edición concurrente** del repertorio (varios miembros a la vez): v1 = "el último gana"; revisar
  si hace falta bloqueo/optimistic locking si da problemas reales.
- **Zona horaria** de eventos: v1 asume hora local; `Band.timezone` cuando haya bandas en husos
  distintos.
- **i18n:** la app es en **español**; sin multidioma por ahora.
- **Límites de plan SaaS** (nº de bandas, cuota de Storage): modelo de negocio, fuera de alcance;
  anotado para cuando toque monetizar.

---

## C.5 — Detalle de la Fase 7 (núcleo de banda)

> Fase **fundacional**: identidad + multi-tenant. Todo lo demás cuelga de aquí. Sigue el bucle de
> 7 pasos de `CLAUDE.md`; cada tarea **no está hecha** hasta `doctor.py` verde + test que la cubre
> (incluido el **test de aislamiento** obligatorio). Los códigos `F7-n` se traducen a `T-NNN` al
> abrirlos en `harness/ROADMAP.md`.

| Tarea | Entrega | Verificación (test) |
|---|---|---|
| **F7-1 · Migración aditiva** | Tablas `musician_profiles`, `bands`, `band_memberships`, `band_invites` + índices `band_id`/FKs. Alembic `--autogenerate`, revisar SQL, `alembic check` limpio. Aplicar a Postgres con **pooler 5432**. | `alembic check` sin drift; `doctor.py` arranca con la BD nueva. |
| **F7-2 · Modelos + schemas** | Modelos SQLAlchemy y schemas Pydantic de las 4 entidades. `role` (`admin\|member\|guest`), `status` (`active\|left`), `left_at`. | Unit: validación de schemas (roles/estados válidos). |
| **F7-3 · Auth multi-tenant** | Dependencias `require_band_member(band_id)` (404/403) y `require_band_admin(band_id)` (403). Reusan `get_current_user` + modo test. | Unit/e2e: miembro→OK, ajeno→404, no-admin en ruta admin→403. |
| **F7-4 · Endpoints banda** | Crear banda (creador→`admin`), listar "mis bandas", ver, editar, borrar (soft delete). | e2e: crear→aparece en mis bandas; **aislamiento** (ajeno no la ve/edita). |
| **F7-5 · Endpoints membresía** | Listar miembros, cambiar rol, dar de baja (**baja blanda**), reactivar. | e2e: baja → pierde acceso pero sigue en histórico; cambiar rol respeta permisos. |
| **F7-6 · Invitaciones** | Generar `BandInvite` (admin) con código; aceptar por código → crea `BandMembership`; caducidad/usos máximos. | e2e: aceptar enlace → entra como `member`/`guest`; código caducado/agotado → error. |
| **F7-7 · Perfil músico** | Crear/editar `MusicianProfile` (display_name, instruments, avatar_url); autorelleno en primer login. | e2e: nombres reales en la lista de miembros (no UUIDs). |
| **F7-8 · Frontend** | Pantalla **"Mis bandas"** (lista + crear), ficha de banda básica, **invitar por código** (generar + aceptar enlace), perfil básico. Ejecutar `cachebust.py`. | e2e Playwright del flujo completo; `test_cache_busting_al_dia` verde. |
| **F7-9 · Suite verde + aislamiento** | Cobertura e2e del flujo banda + **test de aislamiento por cada ruta** (regla de oro). | `run_checks.py` (lint+unit+e2e) verde. |
| **F7-10 · Registro y cierre** | `REGISTRO_DE_CAMBIOS.md` (qué/por qué/cómo/verificación); `[x]` en ROADMAP, mover a "Hechas". | Revisión final: doctor verde + registro al día. |

> **Nota:** `Song.band_id` y `Setlist.band_id` **no** entran en la Fase 7 (son de las Fases 8 y 9).
> La Fase 7 crea solo la **fundación de identidad**; el repertorio se "enchufa" después.

---

## C.6 — Diagrama de relaciones (completo)

```
                         MusicianProfile (id = user_id)
                                 │ (author / owner / assignee / member, por user_id)
                                 │
        BandInvite >──── Band ────< BandMembership   (role: admin|member|guest · status · left_at)
                          │  (currency, bio, social_links, fiscales, public_slug)
                          │
   ┌──────────────────────┼───────────────────────────────────────────────────────┐
   │                      │                                                         │
 Song (band_id, +meta)  Setlist (band_id) ──< SetlistItem (note) >── Song          Venue ──> Contact
   │  └─< Section → Line → ChordMarker/TabLine   (núcleo, sin cambios)               ▲
   │                                                                                 │ venue_id
 Event (type, status-pipeline, cronograma, logística, follow_up_at) ─────────────────┘
   │   ├──< EventAttendance >── (miembro)
   │   ├──< EventSong >── Song                 (orden del día del ensayo)
   │   ├──── setlist_id ─▶ Setlist             (solo concierto)
   │   ├──< EventResource >── BandResource     (riders/backline/stage plot/EPK, reutilizables)
   │   ├──< ChecklistItem (assignee_id)        ← ChecklistTemplate >── ChecklistTemplateItem
   │   └──< Message (event_id = hilo)          (chat general = event_id null)
   │
 Transaction (paid_by | paid_by_fund, event_id?) ──< TransactionSplit (user | to_fund)
   │                                                                    
 Settlement (from_user → to_user | to_fund)        Fondo = participante virtual (flags)
   │
 Message ──< Poll ──< PollOption ──< PollVote      Notification (por usuario)
   │
 Project ──< ProjectSong >── Song · Project ──< Task (assignee, status, →project/song/event)
   │
 InventoryItem · MerchProduct ──< MerchVariant · EmailTemplate
 FanSubscriber · FanMessage

 Attachment (band_id siempre; ≤1 de: event_id | song_id | transaction_id | project_id)
   → adjuntos puntuales por enlace/archivo de cualquier entidad o documento de banda
```

**Lectura rápida:** todo cuelga de `Band` y se filtra por `band_id` (multi-tenant). `Event` es el
hub de la operativa (agenda/booking/conciertos/ensayos). Las finanzas giran en torno a
`Transaction`+`Split`+`Settlement` con el **fondo** como participante. `Attachment`, `Task`,
`Notification`, `Contact` y `ChecklistTemplate` son **genéricos** → candidatos a molde.

---

> **Estado del documento:** 14 áreas resueltas **+ revisadas y pulidas** (incoherencias
> reconciliadas, convenciones transversales fijadas, Fase 7 detallada, diagrama completo). Próximo
> paso cuando lo apruebes: integrar en `harness/ROADMAP.md` (Fase 7 con sus T-NNN, y las 14–21) y
> **arrancar la Fase 7**. Hasta entonces, no se toca código (regla de la guía V2).
