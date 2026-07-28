# Changas API

Backend de [Changas App](https://github.com/gonzalotev/changas-app) — plataforma para conectar clientes con changadores (gasistas, plomeros, electricistas, etc.).

## Stack

- **Python 3.14+** / **FastAPI**
- **SQLAlchemy 2.0** (async) + **aiosqlite** (dev) / PostgreSQL (prod)
- **Alembic** para migraciones
- **JWT** (PyJWT) + **bcrypt** para autenticación
- **Google OAuth** opcional
- **Pytest** + **httpx** para tests (29 de integración + 37 unitarios)

## Arquitectura

Clean Architecture:

```
app/
├── domain/         # Entidades (dataclasses) + interfaces (Protocol)
├── usecases/       # Lógica de negocio
├── adapters/
│   ├── routers/    # Endpoints FastAPI
│   ├── schemas/    # Pydantic request/response
│   ├── repositories/  # Implementaciones SQLAlchemy
│   └── middleware/ # Auth (JWT)
└── framework/      # SQLAlchemy models, DB engine, FastAPI app
```

## Requisitos

- Python 3.13+
- `pip` (o `uv`)

## Levantar en local

```bash
# 1. Clonar
git clone https://github.com/alejandrotevez/changas-api.git
cd changas-api

# 2. Entorno virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. (Opcional) Aplicar migraciones
alembic upgrade head

# 5. Iniciar servidor
python -m uvicorn app.main:app --reload --port 8000
```

El servidor queda en `http://localhost:8000`. Los endpoints están bajo `/v1/`.

### Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/v1/auth/login/email` | Login con email y contraseña |
| POST | `/v1/auth/login/google` | Login con Google |
| PATCH | `/v1/users/me` | Actualizar perfil |
| GET | `/v1/feed` | Obtener feed (según rol) |
| POST | `/v1/feed/swipe` | Swipe (like/dislike) |
| GET | `/v1/matches` | Listar matches |
| GET | `/v1/matches/{id}/messages` | Mensajes de un match |
| POST | `/v1/matches/{id}/messages` | Enviar mensaje |
| GET | `/v1/health` | Health check |
| POST | `/v1/matches/{id}/cotizaciones` | Crear cotización (changador) |
| PATCH | `/v1/matches/{id}/cotizaciones/{id}/accept` | Aceptar cotización (cliente) |
| PATCH | `/v1/matches/{id}/cotizaciones/{id}/reject` | Rechazar cotización (cliente) |

### Tests

```bash
# Todos los tests
pytest -v

# Solo unitarios
pytest tests/unit/ -v

# Solo integración
pytest tests/integration/ -v
```

### Migraciones

```bash
# Crear nueva migración
alembic revision --autogenerate -m "descripcion"

# Aplicar
alembic upgrade head

# Revertir
alembic downgrade -1
```

## Configuración

Crear un archivo `.env` en la raíz:

```env
DATABASE_URL=sqlite+aiosqlite:///./changas.db
JWT_SECRET=tu-secreto-muy-largo-y-seguro
GOOGLE_CLIENT_ID=tu-client-id-de-google
```

## Frontend

El frontend está en [github.com/gonzalotev/changas-app](https://github.com/gonzalotev/changas-app).

Para correr frontend + backend juntos en local:

```bash
# Terminal 1 — Backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd ../changas-app
set EXPO_PUBLIC_API_URL=http://localhost:8000
npx expo start
```
