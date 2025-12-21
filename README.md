# Backend Estadísticas - Proyecto GPS 25-26

Backend API REST para gestión y agregación de estadísticas de música (ratings, reproducciones, ventas de álbumes).

---

## 🚀 Arranque Rápido

### Requisitos previos

- **Docker Desktop** instalado y en ejecución
- Archivo `.env` configurado en la raíz del proyecto (ver configuración abajo)
- **(Opcional)** Servicio de Contenidos ejecutándose en `localhost:8001` para datos reales

### Pasos de instalación

**1. Crear archivo de configuración `.env`**

Crear un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```bash
SECRET_KEY=dev-secret-key-cambiala
DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.mysql
DB_NAME=estadisticas_db
DB_USER=root
DB_PASSWORD=12345
DB_HOST=db
DB_PORT=3306

# URL del servicio de Contenidos (ajustar según entorno)
# - Si Contenidos está en localhost: http://host.docker.internal:8001/api/v1
# - Si Contenidos está en Docker: http://contenidos-web:8001/api/v1
CONTENT_API_BASE=http://host.docker.internal:8001/api/v1
```

**2. Construir y levantar los contenedores**

```bash
docker compose up -d --build
```

**3. Esperar inicialización de MySQL**

Esperar 10-15 segundos para que MySQL esté completamente listo antes de continuar.

**4. Aplicar migraciones de base de datos**

```bash
docker compose exec web python manage.py migrate --noinput
```

> **Nota:** Si aparece el error "Can't connect to server on 'db'", significa que MySQL aún no está listo. Esperar unos segundos más y volver a ejecutar el comando.

**5. Poblar datos de ejemplo**

```bash
docker compose exec web python /code/seed.py
```

Este comando obtiene datos reales desde el servicio de Contenidos (artistas, álbumes, tracks) y genera estadísticas de ejemplo basadas en esos datos. Si el servicio de Contenidos no está disponible, se utilizarán datos de respaldo mínimos.

### Verificación

Acceder a las siguientes URLs para confirmar el funcionamiento:

- **API Estadísticas Globales**: http://localhost:8002/api/v1/stats/global/
- **Panel Admin Django**: http://localhost:8002/admin/

La API debería devolver un JSON con estadísticas agregadas (conteos de ratings, playbacks y ventas).

### Detener el proyecto

```bash
# Detener contenedores sin eliminar datos
docker compose down

# Detener y eliminar base de datos (reset completo)
docker compose down -v
```

---

## 📋 Comandos Útiles

### Arranques posteriores

```bash
# Levantar contenedores (después de haberlos detenido)
docker compose up -d

# Aplicar migraciones si hay cambios en modelos
docker compose exec web python manage.py migrate --noinput
```

### Gestión de datos

```bash
# Verificar cantidad de registros en base de datos (Windows PowerShell)
docker compose exec web python manage.py shell -c 'from stats.models import Rating, Playback, AlbumSale; print(Rating.objects.count(), Playback.objects.count(), AlbumSale.objects.count())'

# Repoblar datos de ejemplo (elimina datos previos)
docker compose exec web python manage.py flush --no-input
docker compose exec web python /code/seed.py

# Crear superusuario para acceso al admin
docker compose exec web python manage.py createsuperuser
```

### Monitoreo

```bash
# Ver logs del servidor web
docker compose logs -f web

# Ver logs de la base de datos
docker compose logs -f db

# Verificar estado de contenedores
docker compose ps
```

---

## 🎯 Descripción del Proyecto

Backend API para centralizar y exponer estadísticas de un servicio de música:
- **Ratings**: valoraciones de canciones de 1 a 5 estrellas por parte de usuarios
- **Playbacks**: registro de reproducciones con duración en segundos
- **Album Sales**: ventas de álbumes con unidades vendidas y montos

El sistema se integra con el servicio de Contenidos para obtener información de artistas, álbumes y canciones existentes.

### Stack Tecnológico

- **Django 5.0** + Django REST Framework 3.14+
- **MySQL 8.4** en contenedor Docker
- **Gunicorn 23.0** servidor WSGI de producción
- **Python 3.13**

---

## 📚 Modelos de Datos

### Rating (Valoraciones)
- `song_id`: identificador de la canción (CharField)
- `artist_id`: identificador del artista (CharField, opcional)
- `user`: usuario que realiza la valoración (ForeignKey)
- `stars`: puntuación 1-5 (PositiveSmallIntegerField)
- `comment`: comentario opcional (CharField, max 512 caracteres)
- `rated_at`: fecha y hora de la valoración (DateTimeField, auto)

### Playback (Reproducciones)
- `song_id`: identificador de la canción (CharField)
- `seconds`: segundos reproducidos (PositiveIntegerField)
- `valid`: indica si la reproducción es válida (BooleanField, default True)
- `played_at`: fecha y hora de reproducción (DateTimeField, auto)

### AlbumSale (Ventas de Álbumes)
- `album_id`: identificador del álbum (CharField)
- `units`: unidades vendidas (PositiveIntegerField, default 1)
- `amount`: monto total de la venta (DecimalField)
- `currency`: código de moneda (CharField, default "EUR")
- `purchased_at`: fecha y hora de compra (DateTimeField, auto)

---

## 🔌 Endpoints Principales

### Estadísticas Globales
```http
GET /api/v1/stats/global/
```
Retorna conteos agregados: total de ratings con promedio, total de reproducciones y total de ventas.

**Respuesta ejemplo:**
```json
{
  "ratings_count": 9,
  "ratings_average": 3.22,
  "plays_count": 67,
  "album_sales_count": 36
}
```

### Agregados por Artista
```http
GET /api/v1/stats/artists/aggregate/
```
Lista agregados de estadísticas agrupadas por artista.

