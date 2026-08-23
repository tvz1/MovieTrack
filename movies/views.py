from collections import Counter
from datetime import timedelta
import hashlib
import secrets

import requests

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    CreateAPIView,
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Movie,
    WatchedMovie,
    WatchlistMovie,
    FavoriteMovie,
    WatchedEpisode,
    UserProfile,
    PasswordResetCode,
)

from .serializers import (
    MovieSerializer,
    WatchedMovieSerializer,
    WatchlistMovieSerializer,
    FavoriteMovieSerializer,
    RegisterSerializer,
    UserSerializer,
)


def tmdb_headers():
    return {
        "Authorization":
            f"Bearer {settings.TMDB_ACCESS_TOKEN}",
        "accept": "application/json",
    }


def valid_media_type(media_type):
    return media_type in {
        "movie",
        "tv",
    }


def normalize_tmdb_item(
    item,
    media_type=None,
):
    detected_type = (
        media_type
        or item.get("media_type")
        or "movie"
    )

    if detected_type == "tv":
        title = (
            item.get("name")
            or item.get("original_name")
            or ""
        )

        release_date = (
            item.get("first_air_date")
            or ""
        )

    else:
        detected_type = "movie"

        title = (
            item.get("title")
            or item.get("original_title")
            or ""
        )

        release_date = (
            item.get("release_date")
            or ""
        )

    result = dict(item)

    result["media_type"] = detected_type
    result["title"] = title
    result["release_date"] = release_date

    return result


def user_status_sets(
    user,
    media_type,
):
    watched_ids = set(
        WatchedMovie.objects.filter(
            user=user,
            movie__media_type=media_type,
        ).values_list(
            "movie__tmdb_id",
            flat=True,
        )
    )

    watchlist_ids = set(
        WatchlistMovie.objects.filter(
            user=user,
            movie__media_type=media_type,
        ).values_list(
            "movie__tmdb_id",
            flat=True,
        )
    )

    favorite_ids = set(
        FavoriteMovie.objects.filter(
            user=user,
            movie__media_type=media_type,
        ).values_list(
            "movie__tmdb_id",
            flat=True,
        )
    )

    return (
        watched_ids,
        watchlist_ids,
        favorite_ids,
    )


