import requests

from django.conf import settings
from django.core.management.base import BaseCommand

from movies.models import Movie


class Command(BaseCommand):
    help = "Refresh all local movie data from TMDb"

    def handle(self, *args, **options):
        movies = Movie.objects.all()

        total = movies.count()

        self.stdout.write(
            f"Refreshing {total} movies..."
        )

        headers = {
            "Authorization": f"Bearer {settings.TMDB_ACCESS_TOKEN}",
            "accept": "application/json",
        }

        for index, movie in enumerate(movies, start=1):
            url = (
                f"https://api.themoviedb.org/3/movie/"
                f"{movie.tmdb_id}"
            )

            try:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=10,
                )

                if response.status_code != 200:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[{index}/{total}] "
                            f"Could not fetch: {movie.title}"
                        )
                    )
                    continue

                data = response.json()

                movie.title = data.get(
                    "title",
                    movie.title,
                )

                movie.release_date = (
                    data.get("release_date") or None
                )

                movie.overview = data.get(
                    "overview",
                    "",
                )

                movie.poster_path = (
                    data.get("poster_path") or ""
                )

                movie.runtime = data.get(
                    "runtime"
                )

                movie.genres = [
                    genre["name"]
                    for genre in data.get(
                        "genres",
                        [],
                    )
                ]

                movie.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"[{index}/{total}] "
                        f"Updated: {movie.title}"
                    )
                )

            except requests.RequestException as error:
                self.stdout.write(
                    self.style.ERROR(
                        f"[{index}/{total}] "
                        f"Error updating {movie.title}: "
                        f"{error}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Movie refresh finished."
            )
        )