### Agregados por Canción
```http
GET /api/v1/stats/songs/<song_id>/aggregate/
```
Estadísticas agregadas para una canción específica.

### Valoraciones de una Canción
```http
GET  /api/v1/stats/songs/<song_id>/ratings/
POST /api/v1/stats/songs/<song_id>/ratings/
```
Obtener o crear valoraciones para una canción.

### Reproducciones
```http
GET /api/v1/stats/songs/<song_id>/plays
```
Historial de reproducciones de una canción.

### Ventas de Álbum
```http
GET /api/v1/stats/albums/<album_id>/sales
```
Historial de ventas de un álbum específico.

---

## 🔧 Troubleshooting

### Puerto 3306 ocupado
**Síntoma:** Error al iniciar el contenedor MySQL indicando que el puerto ya está en uso.

**Solución:** Modificar en `docker-compose.yml` el mapeo de puertos de `3307:3306` a otro puerto libre (ej: `3308:3306`).

### "Connection refused" a MySQL
**Síntoma:** La aplicación no puede conectarse a la base de datos.

**Diagnóstico:**
```bash
docker compose ps
```
Verificar que el contenedor `db` esté en estado "healthy".

**Solución:** Si el contenedor no está healthy, reiniciar:
```bash
docker compose restart db
```

### Migraciones fallan
**Síntoma:** Errores al ejecutar `migrate` con mensajes de tablas duplicadas o columnas faltantes.

**Solución:** Reinicio completo del entorno:
```bash
docker compose down -v
docker compose up -d --build
# Esperar 10-15 segundos
docker compose exec web python manage.py migrate --noinput
```

### Error 1050: "Table 'django_session' already exists"
**Causa:** La tabla existe en la base de datos pero la migración inicial no está registrada en `django_migrations`.

**Soluciones disponibles:**

```bash
# Opción A: Marcar migraciones iniciales como aplicadas (conserva datos)
docker compose exec web python manage.py migrate --fake-initial

# Opción B: Marcar solo la migración de sessions como aplicada
docker compose exec web python manage.py migrate sessions 0001 --fake
docker compose exec web python manage.py migrate

# Opción C: Eliminar tabla de sesiones (no crítica, se recreará)
docker compose exec db mysql -uroot -p12345 -e "DROP TABLE IF EXISTS django_session" estadisticas_db
docker compose exec web python manage.py migrate

# Opción D: Reset completo (elimina todos los datos)
docker compose down -v
docker compose up -d --build
docker compose exec web python manage.py migrate
```

### Error 1091: "Can't DROP 'name'" (contenttypes 0002)
**Causa:** La migración intenta eliminar una columna `name` que ya no existe o el estado de migraciones no coincide.

**Diagnóstico:**
```bash
docker compose exec web python manage.py showmigrations contenttypes
```

**Soluciones:**
```bash
# Opción A: Marcar migración como aplicada (si el esquema es correcto)
docker compose exec web python manage.py migrate contenttypes 0002 --fake
docker compose exec web python manage.py migrate --noinput

# Opción B: Reset completo
docker compose down -v
docker compose up -d --build
docker compose exec web python manage.py migrate --noinput
```

### Datos vacíos en API
**Síntoma:** Los endpoints retornan arrays vacíos o contadores en 0.

**Solución:** Ejecutar el script de seed:
```bash
docker compose exec web python /code/seed.py
```

### Servicio de Contenidos no disponible
**Síntoma:** El seed muestra advertencia "Error fetching from contenidos" y usa datos de respaldo.

**Verificación:** Confirmar que el servicio de Contenidos está ejecutándose:
```bash
# Desde el host
curl http://localhost:8001/api/v1/artists/
```

**Configuración:** Si el servicio de Contenidos está en Docker, actualizar `.env`:
```bash
# Para Contenidos en Docker con nombre de servicio 'contenidos-web'
CONTENT_API_BASE=http://contenidos-web:8001/api/v1
```

**Nota:** El sistema funciona con datos de respaldo si Contenidos no está disponible, pero se recomienda tener el servicio activo para datos realistas.

---

## 🔗 Integración con Servicio de Contenidos

El script de seed (`seed.py`) se integra con el servicio de Contenidos para obtener datos reales de artistas, álbumes y canciones mediante peticiones HTTP a la API REST.

### Requisitos de integración

- Servicio de Contenidos accesible en la URL configurada en `CONTENT_API_BASE`
- Endpoints disponibles: `/artists/`, `/albums/`, `/tracks/`
- El sistema es **compatible con cualquier entorno** donde se ejecute Contenidos:
  - **Localhost directo:** `http://host.docker.internal:8001/api/v1`
  - **Docker mismo host:** `http://contenidos-web:8001/api/v1` (si comparten red)
  - **Otro servidor:** `http://IP_SERVIDOR:8001/api/v1`

### Flujo de datos

1. Al ejecutar `seed.py`, se realizan peticiones GET a los endpoints de Contenidos
2. Se extraen los IDs reales de artistas, álbumes y tracks
3. Se generan estadísticas aleatorias pero realistas basadas en esos IDs:
   - Ratings: 1-5 estrellas con comentarios opcionales
   - Playbacks: 30-300 segundos de reproducción
   - Sales: 1-5 unidades con precios 9.99-19.99€
4. Los datos se almacenan en la base de datos local de Estadísticas

### Fallback automático

Si el servicio de Contenidos no está disponible, `seed.py` utiliza automáticamente datos de respaldo mínimos (IDs 1, 2, 3) para permitir el desarrollo y testing sin dependencias externas.

---

## 📝 Contacto y Contribuciones

**Proyecto:** GPS 25-26  
**Equipo:** Estadísticas  

Para consultas o contribuciones, contactar con el equipo de desarrollo.
