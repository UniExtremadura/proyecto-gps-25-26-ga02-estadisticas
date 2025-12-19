#!/usr/bin/env python
"""
Seed script for populating example stats data.
Run with: docker compose exec web python seed.py
"""

import os
import django
from datetime import datetime, timedelta

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_estadisticas.settings')
django.setup()

from django.contrib.auth import get_user_model
from stats.models import Rating, Playback, AlbumSale

User = get_user_model()


def seed_data():
    """Populate example data for stats tables."""
    
    print("🌱 Starting seed script...")
    
    # Create or get demo users
    users = []
    for i in range(1, 4):
        user, created = User.objects.get_or_create(
            username=f'demo_user_{i}',
            defaults={'is_active': False, 'email': f'demo{i}@example.com'}
        )
        users.append(user)
        status = "created" if created else "exists"
        print(f"  ✓ User '{user.username}' ({status})")
    
    # Create demo artists, albums, songs
    artists = [
        {'artist_id': 'artist_001', 'name': 'The Beatles'},
        {'artist_id': 'artist_002', 'name': 'Pink Floyd'},
        {'artist_id': 'artist_003', 'name': 'Queen'},
    ]
    
    albums = [
        {'album_id': 'album_001', 'artist_id': 'artist_001'},
        {'album_id': 'album_002', 'artist_id': 'artist_002'},
    ]
    
    songs = [
        {'song_id': 'song_001', 'artist_id': 'artist_001'},
        {'song_id': 'song_002', 'artist_id': 'artist_001'},
        {'song_id': 'song_003', 'artist_id': 'artist_002'},
        {'song_id': 'song_004', 'artist_id': 'artist_003'},
    ]
    
    # Create ratings
    print("\n📊 Creating ratings...")
    rating_count = 0
    for user in users:
        for song in songs:
            for stars in [3, 4, 5]:
                rating, created = Rating.objects.get_or_create(
                    user=user,
                    song_id=song['song_id'],
                    stars=stars,
                    defaults={
                        'artist_id': song['artist_id'],
                        'comment': f'Demo rating {stars}★ for {song["song_id"]}'
                    }
                )
                if created:
                    rating_count += 1
    print(f"  ✓ {rating_count} ratings created")
    
    # Create playbacks
    print("\n▶️  Creating playbacks...")
    playback_count = 0
    base_date = datetime.now() - timedelta(days=30)
    for i, song in enumerate(songs * 5):  # Repeat to have more playbacks
        playback, created = Playback.objects.get_or_create(
            song_id=song['song_id'],
            played_at=base_date + timedelta(hours=i),
            defaults={
                'seconds': (i % 5 + 1) * 60,  # 60-300 seconds
                'valid': True
            }
        )
        if created:
            playback_count += 1
    print(f"  ✓ {playback_count} playbacks created")
    
    # Create album sales
    print("\n💿 Creating album sales...")
    sale_count = 0
    for i, album in enumerate(albums * 3):  # Repeat to have more sales
        sale, created = AlbumSale.objects.get_or_create(
            album_id=album['album_id'],
            purchased_at=base_date + timedelta(days=i),
            defaults={
                'units': (i % 10 + 1),
                'amount': (i % 10 + 1) * 9.99,
                'currency': 'EUR'
            }
        )
        if created:
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
