# Runbook de producción (T-V6-70..72)

## Desplegar una rama con migraciones
1. CI verde en la rama (lint, unit, e2e y **Migraciones (Postgres)**).
2. Copia de seguridad (abajo) justo antes.
3. Aplicar migraciones contra el **pooler de sesión** (puerto 5432):
   `DATABASE_URL=postgresql://…:5432/postgres python -m alembic upgrade head`
4. Fusionar a `main` → Vercel despliega solo.
5. Smoke: `/health` 200, entrar, abrir una banda, la agenda y el reproductor.

## Copia de seguridad
- Manual: `python harness/backup_db.py` (usa `DATABASE_URL`; deja `backups/bandflow-AAAAMMDD-HHMM.dump`).
- Automática: workflow **Backup diario** (`.github/workflows/backup.yml`). Solo se ejecuta si existe el
  secreto `BACKUP_DATABASE_URL` en GitHub (Settings › Secrets › Actions). Guarda el volcado como
  artefacto 7 días.

## Restaurar
1. Crear una base vacía (o un proyecto Supabase de pruebas).
2. `pg_restore --no-owner --no-privileges -d "$DATABASE_URL_DESTINO" backups/bandflow-….dump`
3. `python -m alembic current` debe mostrar la última revisión.
4. Probar la restauración al menos una vez al trimestre (apuntar fecha aquí).

## Volver atrás (rollback)
- **Código:** en Vercel › Deployments › el anterior › *Promote to Production* (inmediato).
- **Esquema:** las migraciones V6 son aditivas (tablas/columnas nuevas): el código anterior funciona con
  ellas, así que normalmente NO hace falta `alembic downgrade`. Si hiciera falta:
  `python -m alembic downgrade <revisión>` (probado en CI con Postgres: `downgrade base` + `upgrade head`).
- **Datos:** restaurar la copia (arriba).

## Variables de entorno (Vercel)
`DATABASE_URL` (pooler de transacción 6543), `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `ALLOWED_ORIGINS`,
`OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `CRON_SECRET`. Nunca `CHORDFLOW_TEST_MODE`.

## Staging (cuando se quiera, coste 0)
Proyecto Supabase gratuito aparte + variables del entorno *Preview* de Vercel apuntando a él: cada push a
una rama da una URL de preview con su propia base de datos.
