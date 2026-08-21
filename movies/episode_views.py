import requests

from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Movie,
    TVSeason,
    TVEpisode,
    WatchedEpisode,
)


def tmdb_headers():
    return {
        "Authorization":
            f"Bearer {settings.TMDB_ACCESS_TOKEN}",
        "accept": "application/json",
    }


def safe_date(value):
    if not value:
        return None

    return value


def date_to_string(value):
    if value is None:
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)


def ensure_local_series(
    tmdb_id,
):
    series = Movie.objects.filter(
        tmdb_id=tmdb_id,
        media_type="tv",
    ).first()

    if series:
        return series

    url = (
        f"https://api.themoviedb.org/3/"
        f"tv/{tmdb_id}"
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
        return None

    if response.status_code != 200:
        return None

    data = response.json()

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

    series, _ = (
        Movie.objects.update_or_create(
            tmdb_id=tmdb_id,
            media_type="tv",
            defaults={
                "title":
                    data.get("name")
                    or data.get(
                        "original_name"
                    )
                    or "",

                "release_date":
                    data.get(
                        "first_air_date"
                    )
                    or None,

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

                "runtime":
                    runtime,

                "genres": [
                    genre.get(
                        "name"
                    )
                    for genre
                    in data.get(
                        "genres",
                        [],
                    )
                    if genre.get(
                        "name"
                    )
                ],
            },
        )
    )

    return series


class TVSeasonDetailView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        tmdb_id,
        season_number,
    ):
        series = ensure_local_series(
            tmdb_id
        )

        if series is None:
            return Response(
                {
                    "error":
                        "Could not load series."
                },
                status=500,
            )

        url = (
            f"https://api.themoviedb.org/3/"
            f"tv/{tmdb_id}/"
            f"season/{season_number}"
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
                        "season from TMDb."
                },
                status=response.status_code,
            )

        data = response.json()

        episodes_data = data.get(
            "episodes",
            [],
        )

        season, _ = (
            TVSeason.objects
            .update_or_create(
                series=series,
                season_number=
                    season_number,
                defaults={
                    "tmdb_id":
                        data.get("id"),

                    "name":
                        data.get("name")
                        or
                        f"Season "
                        f"{season_number}",

                    "overview":
                        data.get(
                            "overview",
                            "",
                        ),

                    "air_date":
                        safe_date(
                            data.get(
                                "air_date"
                            )
                        ),

                    "poster_path":
                        data.get(
                            "poster_path"
                        )
                        or "",

                    "episode_count":
                        len(
                            episodes_data
                        ),
                },
            )
        )

        local_episodes = []

        for episode_data in episodes_data:
            episode_number = (
                episode_data.get(
                    "episode_number"
                )
            )

            if episode_number is None:
                continue

            episode, _ = (
                TVEpisode.objects
                .update_or_create(
                    season=season,
                    episode_number=
                        episode_number,
                    defaults={
                        "tmdb_id":
                            episode_data.get(
                                "id"
                            ),

                        "name":
                            episode_data.get(
                                "name"
                            )
                            or
                            f"Episode "
                            f"{episode_number}",

                        "overview":
                            episode_data.get(
                                "overview",
                                "",
                            ),

                        "air_date":
                            safe_date(
                                episode_data.get(
                                    "air_date"
                                )
                            ),

                        "runtime":
                            episode_data.get(
                                "runtime"
                            ),

                        "still_path":
                            episode_data.get(
                                "still_path"
                            )
                            or "",
                    },
                )
            )

            local_episodes.append(
                episode
            )

        watched_episode_ids = set(
            WatchedEpisode.objects.filter(
                user=request.user,
                episode__season=season,
            ).values_list(
                "episode_id",
                flat=True,
            )
        )

        episode_results = []

        for episode in local_episodes:
            episode_results.append({
                "id":
                    episode.id,

                "tmdb_id":
                    episode.tmdb_id,

                "episode_number":
                    episode
                    .episode_number,

                "name":
                    episode.name,

                "overview":
                    episode.overview,

                "air_date":
                    date_to_string(
                        episode.air_date
                    ),

                "runtime":
                    episode.runtime,

                "still_path":
                    episode.still_path,

                "watched":
                    (
                        episode.id
                        in watched_episode_ids
                    ),
            })

        watched_count = sum(
            1
            for episode
            in episode_results
            if episode["watched"]
        )

        total_count = len(
            episode_results
        )

        progress = (
            watched_count
            / total_count
            if total_count > 0
            else 0
        )

        return Response({
            "id":
                season.id,

            "tmdb_id":
                season.tmdb_id,

            "series": {
                "id":
                    series.id,

                "tmdb_id":
                    series.tmdb_id,

                "title":
                    series.title,

                "media_type":
                    "tv",
            },

            "season_number":
                season.season_number,

            "name":
                season.name,

            "overview":
                season.overview,

            "air_date":
                date_to_string(
                    season.air_date
                ),

            "poster_path":
                season.poster_path,

            "episode_count":
                total_count,

            "watched_count":
                watched_count,

            "progress":
                progress,

            "completed":
                (
                    total_count > 0
                    and
                    watched_count
                    == total_count
                ),

            "episodes":
                episode_results,
        })


class MarkEpisodeWatchedView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        episode_id,
    ):
        episode = get_object_or_404(
            TVEpisode,
            id=episode_id,
        )

        _, created = (
            WatchedEpisode.objects
            .get_or_create(
                user=request.user,
                episode=episode,
            )
        )

        return Response(
            {
                "created":
                    created,

                "watched":
                    True,

                "episode_id":
                    episode.id,
            },
            status=(
                201
                if created
                else 200
            ),
        )