class MovieListView(ListCreateAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer


class MovieDetailView(
    RetrieveUpdateDestroyAPIView
):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer


# ==========================================================
# SEARCH
# Movies + TV together
# ==========================================================

class MovieSearchView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        query = (
            request.query_params
            .get("query", "")
            .strip()
        )

        if not query:
            return Response(
                {
                    "error":
                        "Query parameter is required."
                },
                status=400,
            )

        url = (
            "https://api.themoviedb.org/3/"
            "search/multi"
        )

        params = {
            "query": query,
            "include_adult": False,
            "language": "en-US",
            "page": 1,
        }

        try:
            response = requests.get(
                url,
                headers=tmdb_headers(),
                params=params,
                timeout=10,
            )

        except requests.RequestException:
            return Response(
                {
                    "error":
                        "Could not connect to TMDb."
                },
                status=500,
            )

        if response.status_code != 200:
            return Response(
                {
                    "error":
                        "Could not search TMDb."
                },
                status=response.status_code,
            )

        data = response.json()

        raw_results = data.get(
            "results",
            [],
        )

        results = []

        for item in raw_results:
            media_type = item.get(
                "media_type"
            )

            # Multi search vraća i osobe.
            # Nama trenutno trebaju samo
            # filmovi i TV serije.
            if media_type not in {
                "movie",
                "tv",
            }:
                continue

            if not item.get("poster_path"):
                continue

            results.append(
                normalize_tmdb_item(
                    item,
                    media_type,
                )
            )

        watched_movie_ids = set(
            WatchedMovie.objects.filter(
                user=request.user,
                movie__media_type="movie",
            ).values_list(
                "movie__tmdb_id",
                flat=True,
            )
        )

        watched_tv_ids = set(
            WatchedMovie.objects.filter(
                user=request.user,
                movie__media_type="tv",
            ).values_list(
                "movie__tmdb_id",
                flat=True,
            )
        )

        watchlist_movie_ids = set(
            WatchlistMovie.objects.filter(
                user=request.user,
                movie__media_type="movie",
            ).values_list(
                "movie__tmdb_id",
                flat=True,
            )
        )

        watchlist_tv_ids = set(
            WatchlistMovie.objects.filter(
                user=request.user,
                movie__media_type="tv",
            ).values_list(
                "movie__tmdb_id",
                flat=True,
            )
        )

        favorite_movie_ids = set(
            FavoriteMovie.objects.filter(
                user=request.user,
                movie__media_type="movie",
            ).values_list(
                "movie__tmdb_id",
                flat=True,
            )
        )

        favorite_tv_ids = set(
            FavoriteMovie.objects.filter(
                user=request.user,
                movie__media_type="tv",
            ).values_list(
                "movie__tmdb_id",
                flat=True,
            )
        )

        for item in results:
            tmdb_id = item["id"]
            media_type = item["media_type"]

            if media_type == "tv":
                item["watched"] = (
                    tmdb_id
                    in watched_tv_ids
                )

                item["in_watchlist"] = (
                    tmdb_id
                    in watchlist_tv_ids
                )

                item["favorite"] = (
                    tmdb_id
                    in favorite_tv_ids
                )

            else:
                item["watched"] = (
                    tmdb_id
                    in watched_movie_ids
                )

                item["in_watchlist"] = (
                    tmdb_id
                    in watchlist_movie_ids
                )

                item["favorite"] = (
                    tmdb_id
                    in favorite_movie_ids
                )

        return Response({
            "page": data.get(
                "page",
                1,
            ),
            "total_pages": data.get(
                "total_pages",
                1,
            ),
            "results": results,
        })


# ==========================================================
# IMPORT
# Movie or TV
# ==========================================================

class MovieImportView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        tmdb_id,
        media_type="movie",
    ):
        if not valid_media_type(
            media_type
        ):
            return Response(
                {
                    "error":
                        "Invalid media type."
                },
                status=400,
            )

        url = (
            f"https://api.themoviedb.org/3/"
            f"{media_type}/{tmdb_id}"
        )

        try:
            response = requests.get(
                url,
                headers=tmdb_headers(),
                params={
                    "language": "en-US",
                },
                timeout=10,
            )

        except requests.RequestException:
            return Response(
                {
                    "error":
                        "Could not connect to TMDb."
                },
                status=500,
            )

        if response.status_code != 200:
            return Response(
                {
                    "error":
                        "Media could not be fetched "
                        "from TMDb."
                },
                status=response.status_code,
            )

        data = response.json()

        if media_type == "tv":
            title = (
                data.get("name")
                or data.get(
                    "original_name"
                )
                or ""
            )

            release_date = (
                data.get(
                    "first_air_date"
                )
                or None
            )

            episode_runtimes = (
                data.get(
                    "episode_run_time"
                )
                or []
            )

            runtime = (
                episode_runtimes[0]
                if episode_runtimes
                else None
            )

        else:
            title = (
                data.get("title")
                or data.get(
                    "original_title"
                )
                or ""
            )

            release_date = (
                data.get(
                    "release_date"
                )
                or None
            )

            runtime = data.get(
                "runtime"
            )

        media, created = (
            Movie.objects.update_or_create(
                tmdb_id=data["id"],
                media_type=media_type,
                defaults={
                    "title": title,
                    "release_date":
                        release_date,
                    "overview":
                        data.get(
                            "overview",
                            "",
                        ),
                    "poster_path":
                        data.get(
                            "poster_path"
                        )
                        or "",
                    "runtime": runtime,
                    "genres": [
                        genre["name"]
                        for genre
                        in data.get(
                            "genres",
                            [],
                        )
                    ],
                },
            )
        )

        serializer = MovieSerializer(
            media,
            context={
                "request": request
            },
        )

        return Response(
            {
                "created": created,
                "movie":
                    serializer.data,
            },
            status=(
                201
                if created
                else 200
            ),
        )


# ==========================================================
# WATCHED
# ==========================================================

class MarkWatchedView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        movie_id,
    ):
        movie = get_object_or_404(
            Movie,
            id=movie_id,
        )

        watched_movie, created = (
            WatchedMovie.objects
            .get_or_create(
                user=request.user,
                movie=movie,
            )
        )

        serializer = (
            WatchedMovieSerializer(
                watched_movie,
                context={
                    "request": request
                },
            )
        )

        return Response(
            {
                "created": created,
                "watched":
                    serializer.data,
            },
            status=(
                201
                if created
                else 200
            ),
        )


