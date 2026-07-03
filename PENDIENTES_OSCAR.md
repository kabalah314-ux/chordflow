# ✅ Pendientes de Oscar — acciones que solo puedes hacer tú

> Cosas que dependen de paneles/cuentas externas (Claude no tiene acceso). Marca con `[x]` al
> terminar. Última actualización: 2026-06-20.
> Leyenda: 🟢 puedes hacerlo YA (independiente) · 🟡 cuando lleguemos / decisión tuya.

---

## 🟢 Puedes ir haciendo ya

### 1. 🔴 Rotar secretos (seguridad — lo más urgente)
Se compartieron por chat la `sb_secret_` y la contraseña de Postgres **(la contraseña de la BD se
volvió a ver en el chat el 2026-06-16 y OTRA VEZ el 2026-07-03 al aplicar la migración de T-V5-06
→ cámbiala cuanto antes, es lo más urgente de esta lista)**.
- [ ] Supabase → proyecto `fwynfifvtthtpzpejfhb` → **Settings → API** → regenerar la **secret key**.
- [ ] Supabase → **Settings → Database** → **Reset database password** (2 min; no rompe la app: el
      runtime usa la env de Vercel). Tras cambiarla, actualizar `DATABASE_URL` en **Vercel** con la
      nueva contraseña (Settings → Environment Variables) y redeploy.
- [ ] Avísame con las nuevas (o actualízalas tú) en **Vercel** (`DATABASE_URL`, claves) y en
      `.env.local`. *(El `.env.local` lo actualizo yo si me pasas los valores.)*

### 2. ✅ Login con Google (T-046) — HECHO (2026-06-18)
- [x] **Google Cloud Console** → proyecto + **OAuth client ID** ("Web application") creado.
- [x] **Redirect URI** de Supabase (`https://fwynfifvtthtpzpejfhb.supabase.co/auth/v1/callback`)
      añadida en Google Cloud + orígenes JS (prod + `127.0.0.1:8000`).
- [x] *Client ID* + *Client Secret* + URLs de retorno aplicados en **Supabase** (vía Management API)
      y proveedor Google **activado**. Verificado: login real con `oscarcon314@gmail.com` ✅.
- [ ] 🔴 **REVOCAR el Personal Access Token `sbp_` de Supabase** usado para configurarlo (se vio en
      chat). [supabase.com/dashboard/account/tokens](https://supabase.com/dashboard/account/tokens).
      Ya cumplió su función; no afecta a nada borrarlo.

### 3. ✉️ Emails de auth con marca (T-047)
- [ ] Supabase → **Authentication → Email Templates** → personalizar confirmación / recuperación de
      contraseña con la marca **BandFlow**.

---

## 🟡 Cuando lleguemos / decisión tuya

### 4. ✅ Despliegue del giro (Fases 7–13) a producción — HECHO (2026-06-16)
- [x] **Push a `main`** (commit `29bd505`) → Vercel desplegó (deployment READY).
- [x] **6 migraciones del giro aplicadas** a Postgres prod vía pooler 5432
      (`3684ab6335e8` → … → `7022a3162284`, head).
- [x] Verificado en vivo: `/health` ok, `manifest` = BandFlow (código nuevo sirviendo).
- [ ] **Comprobación a ojo final (tú):** entra en https://chordflow-ecru.vercel.app, **inicia sesión**
      y prueba el flujo nuevo (crear banda → Inicio/Agenda/Finanzas/Chat → reproductor). Avísame si algo falla.

### 5. Más adelante (no urgente)
- [ ] **Almacenamiento (Fase 15):** activar **Supabase Storage** (buckets + políticas por banda)
      cuando lleguemos a fotos/recibos/adjuntos reales.

---

---

## 🟣 V3 (red musical) — desbloqueos pendientes (2026-06-17)

> Avancé en código toda la parte gratis de la V3 (ver `GUIA_MAESTRA_V3.md` y `REGISTRO_DE_CAMBIOS.md`).
> Lo siguiente necesita acción tuya.

### 6. ✅ Aplicar las 4 migraciones nuevas de la V3 a Postgres prod — HECHO (verificado 2026-06-20)
Ya están aplicadas en Postgres prod (head de Alembic `e9f1a2b3c4d5`, verificado vía MCP de Supabase):
- [x] `b3f1a9c2d4e5` — `Song.reference_url` (vídeo de referencia, T-090).
- [x] `c5d7e9f1a2b3` — tablas de **giras** (`tours`/`tour_stops`/`tour_budget_lines`, T-093).
- [x] `d7e9f1a2b3c4` — `Band.plan` (andamiaje Free/Pro, T-097).
- [x] `e9f1a2b3c4d5` — **biblioteca global** (`musical_works`/`public_scores`/`score_ratings`/`score_comments`, V3-F9).
      *(Aplicadas al desplegar el commit `c3a70d7 feat(v3)`; head de prod = head local. Confirmado por consulta de solo lectura a `alembic_version` + `information_schema`.)*

### 7. 🟡 Supabase Storage (desbloquea V3-F3 audio/fotos, grabadora, EPK, merch)
- [ ] Supabase → **Storage** → crear bucket(s) (p. ej. `band-media`).
- [ ] Políticas de acceso **por banda** (mismo principio multi-tenant: solo miembros acceden a sus
      archivos). Límites de tamaño/tipos. *Te paso el SQL/políticas cuando lo abordemos.*

### 8. 🟡 Supabase Realtime (desbloquea V3-F6 ensayo sincronizado + chat en vivo)
- [ ] Confirmar que **Realtime** está activo en el proyecto (suele venir activado).
- [ ] Decidir autorización de canales por `band_id` (te guío con el código cuando lleguemos).

### 9. 🟡 RLS de Postgres (prerequisito de abrir datos al público — V3-F7→F10)
- [ ] Decisión: activar **Row-Level Security** como 2ª barrera antes de la capa pública.
      ⚠️ Hay que revisar **cómo conecta el backend** (si usa `service_role`, RLS se ignora). Lo
      analizo y te propongo el plan cuando empecemos la biblioteca global / red.

### 10. 🟡 Stripe (monetización real — V3-F11, muy posterior)
- [ ] Cuenta Stripe + claves. Gratis hasta que cobres. Solo cuando haya features Pro que vender.

---

## ✅ Decisiones ya tomadas (no requieren acción)
- **Nombre del producto:** **BandFlow** (el rebranding se aplica en la **Fase 13**).
- **Divisa:** **EUR** (una por banda; finanzas en Fase 11).
- **V3 (D1–D8):** plano público híbrido, biblioteca acordes+letra recortada, red acotada, giras
  tempranas, ensayo sync v1 visual+metrónomo, Lucide, planes sin cobrar. Ver `GUIA_MAESTRA_V3.md`.