class UnmarkEpisodeWatchedView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def delete(
        self,
        request,
        episode_id,
    ):
        episode = get_object_or_404(
            TVEpisode,
            id=episode_id,
        )

        WatchedEpisode.objects.filter(
            user=request.user,
            episode=episode,
        ).delete()

        return Response(
            status=204
        )


class MarkSeasonWatchedView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        season_id,
    ):
        season = get_object_or_404(
            TVSeason,
            id=season_id,
        )

        episodes = (
            TVEpisode.objects
            .filter(
                season=season
            )
        )

        created_count = 0

        for episode in episodes:
            _, created = (
                WatchedEpisode.objects
                .get_or_create(
                    user=request.user,
                    episode=episode,
                )
            )

            if created:
                created_count += 1

        return Response({
            "watched": True,

            "season_id":
                season.id,

            "episode_count":
                episodes.count(),

            "newly_marked":
                created_count,
        })


class UnmarkSeasonWatchedView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def delete(
        self,
        request,
        season_id,
    ):
        season = get_object_or_404(
            TVSeason,
            id=season_id,
        )

        deleted_count, _ = (
            WatchedEpisode.objects
            .filter(
                user=request.user,
                episode__season=season,
            )
            .delete()
        )

        return Response({
            "watched":
                False,

            "season_id":
                season.id,

            "removed_count":
                deleted_count,
        })


# ==========================================================
# GLOBAL SERIES PROGRESS
#
# Bitna razlika:
# total episode count uzimamo iz TMDb-a,
# tako da ne moraš prije otvoriti sve sezone.
# ==========================================================

class SeriesProgressView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        tmdb_id,
    ):
        series = ensure_local_series(
            tmdb_id
        )

        if series is None:
            return Response(
                {
                    "error":
                        "Could not load series."
                },
                status=500,
            )

        url = (
            f"https://api.themoviedb.org/3/"
            f"tv/{tmdb_id}"
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
                        "series progress data."
                },
                status=response.status_code,
            )

        data = response.json()

        tmdb_seasons = (
            data.get(
                "seasons",
                [],
            )
        )

        season_results = []

        total_episodes = 0
        watched_episodes = 0

        for tmdb_season in tmdb_seasons:
            season_number = (
                tmdb_season.get(
                    "season_number"
                )
            )

            # Specials / Season 0 zasad
            # ne računamo u glavni progress.
            if (
                season_number is None
                or
                season_number <= 0
            ):
                continue

            episode_count = (
                tmdb_season.get(
                    "episode_count"
                )
                or 0
            )

            total_episodes += (
                episode_count
            )

            local_season = (
                TVSeason.objects
                .filter(
                    series=series,
                    season_number=
                        season_number,
                )
                .first()
            )

            watched_count = 0

            if local_season:
                watched_count = (
                    WatchedEpisode.objects
                    .filter(
                        user=request.user,
                        episode__season=
                            local_season,
                    )
                    .count()
                )

            watched_episodes += (
                watched_count
            )

            season_progress = (
                watched_count
                / episode_count
                if episode_count > 0
                else 0
            )

            season_results.append({
                "season_number":
                    season_number,

                "name":
                    tmdb_season.get(
                        "name"
                    )
                    or
                    f"Season "
                    f"{season_number}",

                "poster_path":
                    tmdb_season.get(
                        "poster_path"
                    ),

                "air_date":
                    tmdb_season.get(
                        "air_date"
                    ),

                "episode_count":
                    episode_count,

                "watched_count":
                    watched_count,

                "progress":
                    season_progress,

                "completed":
                    (
                        episode_count > 0
                        and
                        watched_count
                        == episode_count
                    ),
            })

        # TMDb number_of_episodes obično
        # uključuje regularne epizode.
        # Mi ipak koristimo sumu sezona bez
        # season 0 da odgovara UI-u.
        progress = (
            watched_episodes
            / total_episodes
            if total_episodes > 0
            else 0
        )

        next_season = None

        next_episode_number = None

        # Pokušaj pronaći prvu sezonu
        # koja nije dovršena.
        for season_data in season_results:
            if not season_data[
                "completed"
            ]:
                next_season = (
                    season_data[
                        "season_number"
                    ]
                )

                local_season = (
                    TVSeason.objects
                    .filter(
                        series=series,
                        season_number=
                            next_season,
                    )
                    .first()
                )

                # Ako je sezona već bila
                # otvorena i epizode su lokalno
                # spremljene, možemo naći
                # točnu sljedeću epizodu.
                if local_season:
                    watched_ids = set(
                        WatchedEpisode.objects
                        .filter(
                            user=request.user,
                            episode__season=
                                local_season,
                        )
                        .values_list(
                            "episode_id",
                            flat=True,
                        )
                    )

                    first_unwatched = (
                        TVEpisode.objects
                        .filter(
                            season=
                                local_season
                        )
                        .exclude(
                            id__in=
                                watched_ids
                        )
                        .order_by(
                            "episode_number"
                        )
                        .first()
                    )

                    if first_unwatched:
                        next_episode_number = (
                            first_unwatched
                            .episode_number
                        )

                break

        return Response({
            "tmdb_id":
                series.tmdb_id,

            "title":
                series.title,

            "watched_episodes":
                watched_episodes,

            "total_episodes":
                total_episodes,

            "progress":
                progress,

            "completed":
                (
                    total_episodes > 0
                    and
                    watched_episodes
                    == total_episodes
                ),

            "next_season":
                next_season,

            "next_episode":
                next_episode_number,

            "seasons":
                season_results,
        })