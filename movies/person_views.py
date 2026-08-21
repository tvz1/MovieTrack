import requests

from django.conf import settings

from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WatchedMovie


class PersonMoviesView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        person_id,
    ):
        url = (
            f"https://api.themoviedb.org/3/"
            f"person/{person_id}"
        )

        headers = {
            "Authorization":
                f"Bearer "
                f"{settings.TMDB_ACCESS_TOKEN}",
            "accept":
                "application/json",
        }

        params = {
            "language": "en-US",
            "append_to_response":
                "combined_credits",
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=10,
            )

        except requests.RequestException:
            return Response(
                {
                    "error":
                        "Could not connect "
                        "to TMDb."
                },
                status=500,
            )

        if response.status_code != 200:
            return Response(
                {
                    "error":
                        "Could not fetch "
                        "person data."
                },
                status=response.status_code,
            )

        data = response.json()

        credits = (
            data.get(
                "combined_credits",
                {},
            )
            .get(
                "cast",
                [],
            )
        )

        watched_movies = set(
            WatchedMovie.objects.filter(
                user=request.user,
                movie__media_type=
                    "movie",
            ).values_list(
                "movie__tmdb_id",
                flat=True,
            )
        )

        watched_tv = set(
            WatchedMovie.objects.filter(
                user=request.user,
                movie__media_type=
                    "tv",
            ).values_list(
                "movie__tmdb_id",
                flat=True,
            )
        )

        unique_items = {}

        for item in credits:
            media_type = item.get(
                "media_type"
            )

            if media_type not in {
                "movie",
                "tv",
            }:
                continue

            if not item.get(
                "poster_path"
            ):
                continue

            tmdb_id = item.get(
                "id"
            )

            if tmdb_id is None:
                continue

            # Film i TV mogu imati isti
            # numerički TMDb ID.
            key = (
                media_type,
                tmdb_id,
            )

            if key in unique_items:
                continue

            normalized = dict(item)

            normalized[
                "media_type"
            ] = media_type

            if media_type == "tv":
                normalized["title"] = (
                    item.get("name")
                    or item.get(
                        "original_name"
                    )
                    or ""
                )

                normalized[
                    "release_date"
                ] = (
                    item.get(
                        "first_air_date"
                    )
                    or ""
                )

                normalized["watched"] = (
                    tmdb_id
                    in watched_tv
                )

            else:
                normalized["title"] = (
                    item.get("title")
                    or item.get(
                        "original_title"
                    )
                    or ""
                )

                normalized[
                    "release_date"
                ] = (
                    item.get(
                        "release_date"
                    )
                    or ""
                )

                normalized["watched"] = (
                    tmdb_id
                    in watched_movies
                )

            unique_items[key] = (
                normalized
            )

        items = list(
            unique_items.values()
        )

        items.sort(
            key=lambda item:
                item.get(
                    "popularity",
                    0,
                )
                or 0,
            reverse=True,
        )

        movies = [
            item
            for item in items
            if (
                item["media_type"]
                == "movie"
            )
        ]

        series = [
            item
            for item in items
            if (
                item["media_type"]
                == "tv"
            )
        ]

        return Response({
            "id":
                data.get("id"),
            "name":
                data.get("name"),
            "biography":
                data.get(
                    "biography",
                    "",
                ),
            "birthday":
                data.get(
                    "birthday"
                ),
            "place_of_birth":
                data.get(
                    "place_of_birth"
                ),
            "profile_path":
                data.get(
                    "profile_path"
                ),

            # Novi objedinjeni popis.
            "credits":
                items,

            # Zadržavamo "movies"
            # zbog postojećeg Fluttera.
            "movies":
                movies,

            # Novi TV popis.
            "series":
                series,
        })