import requests

from django.conf import settings

from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WatchedMovie


class MovieRecommendationsView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        tmdb_id,
        media_type="movie",
    ):
        if media_type not in {
            "movie",
            "tv",
        }:
            return Response(
                {
                    "error":
                        "Invalid media type."
                },
                status=400,
            )

        url = (
            f"https://api.themoviedb.org/3/"
            f"{media_type}/"
            f"{tmdb_id}/"
            f"recommendations"
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
            "page": 1,
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
                        "recommendations."
                },
                status=response.status_code,
            )

        data = response.json()

        recommendations = []

        for item in data.get(
            "results",
            [],
        ):
            if not item.get(
                "poster_path"
            ):
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

            recommendations.append(
                normalized
            )

        watched_tmdb_ids = set(
            WatchedMovie.objects.filter(
                user=request.user,
                movie__media_type=
                    media_type,
            ).values_list(
                "movie__tmdb_id",
                flat=True,
            )
        )

        for item in recommendations:
            item["watched"] = (
                item.get("id")
                in watched_tmdb_ids
            )

        return Response({
            "media_type":
                media_type,
            "results":
                recommendations,
        })