class WatchedMovieListView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        watched_movies = (
            WatchedMovie.objects
            .filter(
                user=request.user
            )
            .select_related(
                "movie"
            )
        )

        serializer = (
            WatchedMovieSerializer(
                watched_movies,
                many=True,
                context={
                    "request": request
                },
            )
        )

        return Response(
            serializer.data
        )


class UnmarkWatchedView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def delete(
        self,
        request,
        movie_id,
    ):
        watched_movie = (
            get_object_or_404(
                WatchedMovie,
                user=request.user,
                movie_id=movie_id,
            )
        )

        watched_movie.delete()

        return Response(
            status=
                status.HTTP_204_NO_CONTENT
        )


# ==========================================================
# AUTH / USER
# ==========================================================

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = str(
            request.data.get("email", "")
        ).strip().lower()

        # Always return the same message so the API does not reveal
        # whether an account with this email exists.
        generic_response = {
            "message":
                "If an account with that email exists, "
                "a reset code has been sent."
        }

        if not email:
            return Response(
                {"error": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = (
            User.objects
            .filter(email__iexact=email)
            .order_by("id")
            .first()
        )

        if user is None:
            return Response(
                generic_response,
                status=status.HTTP_200_OK,
            )

        # Invalidate older unused codes.
        PasswordResetCode.objects.filter(
            user=user,
            used=False,
        ).update(used=True)

        code = f"{secrets.randbelow(1000000):06d}"
        code_hash = hashlib.sha256(
            code.encode("utf-8")
        ).hexdigest()

        PasswordResetCode.objects.create(
            user=user,
            code_hash=code_hash,
            expires_at=(
                timezone.now()
                + timedelta(minutes=10)
            ),
        )

        send_mail(
            subject="WatchLibrary password reset code",
            message=(
                "Your WatchLibrary password reset code is:\n\n"
                f"{code}\n\n"
                "This code expires in 10 minutes. "
                "If you did not request a password reset, "
                "you can ignore this email."
            ),
            from_email=getattr(
                settings,
                "DEFAULT_FROM_EMAIL",
                None,
            ),
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response(
            generic_response,
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = str(
            request.data.get("email", "")
        ).strip().lower()

        code = str(
            request.data.get("code", "")
        ).strip()

        new_password = str(
            request.data.get("new_password", "")
        )

        if not email or not code or not new_password:
            return Response(
                {
                    "error":
                        "Email, code and new password are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            len(code) != 6
            or not code.isdigit()
        ):
            return Response(
                {"error": "Invalid or expired reset code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_password) < 8:
            return Response(
                {
                    "error":
                        "Password must contain at least 8 characters."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = (
            User.objects
            .filter(email__iexact=email)
            .order_by("id")
            .first()
        )

        if user is None:
            return Response(
                {"error": "Invalid or expired reset code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        code_hash = hashlib.sha256(
            code.encode("utf-8")
        ).hexdigest()

        reset = (
            PasswordResetCode.objects
            .filter(
                user=user,
                code_hash=code_hash,
                used=False,
                expires_at__gt=timezone.now(),
            )
            .order_by("-created_at")
            .first()
        )

        if reset is None:
            return Response(
                {"error": "Invalid or expired reset code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        reset.used = True
        reset.save(update_fields=["used"])

        PasswordResetCode.objects.filter(
            user=user,
            used=False,
        ).update(used=True)

        return Response(
            {
                "message":
                    "Password changed successfully. "
                    "You can now sign in."
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer


class MeView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        serializer = UserSerializer(
            request.user
        )

        return Response(
            serializer.data
        )


# ==========================================================
# WATCHLIST
# ==========================================================

class WatchlistView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        items = (
            WatchlistMovie.objects
            .filter(
                user=request.user
            )
            .select_related(
                "movie"
            )
        )

        serializer = (
            WatchlistMovieSerializer(
                items,
                many=True,
                context={
                    "request": request
                },
            )
        )

        return Response(
            serializer.data
        )

    def post(
        self,
        request,
        movie_id,
    ):
        movie = get_object_or_404(
            Movie,
            id=movie_id,
        )

        item, created = (
            WatchlistMovie.objects
            .get_or_create(
                user=request.user,
                movie=movie,
            )
        )

        serializer = (
            WatchlistMovieSerializer(
                item,
                context={
                    "request": request
                },
            )
        )

        return Response(
            {
                "created": created,
                "watchlist":
                    serializer.data,
            },
            status=(
                201
                if created
                else 200
            ),
        )


class RemoveFromWatchlistView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def delete(
        self,
        request,
        movie_id,
    ):
        item = get_object_or_404(
            WatchlistMovie,
            user=request.user,
            movie_id=movie_id,
        )

        item.delete()

        return Response(
            status=
                status.HTTP_204_NO_CONTENT
        )


# ==========================================================
# FAVORITES
# ==========================================================

class FavoriteView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        items = (
            FavoriteMovie.objects
            .filter(
                user=request.user
            )
            .select_related(
                "movie"
            )
        )

        serializer = (
            FavoriteMovieSerializer(
                items,
                many=True,
                context={
                    "request": request
                },
            )
        )

        return Response(
            serializer.data
        )

    def post(
        self,
        request,
        movie_id,
    ):
        movie = get_object_or_404(
            Movie,
            id=movie_id,
        )

        item, created = (
            FavoriteMovie.objects
            .get_or_create(
                user=request.user,
                movie=movie,
            )
        )

        serializer = (
            FavoriteMovieSerializer(
                item,
                context={
                    "request": request
                },
            )
        )

        return Response(
            {
                "created": created,
                "favorite":
                    serializer.data,
            },
            status=(
                201
                if created
                else 200
            ),
        )


class RemoveFavoriteView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def delete(
        self,
        request,
        movie_id,
    ):
        item = get_object_or_404(
            FavoriteMovie,
            user=request.user,
            movie_id=movie_id,
        )

        item.delete()

        return Response(
            status=
                status.HTTP_204_NO_CONTENT
        )


# ==========================================================
# CATALOG
#
# mode:
# movies
# tv
# upcoming
# ==========================================================

class MovieCatalogView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        mode = (
            request.query_params
            .get(
                "mode",
                "movies",
            )
            .strip()
        )

        if mode == "series":
            mode = "tv"

        if mode not in {
            "movies",
            "tv",
            "upcoming",
        }:
            return Response(
                {
                    "error":
                        "Invalid catalog mode."
                },
                status=400,
            )

        today = timezone.now().date()

        try:
            page = int(
                request.query_params
                .get(
                    "page",
                    1,
                )
            )

        except ValueError:
            page = 1

        page = max(
            page,
            1,
        )

        year_param = (
            request.query_params
            .get(
                "year",
                "",
            )
            .strip()
        )

        genre_param = (
            request.query_params
            .get(
                "genre",
                "",
            )
            .strip()
        )

        country_param = (
            request.query_params
            .get(
                "country",
                "",
            )
            .strip()
        )

        media_type = (
            "tv"
            if mode == "tv"
            else "movie"
        )

        url = (
            f"https://api.themoviedb.org/3/"
            f"discover/{media_type}"
        )

        params = {
            "language": "en-US",
            "include_adult": False,
            "sort_by":
                "popularity.desc",
            "page": page,
        }

        if media_type == "movie":
            params[
                "include_video"
            ] = False

        year = None

        # ----------------------------------
        # UPCOMING MOVIES
        # ----------------------------------

        if mode == "upcoming":
            one_year_from_now = (
                today
                + timedelta(
                    days=365
                )
            )

            params[
                "primary_release_date.gte"
            ] = today.isoformat()

            params[
                "primary_release_date.lte"
            ] = (
                one_year_from_now
                .isoformat()
            )

        # ----------------------------------
        # SERIES
        # ----------------------------------

        elif mode == "tv":
            params[
                "first_air_date.lte"
            ] = today.isoformat()

            params[
                "vote_count.gte"
            ] = 5

            if year_param:
                try:
                    year = int(
                        year_param
                    )

                except ValueError:
                    return Response(
                        {
                            "error":
                                "Year must be "
                                "a number."
                        },
                        status=400,
                    )

                if not (
                    1900
                    <= year
                    <= today.year
                ):
                    return Response(
                        {
                            "error":
                                "Invalid year."
                        },
                        status=400,
                    )

                params[
                    "first_air_date_year"
                ] = year

        # ----------------------------------
        # NORMAL MOVIES
        # ----------------------------------

        else:
            params[
                "primary_release_date.lte"
            ] = today.isoformat()

            params[
                "vote_count.gte"
            ] = 15

            if year_param:
                try:
                    year = int(
                        year_param
                    )

                except ValueError:
                    return Response(
                        {
                            "error":
                                "Year must be "
                                "a number."
                        },
                        status=400,
                    )

                if not (
                    1870
                    <= year
                    <= today.year
                ):
                    return Response(
                        {
                            "error":
                                "Invalid year."
                        },
                        status=400,
                    )

                params[
                    "primary_release_year"
                ] = year

            else:
                # Zadržavamo postojeće
                # ponašanje Home Movies.
                year = today.year

                params[
                    "primary_release_year"
                ] = year

        if genre_param:
            params[
                "with_genres"
            ] = genre_param

        if country_param:
            params[
                "with_origin_country"
            ] = (
                country_param.upper()
            )

        try:
            response = requests.get(
                url,
                headers=tmdb_headers(),
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
                        "catalog from TMDb."
                },
                status=response.status_code,
            )

        data = response.json()

        results = []

        for item in data.get(
            "results",
            [],
        ):
            if not item.get(
                "poster_path"
            ):
                continue

            results.append(
                normalize_tmdb_item(
                    item,
                    media_type,
                )
            )

        (
            watched_ids,
            watchlist_ids,
            favorite_ids,
        ) = user_status_sets(
            request.user,
            media_type,
        )

        for item in results:
            tmdb_id = item["id"]

            item["watched"] = (
                tmdb_id
                in watched_ids
            )

            item["in_watchlist"] = (
                tmdb_id
                in watchlist_ids
            )

            item["favorite"] = (
                tmdb_id
                in favorite_ids
            )

        return Response({
            "mode": mode,
            "media_type":
                media_type,
            "year": year,
            "page": data.get(
                "page",
                page,
            ),
            "total_pages":
                data.get(
                    "total_pages",
                    1,
                ),
            "results": results,
        })


# ==========================================================
# FULL DETAILS
# Movie or TV
# ==========================================================

class MovieFullDetailView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        tmdb_id,
        media_type="movie",
    ):
        if not valid_media_type(
            media_type
        ):
            return Response(
                {
                    "error":
                        "Invalid media type."
                },
                status=400,
            )

        url = (
            f"https://api.themoviedb.org/3/"
            f"{media_type}/{tmdb_id}"
        )

        params = {
            "language": "en-US",
            "append_to_response":
                "credits,videos,"
                "external_ids",
        }

        try:
            response = requests.get(
                url,
                headers=tmdb_headers(),
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
                        "details from TMDb."
                },
                status=response.status_code,
            )

        data = response.json()

        # ----------------------------------
        # CAST
        # ----------------------------------

        cast = (
            data.get(
                "credits",
                {},
            )
            .get(
                "cast",
                [],
            )
        )[:10]

        cast_data = [
            {
                "id":
                    person.get("id"),
                "name":
                    person.get("name"),
                "character":
                    person.get(
                        "character"
                    ),
                "profile_path":
                    person.get(
                        "profile_path"
                    ),
            }
            for person in cast
        ]

        # ----------------------------------
        # DIRECTOR / CREATOR
        # ----------------------------------

        director = None

        if media_type == "movie":
            crew = (
                data.get(
                    "credits",
                    {},
                )
                .get(
                    "crew",
                    [],
                )
            )

            director = next(
                (
                    person
                    for person in crew
                    if person.get("job")
                    == "Director"
                ),
                None,
            )

        else:
            creators = (
                data.get(
                    "created_by"
                )
                or []
            )

            if creators:
                creator = creators[0]

                director = {
                    "id":
                        creator.get("id"),
                    "name":
                        creator.get("name"),
                    "profile_path":
                        creator.get(
                            "profile_path"
                        ),
                }

        # ----------------------------------
        # TRAILER
        # ----------------------------------

        videos = (
            data.get(
                "videos",
                {},
            )
            .get(
                "results",
                [],
            )
        )

        youtube_trailers = [
            video
            for video in videos
            if (
                video.get("site")
                == "YouTube"
                and
                video.get("type")
                == "Trailer"
            )
        ]

        official_trailer = next(
            (
                video
                for video
                in youtube_trailers
                if (
                    video.get(
                        "official"
                    )
                    is True
                )
            ),
            None,
        )

        trailer = (
            official_trailer
            or (
                youtube_trailers[0]
                if youtube_trailers
                else None
            )
        )

        # ----------------------------------
        # NORMALIZED TITLE / DATE / RUNTIME
        # ----------------------------------

        if media_type == "tv":
            title = (
                data.get("name")
                or data.get(
                    "original_name"
                )
                or ""
            )

            release_date = (
                data.get(
                    "first_air_date"
                )
                or ""
            )

            runtimes = (
                data.get(
                    "episode_run_time"
                )
                or []
            )

            runtime = (
                runtimes[0]
                if runtimes
                else None
            )

        else:
            title = (
                data.get("title")
                or ""
            )

            release_date = (
                data.get(
                    "release_date"
                )
                or ""
            )

            runtime = data.get(
                "runtime"
            )

        # ----------------------------------
        # USER STATUS
        # ----------------------------------

        local_movie = (
            Movie.objects.filter(
                tmdb_id=tmdb_id,
                media_type=media_type,
            )
            .first()
        )

        watched = False
        in_watchlist = False
        favorite = False

        if local_movie:
            watched = (
                WatchedMovie.objects
                .filter(
                    user=request.user,
                    movie=local_movie,
                )
                .exists()
            )

            in_watchlist = (
                WatchlistMovie.objects
                .filter(
                    user=request.user,
                    movie=local_movie,
                )
                .exists()
            )

            favorite = (
                FavoriteMovie.objects
                .filter(
                    user=request.user,
                    movie=local_movie,
                )
                .exists()
            )

        response_data = {
            "tmdb_id":
                data.get("id"),
            "media_type":
                media_type,
            "imdb_id":
                data.get(
                    "external_ids",
                    {},
                ).get(
                    "imdb_id"
                ),
            "title": title,
            "tagline":
                data.get(
                    "tagline"
                ),
            "overview":
                data.get(
                    "overview"
                ),
            "release_date":
                release_date,
            "runtime": runtime,
            "vote_average":
                data.get(
                    "vote_average"
                ),
            "vote_count":
                data.get(
                    "vote_count"
                ),
            "poster_path":
                data.get(
                    "poster_path"
                ),
            "backdrop_path":
                data.get(
                    "backdrop_path"
                ),
            "genres": [
                genre.get("name")
                for genre
                in data.get(
                    "genres",
                    [],
                )
            ],
            "director": (
                {
                    "id":
                        director.get(
                            "id"
                        ),
                    "name":
                        director.get(
                            "name"
                        ),
                    "profile_path":
                        director.get(
                            "profile_path"
                        ),
                }
                if director
                else None
            ),
            "cast":
                cast_data,
            "trailer_key":
                (
                    trailer.get(
                        "key"
                    )
                    if trailer
                    else None
                ),
            "watched":
                watched,
            "in_watchlist":
                in_watchlist,
            "favorite":
                favorite,
        }

        if media_type == "tv":
            response_data.update({
                "number_of_seasons":
                    data.get(
                        "number_of_seasons"
                    ),
                "number_of_episodes":
                    data.get(
                        "number_of_episodes"
                    ),
                "status":
                    data.get(
                        "status"
                    ),
                "last_air_date":
                    data.get(
                        "last_air_date"
                    ),
                "seasons":
                    data.get(
                        "seasons",
                        [],
                    ),
            })

        return Response(
            response_data
        )


# ==========================================================
# PROFILE
# ==========================================================

class ProfileView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    AVATAR_NAMES = {
        "horror",
        "action",
        "sci_fi",
        "fantasy",
        "thriller",
        "comedy",
        "drama",
        "romance",
        "animation",
        "adventure",
        "mystery",
        "western",
    }

    def get(self, request):
        user = request.user

        profile, _ = (
            UserProfile.objects.get_or_create(
                user=user
            )
        )

        watched_qs = (
            WatchedMovie.objects
            .filter(user=user)
            .select_related("movie")
        )

        watched_count = watched_qs.count()

        watchlist_count = (
            WatchlistMovie.objects
            .filter(user=user)
            .count()
        )

        favorite_count = (
            FavoriteMovie.objects
            .filter(user=user)
            .count()
        )

        movies_watched = (
            watched_qs
            .filter(
                movie__media_type="movie",
            )
            .count()
        )

        series_watched = (
            watched_qs
            .filter(
                movie__media_type="tv",
            )
            .count()
        )

        episodes_watched = (
            WatchedEpisode.objects
            .filter(user=user)
            .count()
        )

        genre_counter = Counter()

        for watched_item in watched_qs:
            for genre in (
                watched_item.movie.genres
                or []
            ):
                genre_name = (
                    str(genre).strip()
                )

                if genre_name:
                    genre_counter[
                        genre_name
                    ] += 1

        favorite_genres = []

        for genre, count in (
            genre_counter
            .most_common(3)
        ):
            percentage = (
                round(
                    count
                    / watched_count
                    * 100
                )
                if watched_count
                else 0
            )

            favorite_genres.append({
                "name": genre,
                "count": count,
                "percentage":
                    percentage,
            })

        return Response({
            "id":
                user.id,

            "username":
                user.username,

            "email":
                user.email,

            "avatar":
                profile.avatar,

            "member_since":
                user.date_joined
                .strftime(
                    "%B %Y"
                ),

            "watched_count":
                watched_count,

            "watchlist_count":
                watchlist_count,

            "favorite_count":
                favorite_count,

            "movies_watched":
                movies_watched,

            "series_watched":
                series_watched,

            "episodes_watched":
                episodes_watched,

            "favorite_genres":
                favorite_genres,
        })

    def post(self, request):
        avatar = (
            request.query_params
            .get(
                "avatar",
                "",
            )
            .strip()
            .lower()
        )

        if avatar not in self.AVATAR_NAMES:
            return Response(
                {
                    "error":
                        "Invalid avatar."
                },
                status=400,
            )

        profile, _ = (
            UserProfile.objects.get_or_create(
                user=request.user
            )
        )

        profile.avatar = avatar
        profile.save(
            update_fields=[
                "avatar"
            ]
        )

        return Response({
            "avatar": profile.avatar
        })


# ==========================================================
# FILTER OPTIONS
# Movie genres + TV genres + countries
# ==========================================================

class MovieFilterOptionsView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        headers = tmdb_headers()

        try:
            movie_genres_response = (
                requests.get(
                    "https://api."
                    "themoviedb.org/3/"
                    "genre/movie/list",
                    headers=headers,
                    params={
                        "language":
                            "en-US"
                    },
                    timeout=10,
                )
            )

            tv_genres_response = (
                requests.get(
                    "https://api."
                    "themoviedb.org/3/"
                    "genre/tv/list",
                    headers=headers,
                    params={
                        "language":
                            "en-US"
                    },
                    timeout=10,
                )
            )

            countries_response = (
                requests.get(
                    "https://api."
                    "themoviedb.org/3/"
                    "configuration/"
                    "countries",
                    headers=headers,
                    params={
                        "language":
                            "en-US"
                    },
                    timeout=10,
                )
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

        if (
            movie_genres_response
            .status_code
            != 200
            or
            tv_genres_response
            .status_code
            != 200
            or
            countries_response
            .status_code
            != 200
        ):
            return Response(
                {
                    "error":
                        "Could not fetch "
                        "filter options."
                },
                status=500,
            )

        movie_genres = (
            movie_genres_response
            .json()
            .get(
                "genres",
                [],
            )
        )

        tv_genres = (
            tv_genres_response
            .json()
            .get(
                "genres",
                [],
            )
        )

        countries = (
            countries_response
            .json()
        )

        countries = sorted(
            countries,
            key=lambda country:
                country.get(
                    "english_name",
                    country.get(
                        "native_name",
                        "",
                    ),
                ),
        )

        # "genres" ostavljamo zbog
        # kompatibilnosti sa sadašnjim Flutterom.
        return Response({
            "genres":
                movie_genres,
            "movie_genres":
                movie_genres,
            "tv_genres":
                tv_genres,
            "countries":
                countries,
        })