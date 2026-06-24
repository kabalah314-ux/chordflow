# GUÍA MAESTRA V4 — Experiencia de uso y diseño (BORRADOR V1: el QUÉ)

> **Propósito.** Recoger TODO lo que podemos mejorar en BandFlow en **coherencia, experiencia de
> uso, diseño visual y diseño de interacción**, mirando la app en la piel de un músico que se la
> descarga por primera vez.
>
> **Método.** Estudio visual de las 14 páginas (escritorio + móvil) con datos de demo sembrados
> (`harness/seed_demo.py`), recorriendo el flujo real: primer arranque → inicio → biblioteca →
> banda (9 pestañas) → reproductor (la joya).
>
> **Estado.** Esto es el **BORRADOR V1 = el QUÉ** (qué debería haber / qué falla). Luego lo
> repasamos juntos y hacemos la **V2 = el CÓMO** (cómo aplicar cada punto), iteramos hasta tener la
> guía completa, y **entonces** aplicamos y verificamos como siempre (doctor + tests + deploy).
>
> **Leyenda de prioridad:** 🔴 alto impacto · 🟠 medio · 🟢 nice-to-have · 🔌 necesita config/infra
> (Storage/Realtime/email). **Leyenda de tipo:** [F]uncionalidad · [V]isual · [I]nteracción.
>
> _Última actualización del borrador: 2026-06-24._

---

## 0. Veredicto general

Lo bueno (mantener): la base visual es **limpia y coherente** (tema oscuro, acento coral, tipografía
Inter/IBM Plex), el **shell con lateral** funciona muy bien, el sistema es **responsive** y la **joya**
(teleprompter) está enfocada. Las pestañas de banda están bien organizadas y **Finanzas** es ejemplar
de claridad.

Lo mejorable (el foco de esta guía): la app **funciona** pero todavía **no enamora**. Tres patrones se
repiten:
1. **Pantallas "de estantería":** mucho espacio vacío y poca información/acción a la vista (Inicio,
   Resumen de banda, Bandas, Perfil). Parecen formularios, no un panel de control vivo.
2. **Incoherencias de acabado:** iconos emoji mezclados con iconos SVG, una página fuera del shell,
   un término ("Repertorios") con dos significados.
3. **Poca "vida":** faltan microinteracciones, estados hover/foco ricos y feedback que hagan la app
   sentirse rápida y pulida.

Objetivo de la V4: que cada pantalla **tenga sentido al instante, sea bonita y dé gusto tocarla**.

---

## 1. Coherencia estructural y navegación

- **1.1** 🟠 [V] **`setlists.html` está fuera del shell.** Es la única página de navegación que NO usa
  el lateral (usa la top-bar antigua con iconos 🏠/📚 emoji). Debería entrar en el shell como el resto
  para no romper la sensación de "misma app". *(El editor y el reproductor sí deben seguir siendo
  pantallas enfocadas sin lateral.)*
- **1.2** 🟠 [V] **Terminología "Repertorios" vs "Colecciones".** El mismo concepto (agrupar canciones
  por tema, sin orden) se llama **"Repertorios"** en la banda y **"Colecciones"** en lo personal.
  Decidir un único término (propuesta: **"Colecciones"** en todo; dejar "Repertorio" solo para "todas
  las canciones de la banda"). *(Ya resuelto el peor choque: la antigua página personal "Repertorios"
  pasó a llamarse "Setlists", que es lo que era.)*
- **1.3** 🟠 [V] **Iconografía mixta.** El shell usa SVG (Lucide) pero el reproductor, los setlists y el
  perfil usan **emoji** (🏠 📚 🖨️ 🔧 🐈 💾 🗑️ 💬 📊). Unificar todo en el sistema SVG (`icons.js`),
  con tooltips. El emoji se ve "casero" al lado de lo demás.
- **1.4** 🟠 [I] **Pestañas de banda en móvil.** Son 9 y en móvil hay que **scrollear horizontalmente**;
  las últimas (Agenda, Finanzas, Chat, Giras, Ajustes) quedan ocultas sin pista de que hay más.
  Necesita indicador de scroll, fade en el borde, o repensar el patrón (menú/overflow).
- **1.5** 🟢 [F] **Acceso rápido a la banda activa.** Si normalmente tocas en una banda, llegar a ella
  son 2 saltos (Bandas → la banda). Considerar fijar la(s) banda(s) en el lateral o un acceso directo.

---

## 2. Paneles que deberían dar valor de un vistazo (hoy están casi vacíos)

- **2.1** 🔴 [V/F] **Inicio (dashboard).** Hoy es pasivo: saludo + "próximos eventos" + "últimos
  mensajes", con muchísimo espacio vacío en escritorio. Debería ser un **panel de control** del músico:
  - Próximo evento **destacado** (cuenta atrás, sala, tu asistencia, "¿vas?").
  - **Tu saldo** agregado (debes/te deben) con acceso a Finanzas.
  - **Accesos rápidos** (nueva canción, abrir último setlist, ir a mi banda).
  - Aprovechar el ancho (2 columnas en escritorio).
