import os
import django
from datetime import date, time, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.contrib.auth import get_user_model
from theaters.models import Theater, Movie, Show, Seat

User = get_user_model()

def seed():
    print("Seeding cinema data...")
    # Create or get admin
    admin, _ = User.objects.get_or_create(
        email='admin@seatlock.com',
        defaults={'username': 'admin', 'role': 'admin', 'is_superuser': True, 'is_staff': True}
    )
    admin.set_password('Admin@123')
    admin.save()

    # Create owner
    owner, _ = User.objects.get_or_create(
        email='owner@seatlock.com',
        defaults={'username': 'pvr_owner', 'role': 'owner'}
    )
    owner.set_password('Owner@123')
    owner.save()

    # Create customer user
    user, _ = User.objects.get_or_create(
        email='user@seatlock.com',
        defaults={'username': 'siva_kumar', 'role': 'user'}
    )
    user.set_password('User@123')
    user.save()

    # Theaters
    t1, _ = Theater.objects.get_or_create(
        name='PVR Superplex IMAX',
        location='Forum Mall, Koramangala, Bengaluru',
        owner=owner
    )
    t2, _ = Theater.objects.get_or_create(
        name='INOX Megaplex Luxe',
        location='Phoenix Marketcity, Whitefield, Bengaluru',
        owner=owner
    )

    movies_data = [
        {
            "title": "Dune: Part Two",
            "genre": "Sci-Fi / Adventure",
            "rating": 8.8,
            "duration": 166,
            "language": "English",
            "poster": "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=800&q=80",
            "banner": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1600&q=80",
            "desc": "Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family.",
            "theater": t1
        },
        {
            "title": "Oppenheimer",
            "genre": "Biography / Drama",
            "rating": 8.9,
            "duration": 180,
            "language": "English",
            "poster": "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?auto=format&fit=crop&w=800&q=80",
            "banner": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1600&q=80",
            "desc": "The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb.",
            "theater": t1
        },
        {
            "title": "Interstellar",
            "genre": "Sci-Fi / Adventure",
            "rating": 8.7,
            "duration": 169,
            "language": "English",
            "poster": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80",
            "banner": "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=1600&q=80",
            "desc": "When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot is tasked with piloting a spacecraft along with a team of researchers.",
            "theater": t2
        },
        {
            "title": "The Dark Knight",
            "genre": "Action / Crime",
            "rating": 9.0,
            "duration": 152,
            "language": "English",
            "poster": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=800&q=80",
            "banner": "https://images.unsplash.com/photo-1514306191717-452ec28c7814?auto=format&fit=crop&w=1600&q=80",
            "desc": "When the menace known as the Joker wreaks havoc and chaos on Gotham, Batman must accept one of the greatest psychological and physical tests.",
            "theater": t2
        }
    ]

    today = date.today()
    for mdata in movies_data:
        movie, _ = Movie.objects.get_or_create(
            title=mdata["title"],
            language=mdata["language"],
            owner=owner,
            defaults={
                "theater": mdata["theater"],
                "description": mdata["desc"],
                "duration_minutes": mdata["duration"],
                "genre": mdata["genre"],
                "rating": mdata["rating"],
                "poster_url": mdata["poster"],
                "banner_url": mdata["banner"],
                "release_date": today
            }
        )

        # Create 2 shows per movie
        show_times = [(time(14, 0), time(17, 0)), (time(19, 30), time(22, 30))]
        for st, et in show_times:
            show, created = Show.objects.get_or_create(
                theater=mdata["theater"],
                movie=movie,
                start_time=st,
                end_time=et,
                date=today,
                owner=owner,
                defaults={
                    "vip_price": 280.00,
                    "premium_price": 200.00,
                    "standard_price": 140.00
                }
            )
            if created:
                print(f"Created show: {movie.title} at {show.start_time} (100 seats generated)")

    print("Seeding completed successfully!")

if __name__ == '__main__':
    seed()
