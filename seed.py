#!/usr/bin/env python
"""
Seed script for populating example stats data.
Run with: docker compose exec web python seed.py
"""

import os
import sys
import django
import subprocess
import random
from datetime import datetime, timedelta
from pathlib import Path

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_estadisticas.settings')
django.setup()

from django.contrib.auth import get_user_model
from stats.models import Rating, Playback, AlbumSale

User = get_user_model()


def import_backup_if_exists():
    """Intenta importar desde backup.sql si existe."""
    backup_path = Path('/code/backup.sql')
    
    if not backup_path.exists():
        return False
    
    print(f"\n📂 Backup file found: {backup_path}")
    print("   Importing data from backup.sql...")
    print("   NOTE: Place backup.sql in project root, it won't be uploaded to GitHub")
    print("   Importing via Django ORM (this may take a moment)...\n")
    
    try:
        from django.db import connection
        
        # Leer el contenido del backup
        with open(backup_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Ejecutar el SQL directamente
        with connection.cursor() as cursor:
            # Dividir por líneas y filtrar comandos útiles
            statements = []
            current_statement = []
            
            for line in sql_content.split('\n'):
                # Ignorar comentarios y comandos especiales de mysqldump
                if line.startswith('--') or line.startswith('/*') or line.startswith('*/'):
                    continue
                if line.strip().startswith('/*!'):
                    continue
                    
                current_statement.append(line)
                
                # Si la línea termina en ;, es el final de un statement
                if line.strip().endswith(';'):
                    statement = '\n'.join(current_statement).strip()
                    if statement and not statement.startswith('LOCK') and not statement.startswith('UNLOCK'):
                        statements.append(statement)
                    current_statement = []
            
            # Ejecutar cada statement
            for statement in statements:
                try:
                    cursor.execute(statement)
                except Exception as e:
                    # Ignorar errores de tablas que ya existen, etc.
                    if 'already exists' not in str(e) and 'Duplicate' not in str(e):
                        pass  # Continuar silenciosamente
        
        print("   ✅ Backup imported successfully!")
        return True
            
    except Exception as e:
        print(f"   ⚠️  Import error: {e}")
        return False


def seed_data():
    """Populate example data for stats tables."""
    
    print("🌱 Starting seed script...")
    
    # Check existing data
    existing_ratings = Rating.objects.count()
    existing_playbacks = Playback.objects.count()
    existing_sales = AlbumSale.objects.count()
    
    print(f"\n📊 Current data in database:")
    print(f"  Ratings: {existing_ratings}")
    print(f"  Playbacks: {existing_playbacks}")
    print(f"  Album Sales: {existing_sales}")
    
    if existing_ratings > 0 or existing_playbacks > 0 or existing_sales > 0:
        print("\n⚠️  Database already contains data.")
        print("   Skipping seed to preserve existing data.")
        print("   To reset and seed fresh data, run:")
        print("   docker compose exec web python manage.py flush --no-input")
        print("   Then run seed.py again.\n")
        return
    
    print("\n✓ Database is empty, proceeding with seed...\n")
    
    # Try to import from backup.sql first
    if import_backup_if_exists():
        print("\n📈 Summary (from backup):")
        print(f"  Total ratings: {Rating.objects.count()}")
        print(f"  Total playbacks: {Playback.objects.count()}")
        print(f"  Total album sales: {AlbumSale.objects.count()}")
        print("\n✅ Seed complete (from backup)!")
        return
    
    print("\n💡 No backup.sql found, fetching data from contenidos service...")
    
    # Fetch data from contenidos API
    import requests
    from django.conf import settings
    
    contenidos_base = os.getenv('CONTENT_API_BASE', 'http://host.docker.internal:8001/api/v1')
    
    # Headers to avoid DisallowedHost error from Django contenidos service
    headers = {'Host': 'localhost:8001'}
    
    try:
        # Fetch artists
        print(f"  🔍 Fetching artists from {contenidos_base}/artists/")
        artists_response = requests.get(f'{contenidos_base}/artists/', headers=headers, timeout=5)
        artists_response.raise_for_status()
        artists_data = artists_response.json()
        # API returns a list directly, not a paginated response
        artists_list = artists_data if isinstance(artists_data, list) else artists_data.get('results', [])
        artists = [{'artist_id': str(a['id']), 'name': a.get('name', f'Artist {a["id"]}')} for a in artists_list]
        print(f"  ✓ Found {len(artists)} artists")
        
        # Fetch albums
        print(f"  🔍 Fetching albums from {contenidos_base}/albums/")
        albums_response = requests.get(f'{contenidos_base}/albums/', headers=headers, timeout=5)
        albums_response.raise_for_status()
        albums_data = albums_response.json()
        albums_list = albums_data if isinstance(albums_data, list) else albums_data.get('results', [])
        albums = [{'album_id': str(a['id']), 'artist_id': str(a.get('artist', {}).get('id', a.get('artist_id', '1')))} for a in albums_list]
        print(f"  ✓ Found {len(albums)} albums")
        
        # Fetch tracks (songs)
        print(f"  🔍 Fetching tracks from {contenidos_base}/tracks/")
        tracks_response = requests.get(f'{contenidos_base}/tracks/', headers=headers, timeout=5)
        tracks_response.raise_for_status()
        tracks_data = tracks_response.json()
        tracks_list = tracks_data if isinstance(tracks_data, list) else tracks_data.get('results', [])
        # Note: tracks use 'track_id' not 'id'
        songs = [{'song_id': str(t.get('track_id', t.get('id', '1'))), 'artist_id': str(t.get('artist', {}).get('id', t.get('artist_id', '1')))} for t in tracks_list]
        print(f"  ✓ Found {len(songs)} tracks")
        
    except Exception as e:
        print(f"  ⚠️  Error fetching from contenidos: {e}")
        print("  Using fallback minimal data...")
        artists = [{'artist_id': '1', 'name': 'Artist 1'}, {'artist_id': '2', 'name': 'Artist 2'}]
        albums = [{'album_id': '1', 'artist_id': '1'}, {'album_id': '2', 'artist_id': '2'}]
        songs = [{'song_id': '1', 'artist_id': '1'}, {'song_id': '2', 'artist_id': '1'}, {'song_id': '3', 'artist_id': '2'}]
    
    if not artists or not albums or not songs:
        print("  ⚠️  No data from contenidos, using minimal fallback...")
        artists = [{'artist_id': '1', 'name': 'Artist 1'}, {'artist_id': '2', 'name': 'Artist 2'}]
        albums = [{'album_id': '1', 'artist_id': '1'}, {'album_id': '2', 'artist_id': '2'}]
        songs = [{'song_id': '1', 'artist_id': '1'}, {'song_id': '2', 'artist_id': '1'}, {'song_id': '3', 'artist_id': '2'}]
    
    # Create or get demo users
    print("\n👤 Creating demo users...")
    users = []
    for i in range(1, 4):
        user, created = User.objects.get_or_create(
            username=f'demo_user_{i}',
            defaults={'is_active': False, 'email': f'demo{i}@example.com'}
        )
        users.append(user)
        status = "created" if created else "exists"
        print(f"  ✓ User '{user.username}' ({status})")
    
    # Use fixed base date to avoid duplicates on re-runs
    base_date = datetime(2025, 11, 19, 12, 0, 0)
    
    # Create ratings (aleatorias pero realistas)
    print("\n📊 Creating ratings...")
    rating_count = 0
    comments = [
        "Excelente canción!", "Me encanta", "Muy buena", "Increíble",
        "No está mal", "Podría mejorar", "Genial", "Obra maestra",
        "", "", "", ""  # Algunos sin comentario
    ]
    
    for user in users:
        # Cada usuario valora entre 8 y 15 canciones
        num_ratings = random.randint(8, 15)
        rated_songs = random.sample(songs, min(num_ratings, len(songs)))
        
        for song in rated_songs:
            # Distribución más realista: más 4 y 5 estrellas
            stars = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 35, 30])[0]
            rating = Rating.objects.create(
                user=user,
                song_id=song['song_id'],
                artist_id=song['artist_id'],
                stars=stars,
                comment=random.choice(comments),
            )
            # Fecha aleatoria en los últimos 30 días
            rating.rated_at = base_date - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
            rating.save(update_fields=['rated_at'])
            rating_count += 1
    
    print(f"  ✓ {rating_count} ratings created")
    
    # Create playbacks con duración aleatoria realista
    print("\n▶️  Creating playbacks...")
    playback_count = 0
    
    # Generar entre 50 y 80 reproducciones
    num_playbacks = random.randint(50, 80)
    for i in range(num_playbacks):
        song = random.choice(songs)
        # Duración aleatoria: entre 30 segundos y 5 minutos
        seconds = random.randint(30, 300)
        # 90% de reproducciones válidas
        valid = random.random() > 0.1
        
        playback = Playback.objects.create(
            song_id=song['song_id'],
            seconds=seconds,
            valid=valid
        )
        # Fecha aleatoria en los últimos 60 días
        playback.played_at = base_date - timedelta(days=random.randint(0, 60), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        playback.save(update_fields=['played_at'])
        playback_count += 1
    
    print(f"  ✓ {playback_count} playbacks created")
    
    # Create album sales con valores aleatorios realistas
    print("\n💿 Creating album sales...")
    sale_count = 0
    
    # Generar entre 30 y 50 ventas
    num_sales = random.randint(30, 50)
    for i in range(num_sales):
        album = random.choice(albums)
        # Unidades vendidas: entre 1 y 5 (más común 1-2)
        units = random.choices([1, 2, 3, 4, 5], weights=[50, 30, 10, 5, 5])[0]
        # Precio por álbum: entre 9.99 y 19.99
        price_per_unit = round(random.uniform(9.99, 19.99), 2)
        amount = round(units * price_per_unit, 2)
        
        sale = AlbumSale.objects.create(
            album_id=album['album_id'],
            units=units,
            amount=amount,
            currency=random.choice(['EUR', 'EUR', 'EUR', 'USD'])  # 75% EUR, 25% USD
        )
        # Fecha aleatoria en los últimos 90 días
        sale.purchased_at = base_date - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
        sale.save(update_fields=['purchased_at'])
        sale_count += 1
    
    print(f"  ✓ {sale_count} album sales created")
    
    # Summary
    print("\n📈 Summary:")
    print(f"  Total ratings: {Rating.objects.count()}")
    print(f"  Total playbacks: {Playback.objects.count()}")
    print(f"  Total album sales: {AlbumSale.objects.count()}")
    print("\n✅ Seed complete!")


if __name__ == '__main__':
    seed_data()
