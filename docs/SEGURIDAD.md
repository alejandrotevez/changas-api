# Seguridad — hallazgos y mejoras pendientes

Estado actual de seguridad del proyecto, ordenado por prioridad. Cada ítem indica
el archivo afectado y qué hacer.

## Crítico (arreglar antes de cualquier deploy)

### 1. Bug de autorización en cotizaciones (IDOR)
**Archivo:** `app/usecases/cotizaciones.py` (método `_transition`)

Al aceptar/rechazar una cotización se valida que el usuario sea participante del
`match_id` de la URL, pero **no se valida que la cotización pertenezca a ese match**
(`get_by_id(cotizacion_id)` no compara `cotizacion.match_id` con el `match_id` recibido).
Un cliente con un match propio puede aceptar/rechazar cotizaciones de matches ajenos
si conoce (o adivina) el ID.

**Fix:** después de obtener la cotización, agregar:
```python
if cotizacion.match_id != match_id:
    raise NotFound(entity="Cotizacion", id=cotizacion_id)
```

### 2. JWT_SECRET con valor default
**Archivo:** `app/config.py`

`JWT_SECRET` tiene un default hardcodeado (`"change-me-to-a-long-random-secret"`).
Si en prod no se define la variable, cualquiera que lea el repo puede firmar tokens
válidos de cualquier usuario.

**Fix:** eliminar el default y fallar al arrancar si falta (`JWT_SECRET: str` sin
valor, o un validator que rechace el valor default). Generar el secreto con
`secrets.token_urlsafe(64)`.

### 3. CORS abierto con credenciales
**Archivo:** `app/main.py`

`allow_origins=["*"]` junto con `allow_credentials=True` es inválido según la spec
CORS y peligroso: cualquier sitio puede llamar a la API.

**Fix:** lista blanca de orígenes desde settings (ej. `CORS_ORIGINS` en `.env`):
el dominio del frontend en prod, `http://localhost:8081`/Expo en dev.

## Alto

### 4. Sin rate limiting (fuerza bruta en login)
`POST /v1/auth/login/email` acepta intentos ilimitados. Agregar rate limiting
(ej. [slowapi](https://github.com/laurentS/slowapi)): 5–10 intentos/minuto por IP
en login, y un límite global razonable en el resto.

### 5. `rol_actual` sin validar
**Archivo:** `app/adapters/schemas/auth.py`

`UpdateUserRequest.rol_actual` es `Optional[str]`: se puede setear cualquier string
(`"ADMIN"`, basura, etc.) vía `PATCH /v1/users/me`. Como los permisos de cotizaciones
dependen del rol, esto corrompe la lógica de autorización.

**Fix:** `rol_actual: Optional[Literal["CLIENTE", "CHANGADOR"]] = None`.

### 6. Tokens sin revocación y con vida larga
- Expiración de 24 h y sin refresh tokens: un token robado sirve un día entero.
- No hay logout del lado del servidor.

**Fix sugerido:** access token corto (15–30 min) + refresh token con rotación,
y blacklist (Redis o tabla) por `jti` para revocar.

## Medio

### 7. Registro de usuarios inexistente
No hay `POST /v1/auth/register`; la única alta es vía Google. Cuando se agregue:
- Política de contraseñas (largo mínimo 8+, verificar contra listas de contraseñas filtradas).
- Verificación de email antes de activar la cuenta.
- Respuesta idéntica exista o no el email (evitar enumeración).

### 8. Enumeración de usuarios por timing en login
**Archivo:** `app/usecases/auth.py`

El mensaje de error ya es genérico (bien), pero si el email no existe no se ejecuta
`bcrypt.checkpw`, así que la respuesta es más rápida → se puede inferir si un email
está registrado midiendo tiempos.

**Fix:** hacer siempre un `checkpw` contra un hash dummy cuando el usuario no existe.

### 9. Security headers y HTTPS
Agregar middleware con `X-Content-Type-Options: nosniff`,
`Strict-Transport-Security`, `X-Frame-Options: DENY`, etc.
En prod, forzar HTTPS en el reverse proxy y `--proxy-headers` en uvicorn.

### 10. Errores que filtran detalle interno
**Archivo:** `app/usecases/auth.py` (`execute_google`)

`AuthenticationError(f"Invalid Google id token: {exc}")` devuelve al cliente el
detalle del error de la librería de Google. Loggear el detalle, responder genérico.

## Bajo / higiene

- **Dependencias:** correr `pip-audit` en CI y habilitar Dependabot/Renovate.
- **Deshabilitar `/docs` y `/openapi.json` en prod** (o protegerlos) si la API no es pública.
- **Logging estructurado sin datos sensibles:** nunca loggear passwords, tokens ni hashes.
- **Swipes/matches sin constraint único en DB:** la unicidad se chequea en código;
  agregar `UniqueConstraint(user_id, item_id)` en swipes y `UniqueConstraint(user_a_id, user_b_id)`
  en matches para cerrar la race condition a nivel base (ver `docs/MEJORAS.md`).
- **`.env`:** ya está en `.gitignore` (correcto). Usar un secret manager en prod
  (no variables en texto plano en el servidor).
