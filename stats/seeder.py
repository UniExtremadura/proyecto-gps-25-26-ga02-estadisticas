"""
Dynamic seeder for stats based on contenidos data.

Reads artists, albums, and tracks from CONTENT_API_BASE and creates
realistic example ratings, playbacks, and sales data automatically.
Runs on post_migrate and can be called manually.
"""
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from .models import Rating, Playback, AlbumSale


def fetch_content_data():
    """Fetch artists, albums, and tracks from contenidos API."""
    content_api = getattr(settings, "CONTENT_API_BASE", "http://127.0.0.1:8001/api/v1")
    
    data = {
        "artists": [],
        "albums": [],
        "tracks": [],
    }
    
    # Fetch artists
    try:
        r = requests.get(f"{content_api}/artists?limit=100", timeout=5)
        if r.ok:
            resp = r.json()
            if isinstance(resp, dict):
                data["artists"] = resp.get("items") or resp.get("artists") or []
            elif isinstance(resp, list):
                data["artists"] = resp
        print(f"  ✓ Fetched {len(data['artists'])} artists from contenidos")
    except Exception as e:
        print(f"  ⚠️  Could not fetch artists: {e}")
    
    # Fetch albums
    try:
        r = requests.get(f"{content_api}/albums?limit=100", timeout=5)
        if r.ok:
            resp = r.json()
            if isinstance(resp, dict):
                data["albums"] = resp.get("items") or resp.get("albums") or []
            elif isinstance(resp, list):
                data["albums"] = resp
        print(f"  ✓ Fetched {len(data['albums'])} albums from contenidos")
    except Exception as e:
        print(f"  ⚠️  Could not fetch albums: {e}")
    
    # Fetch tracks
    try:
        r = requests.get(f"{content_api}/tracks?limit=100", timeout=5)
        if r.ok:
            resp = r.json()
            if isinstance(resp, dict):
                data["tracks"] = resp.get("items") or resp.get("tracks") or []
            elif isinstance(resp, list):
                data["tracks"] = resp
        print(f"  ✓ Fetched {len(data['tracks'])} tracks from contenidos")
    except Exception as e:
        print(f"  ⚠️  Could not fetch tracks: {e}")
    
    return data


def extract_id(obj, *keys):
    """Extract ID from object, trying multiple possible key names."""
    if not obj:
        return None
    for key in keys:
        val = obj.get(key)
        if val:
            return str(val)
    return None


def seed_from_contenidos():
    """
    Fetch contenidos data and create realistic stats.
    Only runs if tables are empty.
    """
    if Rating.objects.exists() or Playback.objects.exists() or AlbumSale.objects.exists():
        print("[SEEDER] Database already has stats data. Skipping auto-seed.")
        return False
    
    print("\n[SEEDER] Fetching data from contenidos API...")
    content_data = fetch_content_data()
    
    artists = content_data.get("artists", [])
    albums = content_data.get("albums", [])
    tracks = content_data.get("tracks", [])
    
    if not artists and not tracks:
        print("[SEEDER] ⚠️  No artists or tracks found. Cannot seed from contenidos.")
        return False
    
    print(f"[SEEDER] ✓ Using data: {len(artists)} artists, {len(albums)} albums, {len(tracks)} tracks")
    
    # Ensure we have demo users
    demo_users = []
    for i in range(1, 4):
        user, _ = User.objects.get_or_create(
            username=f"demo_user_{i}",
            defaults={"email": f"demo{i}@example.com", "is_active": True}
        )
        demo_users.append(user)
    
    base_date = datetime(2025, 11, 27, 12, 0, 0)
    
    # Create ratings from tracks
    print("[SEEDER] Creating ratings from tracks...")
    rating_count = 0
    for idx, track in enumerate(tracks[:30]):  # Limit to 30 tracks
        track_id = extract_id(track, "id", "track_id", "song_id", "uuid")
        artist_id = extract_id(track, "artist_id", "artist")
        
        if not track_id:
            continue
        
        # Get artist_id from artist object if present
        if isinstance(track.get("artist"), dict):
            artist_id = extract_id(track["artist"], "id", "artist_id", "uuid") or artist_id
        
        # Create 2-3 ratings per track from different users
        for user_idx in range(2):
            if user_idx >= len(demo_users):
                break
            
            stars = 3 + (idx + user_idx) % 3  # 3, 4, or 5
            rating, created = Rating.objects.get_or_create(
                user=demo_users[user_idx],
                song_id=track_id,
                stars=stars,
                defaults={
                    "artist_id": artist_id or "",
                    "comment": f"Auto-generated rating from {track.get('name', 'Track')}",
                }
            )
            if created:
                rating.rated_at = base_date + timedelta(hours=idx * 2 + user_idx)
                rating.save(update_fields=["rated_at"])
                rating_count += 1
    
    print(f"  ✓ Created {rating_count} ratings")
    
    # Create playbacks from tracks
    print("[SEEDER] Creating playbacks from tracks...")
    playback_count = 0
    for idx, track in enumerate(tracks[:30]):
        track_id = extract_id(track, "id", "track_id", "song_id", "uuid")
        if not track_id:
            continue
        
        # Create 3-5 playbacks per track at different times
        for play_idx in range(2 + (idx % 3)):
            playback = Playback.objects.create(
                song_id=track_id,
                seconds=0,
                valid=True,
            )
            playback.played_at = base_date + timedelta(
                hours=idx * 3 + play_idx,
                minutes=(idx * 5 + play_idx * 7) % 60
            )
            playback.save(update_fields=["played_at"])
            playback_count += 1
    
    print(f"  ✓ Created {playback_count} playbacks")
    
    # Create album sales
    print("[SEEDER] Creating album sales from albums...")
    sale_count = 0
    for idx, album in enumerate(albums[:20]):
        album_id = extract_id(album, "id", "album_id", "uuid")
        if not album_id:
            continue
        
        # Create 3-6 sales per album
        for sale_idx in range(3 + (idx % 4)):
            sale = AlbumSale.objects.create(
                album_id=album_id,
                units=1 + (idx + sale_idx) % 4,
                amount=9.99 + ((idx * 7 + sale_idx * 3) % 20),
                currency="EUR",
            )
            sale.purchased_at = base_date + timedelta(
                days=idx + sale_idx,
                hours=(idx * 2 + sale_idx) % 24
            )
            sale.save(update_fields=["purchased_at"])
            sale_count += 1
    
    print(f"  ✓ Created {sale_count} album sales")
    
    print(f"\n[SEEDER] ✅ Auto-seeding from contenidos complete!")
    print(f"  Ratings:  {Rating.objects.count()}")
    print(f"  Playbacks: {Playback.objects.count()}")
    print(f"  Sales:    {AlbumSale.objects.count()}")
    
    return True