- **2.2** 🔴 [V/F] **Resumen de banda.** Es la pestaña por defecto al entrar en una banda y hoy solo
  muestra "Sobre la banda" + 2 chips. Debería resumir el estado de la banda: **próximo evento +
  quién confirma**, **último mensaje**, **saldos**, **nº de canciones/setlists**, accesos a cada
  sección. Es la "portada" de la banda y ahora mismo decepciona.
- **2.3** 🟠 [V/F] **Lista de "Mis bandas".** La tarjeta de banda solo dice nombre + rol + nº miembros,
  con mucho hueco. Enriquecer: **avatar/color** de la banda, **próximo evento**, nº de canciones, quizá
  tu saldo en ella. Que invite a entrar.
- **2.3b** 🟢 [V] **Estado vacío de "Mis bandas"** (cuando no tienes ninguna): hoy es un texto; darle un
  empty-state ilustrado con CTA "Crear banda" / "Tengo un código de invitación".
- **2.4** 🟢 [V/F] **Perfil.** Muy escueto (nombre + instrumentos). Añadir **avatar**, **mis bandas**,
  quizá enlaces (redes), e instrumentos como chips en vez de texto con comas. (Avatar real → 🔌 Storage.)

---

## 3. Tarjetas, listas y densidad

- **3.1** 🟠 [V/I] **Tarjetas de canción (Biblioteca).** Planas: título, artista, y 2-3 "pills"
  (Personal/BPM/sección). No hay **botón de reproducir visible** (se abre al hacer clic en toda la
  tarjeta, poco descubrible). Mejorar: **play en hover**, jerarquía visual más clara, acciones
  (editar/borrar/añadir a colección) coherentes, quizá una franja de color por fuente (personal/banda).
- **3.2** 🟠 [I] **Filas de Agenda muy cargadas.** Cada evento amontona en una línea: asistencia
  (Voy/Quizás/No voy) + estado de booking (desplegable) + 💬 + 🗑️ + la línea de confirmados. Se ve
  apretado. Agrupar acciones secundarias (p. ej. estado/borrar en un menú "⋯") y dejar lo principal
  (¿vas? + cuándo + dónde) limpio.
- **3.3** 🟢 [V] **"Quitar de X" con ✕ rojo** aparece en repertorio, setlists, etc. Coherente, pero el
  rojo llama mucho para una acción no destructiva (quitar ≠ borrar). Revisar peso visual.
- **3.4** 🟢 [V] **Identidad de banda.** El avatar autogenerado (iniciales sobre color) está bien;
  usar **ese mismo color** de forma consistente (banner, tarjeta en "Mis bandas", chat, etiquetas en
  Inicio/Agenda) para que cada banda sea reconocible de un vistazo. (Logo subido → 🔌 Storage.)

---

## 4. Diseño de interacción y "vida" (lo que hace que dé gusto usarla)

- **4.1** 🔴 [I] **Estados hover/active/focus ricos** en tarjetas, filas y pestañas (elevación sutil,
  borde acento, cursor). Hoy se sienten estáticas. Revisar que TODO lo clicable lo parezca.
- **4.2** 🟠 [I] **Transiciones suaves**: cambio de pestaña en la banda, abrir/cerrar modales,
  aparición de tarjetas. Animaciones cortas (150–200 ms) que den sensación de fluidez.
- **4.3** 🟠 [I] **Microinteracciones de feedback**: al añadir/quitar/guardar (no solo el toast; también
  un pequeño efecto en el elemento). Al marcar "Voy", animar el cambio.
- **4.4** 🟠 [I] **Skeletons de carga en todas las vistas.** Inicio ya los tiene; faltan en otras
  (p. ej. Giras muestra "Cargando…" en texto plano; Biblioteca/Agenda/Finanzas igual). Unificar.
- **4.5** 🟢 [I] **Drag & drop para reordenar** las canciones de un setlist (hoy se añaden en el orden
  de clic y no se pueden reordenar sin rehacer). Muy esperable en un setlist.
- **4.6** 🟢 [I] **Atajos de teclado** visibles/documentados (ya hay espacio=play; pedalera). Un pequeño
  "?" con la lista de atajos.

---

## 5. La joya — el reproductor en directo

- **5.1** 🔴 [V] **Iconos del reproductor.** La top-bar y la bottom-bar usan emoji crípticos: 🔧
  (¿diagramas?), 🐈 (¡un gato! probablemente el afinador/metrónomo), 🏠, 📚, 🖨️, ➕. Pasar a SVG
  claros + tooltips. El gato hay que cazarlo 🙂.
