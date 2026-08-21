from datetime import timedelta

import requests

from django.conf import settings
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WatchedMovie, WatchlistMovie, FavoriteMovie


def tmdb_headers():
    return {
        "Authorization": f"Bearer {settings.TMDB_ACCESS_TOKEN}",
        "accept": "application/json",
    }


def normalize_tmdb_item(item, media_type):
    result = dict(item)
    result["media_type"] = media_type

    if media_type == "tv":
        result["title"] = item.get("name") or item.get("original_name") or ""
        result["release_date"] = item.get("first_air_date") or ""
    else:
        result["title"] = item.get("title") or item.get("original_title") or ""
        result["release_date"] = item.get("release_date") or ""

    return result


def user_status_sets(user, media_type):
    watched_ids = set(
        WatchedMovie.objects.filter(
            user=user,
            movie__media_type=media_type,
        ).values_list("movie__tmdb_id", flat=True)
    )

    watchlist_ids = set(
        WatchlistMovie.objects.filter(
            user=user,
            movie__media_type=media_type,
        ).values_list("movie__tmdb_id", flat=True)
    )

    favorite_ids = set(
        FavoriteMovie.objects.filter(
            user=user,
            movie__media_type=media_type,
        ).values_list("movie__tmdb_id", flat=True)
    )

    return watched_ids, watchlist_ids, favorite_ids


class MovieCatalogView(APIView):
    permission_classes = [IsAuthenticated]

    MOVIE_SORTS = {
        "popular": "popularity.desc",
        "newest": "primary_release_date.desc",
        "oldest": "primary_release_date.asc",
        "top_rated": "vote_average.desc",
    }

    TV_SORTS = {
        "popular": "popularity.desc",
        "newest": "first_air_date.desc",
        "oldest": "first_air_date.asc",
        "top_rated": "vote_average.desc",
    }

    UPCOMING_SORTS = {
        "release_soonest": "primary_release_date.asc",
        "release_latest": "primary_release_date.desc",
        "popular": "popularity.desc",
    }

    def get(self, request):
        mode = request.query_params.get("mode", "movies").strip().lower()

        if mode == "series":
            mode = "tv"

        if mode not in {"movies", "tv", "upcoming"}:
            return Response({"error": "Invalid catalog mode."}, status=400)

        try:
            page = int(request.query_params.get("page", 1))
        except ValueError:
            page = 1

        page = max(page, 1)

        sort = request.query_params.get("sort", "").strip().lower()

        if not sort:
            sort = "release_soonest" if mode == "upcoming" else "popular"

        year_param = request.query_params.get("year", "").strip()
        genre_param = request.query_params.get("genre", "").strip()
        country_param = request.query_params.get("country", "").strip().upper()

        today = timezone.now().date()
        media_type = "tv" if mode == "tv" else "movie"

        if sort == "trending":
            if mode == "upcoming":
                return Response(
                    {"error": "Trending is not available for Upcoming."},
                    status=400,
                )

            url = (
                "https://api.themoviedb.org/3/"
                f"trending/{media_type}/day"
            )

            params = {
                "language": "en-US",
                "page": page,
            }

        else:
            url = (
                "https://api.themoviedb.org/3/"
                f"discover/{media_type}"
            )

            params = {
                "language": "en-US",
                "include_adult": False,
                "page": page,
            }

            if media_type == "movie":
                params["include_video"] = False

            if mode == "upcoming":
                if sort not in self.UPCOMING_SORTS:
                    return Response(
                        {"error": "Invalid Upcoming sort."},
                        status=400,
                    )

                params["sort_by"] = self.UPCOMING_SORTS[sort]
                params["primary_release_date.gte"] = today.isoformat()
                params["primary_release_date.lte"] = (
                    today + timedelta(days=365)
                ).isoformat()

            elif mode == "tv":
                if sort not in self.TV_SORTS:
                    return Response(
                        {"error": "Invalid TV sort."},
                        status=400,
                    )

                params["sort_by"] = self.TV_SORTS[sort]
                params["first_air_date.lte"] = today.isoformat()
                params["vote_count.gte"] = 200 if sort == "top_rated" else 5

            else:
                if sort not in self.MOVIE_SORTS:
                    return Response(
                        {"error": "Invalid Movie sort."},
                        status=400,
                    )

                params["sort_by"] = self.MOVIE_SORTS[sort]
                params["primary_release_date.lte"] = today.isoformat()
                params["vote_count.gte"] = 200 if sort == "top_rated" else 15

            if year_param:
                try:
                    year = int(year_param)
                except ValueError:
                    return Response(
                        {"error": "Year must be a number."},
                        status=400,
                    )

                if media_type == "tv":
                    if not (1900 <= year <= today.year):
                        return Response({"error": "Invalid year."}, status=400)

                    params["first_air_date_year"] = year
                else:
                    max_year = today.year + 1 if mode == "upcoming" else today.year

                    if not (1870 <= year <= max_year):
                        return Response({"error": "Invalid year."}, status=400)

                    params["primary_release_year"] = year

            if genre_param:
                params["with_genres"] = genre_param

            if country_param:
                params["with_origin_country"] = country_param

        try:
            response = requests.get(
                url,
                headers=tmdb_headers(),
                params=params,
                timeout=10,
            )
        except requests.RequestException:
            return Response(
                {"error": "Could not connect to TMDb."},
                status=500,
            )

        if response.status_code != 200:
            return Response(
                {"error": "Could not fetch catalog from TMDb."},
                status=response.status_code,
            )

        data = response.json()

        results = []

        for item in data.get("results", []):
            if not item.get("poster_path"):
                continue

            results.append(
                normalize_tmdb_item(item, media_type)
            )

        watched_ids, watchlist_ids, favorite_ids = user_status_sets(
            request.user,
            media_type,
        )

        for item in results:
            tmdb_id = item.get("id")
            item["watched"] = tmdb_id in watched_ids
            item["in_watchlist"] = tmdb_id in watchlist_ids
            item["favorite"] = tmdb_id in favorite_ids

        return Response({
            "mode": mode,
            "media_type": media_type,
            "sort": sort,
            "page": data.get("page", page),
            "total_pages": data.get("total_pages", 1),
            "total_results": data.get("total_results", len(results)),
            "results": results,
        })