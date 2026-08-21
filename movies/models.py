from django.db import models
from django.contrib.auth.models import User


class Movie(models.Model):
    MEDIA_TYPE_CHOICES = [
        ("movie", "Movie"),
        ("tv", "TV Series"),
    ]

    tmdb_id = models.IntegerField()

    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPE_CHOICES,
        default="movie",
    )

    title = models.CharField(
        max_length=255
    )

    release_date = models.DateField(
        null=True,
        blank=True
    )

    overview = models.TextField(
        blank=True
    )

    poster_path = models.CharField(
        max_length=500,
        blank=True
    )

    runtime = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    genres = models.JSONField(
        default=list,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "tmdb_id",
                    "media_type",
                ],
                name="unique_tmdb_media",
            )
        ]

    def __str__(self):
        return (
            f"{self.title} "
            f"({self.media_type})"
        )


class WatchedMovie(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="watched_movies",
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="watched_by",
    )

    watched_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "movie",
                ],
                name="unique_user_watched_movie",
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.movie.title}"
        )


class WatchlistMovie(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="watchlist_movies",
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="watchlisted_by",
    )

    added_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "movie",
                ],
                name="unique_user_watchlist_movie",
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.movie.title}"
        )


class FavoriteMovie(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorite_movies",
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )

    added_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "movie",
                ],
                name="unique_user_favorite_movie",
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.movie.title}"
        )


# ==========================================================
# TV SEASONS
# ==========================================================

class TVSeason(models.Model):
    series = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="seasons",
    )

    tmdb_id = models.IntegerField(
        null=True,
        blank=True,
    )

    season_number = models.PositiveIntegerField()

    name = models.CharField(
        max_length=255,
        blank=True,
    )

    overview = models.TextField(
        blank=True,
    )

    air_date = models.DateField(
        null=True,
        blank=True,
    )

    poster_path = models.CharField(
        max_length=500,
        blank=True,
    )

    episode_count = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = [
            "season_number"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "series",
                    "season_number",
                ],
                name="unique_series_season",
            )
        ]

    def __str__(self):
        return (
            f"{self.series.title} - "
            f"Season {self.season_number}"
        )


# ==========================================================
# TV EPISODES
# ==========================================================

class TVEpisode(models.Model):
    season = models.ForeignKey(
        TVSeason,
        on_delete=models.CASCADE,
        related_name="episodes",
    )

    tmdb_id = models.IntegerField(
        null=True,
        blank=True,
    )

    episode_number = models.PositiveIntegerField()

    name = models.CharField(
        max_length=255,
    )

    overview = models.TextField(
        blank=True,
    )

    air_date = models.DateField(
        null=True,
        blank=True,
    )

    runtime = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    still_path = models.CharField(
        max_length=500,
        blank=True,
    )

    class Meta:
        ordering = [
            "episode_number"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "season",
                    "episode_number",
                ],
                name="unique_season_episode",
            )
        ]

    def __str__(self):
        return (
            f"{self.season.series.title} - "
            f"S{self.season.season_number:02}"
            f"E{self.episode_number:02} - "
            f"{self.name}"
        )


# ==========================================================
# WATCHED EPISODES
# ==========================================================

class WatchedEpisode(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="watched_episodes",
    )

    episode = models.ForeignKey(
        TVEpisode,
        on_delete=models.CASCADE,
        related_name="watched_by",
    )

    watched_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "episode",
                ],
                name="unique_user_watched_episode",
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.episode}"
        )