from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.core.management import call_command

def _seed_defaults(sender, **kwargs):
    # Import inside to avoid app registry issues
    from django.contrib.auth.models import User
    from datetime import datetime, timedelta
    from stats.models import Rating, Playback, AlbumSale
    from stats.seeder import seed_from_contenidos

    # Only seed if tables are empty
    if Rating.objects.exists() or Playback.objects.exists() or AlbumSale.objects.exists():
        return

    # First try fixture-based load to keep data consistent across collaborators
    try:
        call_command("loaddata", "sample_data")
        print("[APP-CONFIG] Successfully loaded sample_data fixture")
        return
    except Exception as e:
        print(f"[APP-CONFIG] Fixture load failed ({e}), trying dynamic seeding from contenidos...")

    # If still empty, try dynamic seeding from contenidos
    if not seed_from_contenidos():
        # If no contenidos data available, fallback to deterministic in-code dataset
        print("[APP-CONFIG] Dynamic seeding from contenidos failed, using static fallback...")
        # Ensure basic users exist (deterministic)
        users = []
        for uname in ["user1", "user2", "user3", "anonymous"]:
            user, _ = User.objects.get_or_create(
                username=uname,
                defaults={"email": f"{uname}@example.com", "is_active": True},
            )
            users.append(user)

        # Deterministic base date
        base = datetime(2025, 11, 27, 12, 0, 0)

        # Ratings: target ~19 records, matching sample distribution shape
        rating_specs = [
            ("2", "2", users[-1], 5),
            ("2", "2", users[-1], 3),
            ("2", "2", users[-1], 5),
            ("2", "2", users[-1], 5),
            ("3", "3", users[-1], 3),
            ("1", "1", users[-1], 5),
            ("1", "1", users[-1], 0),
            ("1", "1", users[-1], 0),
            ("1", "1", users[-1], 0),
            ("1", "1", users[0], 4),
            ("1", "1", users[-1], 3),
            ("1", "1", users[-1], 1),
            ("1", "1", users[-1], 1),
            ("1", "1", users[-1], 5),
            ("1", "1", users[-1], 5),
            ("2", "2", users[-1], 1),
            ("2", "2", users[-1], 5),
            ("2", "2", users[-1], 3),
            ("1", "1", users[-1], 5),
        ]
        for idx, (song_id, artist_id, user, stars) in enumerate(rating_specs):
            r = Rating.objects.create(
                song_id=song_id,
                artist_id=artist_id,
                user=user,
                stars=stars,
                comment="",
            )
            # override auto_now_add timestamps for consistency
            r.rated_at = base + timedelta(minutes=idx)
            r.save(update_fields=["rated_at"])

        # Playbacks: target ~13 records, zero seconds, valid
        playback_times = [
            base + timedelta(hours=8, minutes=5),
            base + timedelta(hours=8, minutes=20),
            base + timedelta(hours=8, minutes=22),
            base + timedelta(hours=10, minutes=3),
            base + timedelta(hours=10, minutes=3, seconds=10),
            base + timedelta(hours=11, minutes=9),
            base + timedelta(hours=11, minutes=9, seconds=10),
            base + timedelta(hours=11, minutes=9, seconds=20),
            base + timedelta(days=1, hours=7, minutes=38),
            base + timedelta(days=21, hours=3, minutes=18, seconds=35),
            base + timedelta(days=21, hours=3, minutes=18, seconds=35, milliseconds=100),
            base + timedelta(days=21, hours=3, minutes=18, seconds=35, milliseconds=200),
            base + timedelta(days=21, hours=3, minutes=18, seconds=36),
        ]
        for idx, played_at in enumerate(playback_times):
            song_id = "1" if idx < 9 else "2"
            p = Playback.objects.create(
                song_id=song_id,
                seconds=0,
                valid=True,
            )
            p.played_at = played_at
            p.save(update_fields=["played_at"])

        # Album sales: deterministic 102 records across albums 1..4
        sales_records = []
        idx = 0
        for album_id in ["1", "2", "3", "4"]:
            for _ in range(30):  # 120 then trim
                units = (idx % 4) + 1
                amount = round((idx % 10 + 1) * 2.73, 2)
                when = base + timedelta(minutes=idx)
                sales_records.append((album_id, when, units, amount, "EUR"))
                idx += 1
        sales_records = sales_records[:102]
        for album_id, when, units, amount, currency in sales_records:
            s = AlbumSale.objects.create(
                album_id=album_id,
                units=units,
                amount=amount,
                currency=currency,
            )
            s.purchased_at = when
            s.save(update_fields=["purchased_at"])


class StatsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stats'

    def ready(self):
        # Seed after migrations on first run
        # COMENTADO: para control manual del seeding ejecuta seed.py explícitamente
        # post_migrate.connect(_seed_defaults, sender=self)
        pass
