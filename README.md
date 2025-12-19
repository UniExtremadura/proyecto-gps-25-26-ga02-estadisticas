# Backend Estadísticas - Proyecto GPS 25-26

Backend API REST para gestión y agregación de estadísticas de música (ratings, reproducciones, ventas de álbumes).

## Arranque del Docker

### Requisitos previos

- **Docker Desktop** instalado con virtualización habilitada en BIOS/UEFI.
- **Python 3.13+** (opcional, solo si quieres ejecutar comandos locales sin Docker).
- **MySQL 8+** (opcional, incluido en el docker-compose).

### Pasos de arranque

#### 1. Crear archivo `.env`

En la raíz del proyecto, crea un archivo `.env` con las variables de entorno:

```bash
SECRET_KEY=dev-secret-key-cambiala
DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos (debe coincidir con docker-compose.yml)
DB_ENGINE=django.db.backends.mysql
DB_NAME=estadisticas_db
DB_USER=root
DB_PASSWORD=12345
DB_HOST=db
DB_PORT=3306

# API de contenidos (para resolver canciones → artistas)
CONTENT_API_BASE=http://host.docker.internal:8001/api/v1
```

#### 2. Levantar contenedores

```bash
# Primera vez: construir y arrancar en background
docker-compose up -d --build

# Aplicar migraciones
docker-compose exec web python manage.py migrate

# Poblar datos de ejemplo
docker-compose exec web python /code/seed.py
```

**Comandos posteriores** (cuando ya está construido):

```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python /code/seed.py
```

**(Opcional)** Crear superusuario para acceder al admin:

```bash
docker-compose exec web python manage.py createsuperuser
```

#### 3. Verificar servicio

- **API**: http://localhost:8002/api/v1/stats/
- **Admin**: http://localhost:8002/admin/ (si creaste superusuario)
- **DB**: accesible en `localhost:3307` (host) → `3306` (contenedor)

#### 4. Restaurar datos desde MySQL local

Si tienes datos en tu MySQL local:

```bash
# Sacar dump desde tu MySQL local (Windows)
mysqldump -uroot -p --result-file="C:\Users\Jorge\backup.sql" estadisticas_db

# Copiar dump al contenedor
docker compose cp "C:\Users\Jorge\backup.sql" db:/tmp/backup.sql

# Importar en la BD del contenedor
docker compose exec db sh -c "mysql -uroot -p12345 estadisticas_db < /tmp/backup.sql"

# Verificar conteos
docker compose exec web python manage.py shell -c "from stats.models import Rating, Playback, AlbumSale; print(f'Ratings: {Rating.objects.count()}, Playbacks: {Playback.objects.count()}, Sales: {AlbumSale.objects.count()}')"
```

#### 5. Detener servicios

```bash
docker compose down          # Detiene sin borrar datos
docker compose down -v       # Detiene y borra volumen de BD (CUIDADO)
```

---

## Cómo funciona el Backend

### Arquitectura general

- **Framework**: Django 5.0 + Django REST Framework (DRF)
- **Base de datos**: MySQL 8.4
- **Servidor**: Gunicorn en puerto `8002`
- **Contenedor**: Python 3.13-slim + libmysqlclient (WORKDIR `/code`)

### Modelos de datos

El backend gestiona tres modelos principales en `stats/models.py`:

#### 1. **Rating** (Valoraciones)
```python
- song_id: str (identificador único de la canción)
- artist_id: str (opcional, artista de la canción)
- user: ForeignKey (usuario que valora)
- stars: int (1-5, puntuación)
- comment: str (comentario opcional)
- rated_at: datetime (timestamp automático)
```

#### 2. **Playback** (Reproducciones)
```python
- song_id: str (identificador de la canción)
- seconds: int (segundos reproducidos)
- valid: bool (reproducción válida o no)
- played_at: datetime (timestamp automático)
```

#### 3. **AlbumSale** (Ventas de álbumes)
```python
- album_id: str (identificador del álbum)
- units: int (número de unidades vendidas)
- amount: decimal (monto en moneda)
- currency: str (código de moneda, e.g., EUR)
- purchased_at: datetime (timestamp automático)
```

### Endpoints principales

#### Estadísticas globales
```
GET /api/v1/stats/global/

Respuesta:
{
  "ratings_count": 19,
  "ratings_average": 4.2105,
  "plays_count": 43,
  "album_sales_count": 102
}
```

#### Agregados de artistas
```
GET /api/v1/stats/artists/
GET /api/v1/stats/artists/aggregate/

Respuesta:
{
  "total": 3,
  "items": [
    {
      "artist_id": "artist_001",
      "name": "The Beatles",
      "ratings_count": 9,
      "ratings_average": 4.33
    },
    ...
  ]
}

Parámetros opcionales:
- limit: int (número máximo de resultados)
- offset: int (desplazamiento para paginación)
- sort: "count" | "average" (ordenamiento)
- from: ISO datetime (filtro de fecha inicio)
- to: ISO datetime (filtro de fecha fin)
```

#### Agregados por canción
```
GET /api/v1/stats/songs/<song_id>/aggregate/

Respuesta:
{
  "song_id": "song_001",
  "ratings_count": 3,
  "ratings_average": 4.67,
  "plays_count": 8
}
```