- **5.2** 🟠 [V] **Top-bar abarrotada.** BPM, tono (♭/♯/guardar), y 5 iconos sueltos. Agrupar por
  función (transporte / herramientas / navegación) y dar aire.
- **5.3** 🟠 [V/I] **Más espectacular en directo.** Ya hay glow del acorde activo y modo escenario
  (V3-F1/F4). Subir el listón: tamaño/contraste de acordes en escenario, animación de la "bolita" de
  posición, transición suave entre líneas, modo alto contraste para escenario con poca luz.
- **5.4** 🟢 [F] **Controles de directo** (diferidos a V3-F6): loop A-B, metrónomo audible, autoscroll
  más fino. Anotados aquí para no perderlos.

---

## 6. Onboarding y primera impresión

- **6.1** ✅ [F] **Inicio sin bandas → "Primeros pasos"** (hecho 2026-06-24). Mantener y, si acaso,
  enriquecer con una pista visual.
- **6.2** 🟠 [V] **Pantalla de login.** Es lo PRIMERO que ve un usuario real y no la hemos repasado en
  este estudio (en modo test se salta). Revisar branding, propuesta de valor ("gestiona tu banda:
  repertorio, bolos y cuentas") y el botón de Google.
- **6.3** 🟢 [F] **Tour/tooltips la primera vez** en el espacio de banda (qué es cada pestaña).
- **6.4** 🟢 [V] **Biblioteca vacía** ya tiene buen empty-state; revisar que TODOS los vacíos tengan
  CTA (no solo texto).

---

## 7. Sistema de diseño y acabado fino

- **7.1** 🟠 [V] **Uso del ancho.** Muchas páginas tienen el contenido en una columna estrecha con
  enormes márgenes vacíos en escritorio (Inicio, Bandas, Perfil, Explorar). Decidir: ¿ensanchar el
  contenedor, usar rejillas de 2-3 columnas, o centrar con un ancho máximo más generoso?
- **7.2** 🟢 [V] **Dos tonos de naranja.** Algunos botones (p. ej. "Buscar" de Explorar) se ven de un
  naranja más brillante que el acento coral del resto. Unificar el acento.
- **7.3** 🟢 [V] **Jerarquía tipográfica.** Revisar tamaños/pesos de h1/h2/subtítulos/badges para una
  escala más clara y consistente entre páginas.
- **7.4** 🟢 [V] **Modo claro.** Existe el toggle; verificar que el modo claro está igual de pulido que
  el oscuro (no lo hemos auditado a fondo aquí).
- **7.5** 🟢 [♿] **Accesibilidad** (auditoría aparte): contraste de texto secundario (los grises muy
  tenues sobre negro rozan el mínimo), foco visible en todo, tamaño de objetivos táctiles en móvil.

---

## 8. Ideas de funcionalidad detectadas (para no perderlas)

> No son fallos; son oportunidades vistas durante el estudio. Se priorizan al hacer la V2.

- **8.1** 🟢 [F] "Añadir a setlist / colección" **desde la tarjeta de una canción** (hoy hay que ir al
  editor de la colección/setlist).
- **8.2** 🟢 [F] **Buscador** dentro del repertorio de banda y de los setlists (hoy solo en Biblioteca).
- **8.3** 🟢 [F] **Reordenar** dentro de una colección/setlist (drag & drop, ver 4.5).
- **8.4** 🔌 [F] **Avatar/logo de banda y de perfil** (necesita Storage).
- **8.5** 🔌 [F] **Notificaciones/recordatorios reales** (email/push) de eventos y mensajes.
- **8.6** 🔌 [F] **Página pública / EPK** de la banda (V3-F8) y **ensayo en tiempo real** (V3-F6).
- **8.7** 🟢 [F] **Resumen de caché por temporada** (hoy hay por gira).
- **8.8** 🟢 [F] **Duplicar** una canción/setlist/colección como punto de partida.

---

## 9. Cómo seguimos (proceso acordado)

1. **(Esta guía = V1, el QUÉ.)** Oscar la repasa y marca prioridades / añade lo que falte.
2. **V2 (el CÓMO):** por cada punto, definir la solución concreta (diseño + implementación).
3. Iterar V2→V3… hasta tener la guía completa y cerrada.
4. **Aplicar por fases** (V4-F1, V4-F2…) con el bucle de siempre: tarea en `TASKS.md` → implementar →
   `doctor` verde → test que lo cubre → `cachebust` → registrar → desplegar → verificar en vivo.

> Sugerencia de primer bloque a aplicar (cuando cerremos el CÓMO), por relación impacto/esfuerzo y sin
> necesitar config externa: **1.3 iconos SVG**, **1.1 setlists al shell**, **2.2 Resumen de banda
> útil**, **2.1 Inicio panel de control**, **4.1/4.2 hover+transiciones**, **5.1 iconos del reproductor**.
