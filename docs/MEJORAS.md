# Roadmap de mejoras — Changas API

Mejoras propuestas para que el proyecto escale, ordenadas por etapa. Los ítems de
seguridad están en `docs/SEGURIDAD.md` (leer primero: hay 3 críticos).

## Etapa 1 — Fundaciones (antes de sumar features)

### 1.1 Endpoint de registro
Hoy no existe `POST /v1/auth/register`: sin Google OAuth no se pueden crear usuarios
(este repo lo resuelve con `scripts/seed.py`, solo apto para dev). Es el faltante
funcional más grande.

### 1.2 Migraciones como única fuente de verdad del esquema
`init_db()` hace `create_all()` en cada arranque (`app/framework/database.py`) y a la
vez existe Alembic. En cuanto haya un cambio de esquema sobre datos reales, `create_all`
no alcanza (no altera tablas existentes) y los dos mecanismos van a divergir.
**Propuesta:** en prod solo `alembic upgrade head`; dejar `create_all` únicamente
para los tests.

### 1.3 PostgreSQL en prod
SQLite no soporta escrituras concurrentes reales. La URL async ya está parametrizada;
falta probar con `postgresql+asyncpg://`, configurar pool (`pool_size`, `max_overflow`)
y un docker-compose para levantar Postgres en dev.

### 1.4 Constraints de unicidad en DB
La unicidad de swipes y matches se valida solo en código (`SwipeUseCase`): dos requests
concurrentes pueden duplicar. Agregar en `app/framework/models.py`:
- `UniqueConstraint("user_id", "item_id")` en `swipes`
- `UniqueConstraint("user_a_id", "user_b_id")` en `matches`

y capturar `IntegrityError` en los repos como caso de duplicado.

## Etapa 2 — Producto

### 2.1 Fotos reales
`fotos` / `fotos_trabajos` son listas de strings sin backend de archivos. Falta:
upload a S3/Cloudinary/Supabase Storage con URLs firmadas, validación de tipo y
tamaño, y thumbnails.

### 2.2 Chat en tiempo real
El chat actual es polling de `GET /messages`. Migrar a WebSockets
(`fastapi.WebSocket`) o Server-Sent Events; con múltiples instancias hará falta
un pub/sub (Redis).

### 2.3 Notificaciones push
Nuevo match / mensaje / cotización → push vía Expo Notifications (el frontend ya
es Expo) o FCM. Requiere tabla de device tokens.

### 2.4 Feed con ranking
Hoy el feed es "todo menos lo swipeado", ordenado por fecha. Mejoras naturales:
- Matching por `tags` del usuario vs tags del post / especialidades del perfil.
- Filtro por zona (`barrio` hoy es texto libre; considerar geolocalización).
- Excluir items propios del feed.

### 2.5 Ciclo de vida del trabajo
La cotización aceptada es el final del flujo actual. Extender:
`ACEPTADA → EN_PROGRESO → COMPLETADA` + calificaciones/reviews entre partes
(clave para confianza en la plataforma).

### 2.6 Paginación por cursor
`page`/`limit` con offset se degrada con volumen y duplica/saltea items si el feed
cambia entre páginas. Migrar a cursor (`created_at` + `id`).

## Etapa 3 — Escala operativa

- **Observabilidad:** logging estructurado (JSON), Sentry para errores,
  métricas Prometheus/OpenTelemetry.
- **Cache:** Redis para el feed y sesiones/rate-limit.
- **Tests:** medir cobertura (`pytest-cov`) y sumar factories (factory-boy) para
  reducir el boilerplate de fixtures.
- **Búsqueda:** si crece el volumen de posts, full-text search (Postgres `tsvector`
  alcanza para empezar).
- **Background jobs:** para emails, notificaciones y limpieza (arq o Celery).

## Orden sugerido

1. Los 3 críticos de `docs/SEGURIDAD.md` (fix IDOR, JWT_SECRET, CORS) — poco esfuerzo, riesgo alto.
2. Registro + CI + Docker (1.1, 1.5, 1.6) — habilitan todo lo demás.
3. Postgres + migraciones + constraints (1.2, 1.3, 1.4) — antes de tener datos reales.
4. Etapa 2 según prioridad de producto.