#### Reproducciones por canción
```
GET /api/v1/stats/songs/<song_id>/plays

Respuesta:
{
  "song_id": "song_001",
  "total_plays": 8,
  "total_seconds": 1440
}
```

#### Ventas de álbum
```
GET /api/v1/stats/albums/<album_id>/sales

Respuesta:
{
  "album_id": "album_001",
  "total_units": 5,
  "total_amount": 49.95,
  "currency": "EUR"
}
```

#### Valoraciones de una canción
```
GET /api/v1/stats/songs/<song_id>/ratings/

Respuesta (lista):
[
  {
    "id": 1,
    "song_id": "song_001",
    "stars": 5,
    "comment": "Great!",
    "user": "demo_user_1",
    "rated_at": "2025-12-19T08:50:00Z"
  },
  ...
]
```

#### Crear valoración
```
POST /api/v1/stats/songs/<song_id>/ratings/

Body:
{
  "stars": 4,
  "comment": "Very good"
}

Respuesta:
{
  "id": 2,
  "song_id": "song_001",
  "stars": 4,
  "comment": "Very good",
  "user": "anonymous",
  "rated_at": "2025-12-19T09:00:00Z"
}
```

---

## En qué consiste el Backend

### Propósito

Backend API para centralizar y exponer estadísticas de un servicio de música:
- **Ratings**: permite a usuarios valorar canciones de 1 a 5 estrellas.
- **Playbacks**: registra reproducciones con duración y validez.
- **Sales**: registra ventas de álbumes con cantidades y montos.
- **Agregación**: calcula automáticamente conteos y promedios por artista, canción y globales.

### Características clave

1. **Agregación por BD**: usa ORM de Django + SQL para computar sumas y promedios sin traer todos los datos al app.
2. **Resolución de artistas**: si una valoración tiene `artist_id` vacío, intenta resolver vía API externa (`CONTENT_API_BASE`).
3. **CORS habilitado**: permite peticiones desde frontend en `http://localhost:5173`.
4. **Autenticación**: soporta JWT, sesiones Django y acceso anónimo.
5. **Admin de Django**: interfaz web para gestionar datos directamente.
6. **Seed script**: `seed.py` para poblar datos de prueba rápidamente.

### Stack tecnológico

| Componente | Versión | Propósito |
|------------|---------|----------|
| Django | 5.0.3 | Framework web |
| Django REST Framework | 3.14+ | API REST |
| MySQL | 8.4 | Base de datos |
| Gunicorn | 23.0.0 | Servidor WSGI |
| Python | 3.13 | Lenguaje |
| mysqlclient | 2.2+ | Driver MySQL |

### Flujo típico

1. **Frontend** (5173) envía request a **Backend** (8002/api/v1/stats/...).
2. **Backend** consulta **MySQL** (3306 interno) usando ORM de Django.
3. Si faltan datos (e.g., `artist_id`), consulta **API de Contenidos** (8001) para enriquecer.
4. Retorna JSON con datos agregados.
5. **Frontend** renderiza gráficos/tablas.

### Archivos principales

- `Dockerfile`: define imagen Python + dependencias + puerto 8002.
- `docker-compose.yml`: orquesta DB (MySQL) + Web (Django).
- `manage.py`: CLI de Django (migraciones, shell, etc.).
- `backend_estadisticas/settings.py`: configuración de Django (BD, CORS, etc.).
- `backend_estadisticas/urls.py`: rutas principales.
- `stats/models.py`: definición de Rating, Playback, AlbumSale.
- `stats/views.py`: lógica de endpoints (agregación, filtrado).
- `stats/serializers.py`: convertidores modelo → JSON.
- `stats/urls.py`: rutas de API.
- `seed.py`: script para poblar datos de ejemplo.
- `.env`: variables de entorno (contraseñas, URLs, etc.).

---

## Desarrollo

### Actualizar dependencias

```bash
# Editar requirements.txt, luego:
docker compose up --build
```

### Crear migraciones

```bash
# Tras cambiar models.py:
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

### Acceder a Django Shell

```bash
docker compose exec web python manage.py shell
```

Dentro:
```python
from stats.models import Rating
Rating.objects.all()
```

### Ver logs

```bash
# Logs en vivo
docker compose logs -f web

# Logs de BD
docker compose logs -f db
```

---

## Próximas integraciones

1. **Frontend (Vite, React)**: en puerto 5173.
2. **Backend de Contenidos**: en puerto 8001 (servicio que expone `/api/v1/tracks/...`).
3. **Autenticación**: integrar JWT o sesiones con el frontend.

---

## Troubleshooting

### Puerto 3306 ocupado
→ Cambia en `docker-compose.yml` el mapeo de `3307:3306` a otro puerto libre (e.g., `3308:3306`).

### "Connection refused" a MySQL
→ Asegúrate de que el contenedor `db` está healthy: `docker compose ps`.

### Migraciones fallan
→ Reinicia limpio: `docker compose down -v && docker compose up --build`.

### Datos vacíos en API
→ Ejecuta `docker compose exec web python seed.py` o importa un dump: ver sección "Restaurar datos".

---

## Contacto y contribuciones

Proyecto GPS 25-26 | Equipo de Estadísticas
