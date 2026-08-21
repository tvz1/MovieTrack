from django.urls import path

from .views import (
    MovieListView,
    MovieDetailView,
    MovieSearchView,
    MovieImportView,
    MarkWatchedView,
    WatchedMovieListView,
    UnmarkWatchedView,
    WatchlistView,
    RemoveFromWatchlistView,
    FavoriteView,
    RemoveFavoriteView,
    RegisterView,
    MeView,
    MovieFullDetailView,
    ProfileView,
    MovieFilterOptionsView,
)

from .catalog_views import (
    MovieCatalogView,
)

from .person_views import (
    PersonMoviesView,
)

from .recommendation_views import (
    MovieRecommendationsView,
)

from .episode_views import (
    TVSeasonDetailView,
    MarkEpisodeWatchedView,
    UnmarkEpisodeWatchedView,
    MarkSeasonWatchedView,
    UnmarkSeasonWatchedView,
    SeriesProgressView,
)


urlpatterns = [
    path("", MovieListView.as_view(), name="movie-list"),
    path("catalog/", MovieCatalogView.as_view(), name="movie-catalog"),
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path(
        "filter-options/",
        MovieFilterOptionsView.as_view(),
        name="movie-filter-options",
    ),
    path("search/", MovieSearchView.as_view(), name="media-search"),

    path("watched/", WatchedMovieListView.as_view(), name="watched-list"),
    path(
        "<int:movie_id>/watched/",
        MarkWatchedView.as_view(),
        name="media-watched",
    ),
    path(
        "<int:movie_id>/watched/remove/",
        UnmarkWatchedView.as_view(),
        name="media-unwatched",
    ),

    path("watchlist/", WatchlistView.as_view(), name="watchlist"),
    path(
        "<int:movie_id>/watchlist/",
        WatchlistView.as_view(),
        name="watchlist-add",
    ),
    path(
        "<int:movie_id>/watchlist/remove/",
        RemoveFromWatchlistView.as_view(),
        name="watchlist-remove",
    ),

    path("favorites/", FavoriteView.as_view(), name="favorites"),
    path(
        "<int:movie_id>/favorite/",
        FavoriteView.as_view(),
        name="favorite-add",
    ),
    path(
        "<int:movie_id>/favorite/remove/",
        RemoveFavoriteView.as_view(),
        name="favorite-remove",
    ),

    path(
        "import/<str:media_type>/<int:tmdb_id>/",
        MovieImportView.as_view(),
        name="media-import",
    ),
    path(
        "import/<int:tmdb_id>/",
        MovieImportView.as_view(),
        name="movie-import-old",
    ),

    path(
        "tv/<int:tmdb_id>/season/<int:season_number>/",
        TVSeasonDetailView.as_view(),
        name="tv-season-detail",
    ),
    path(
        "episodes/<int:episode_id>/watched/",
        MarkEpisodeWatchedView.as_view(),
        name="episode-watched",
    ),
    path(
        "episodes/<int:episode_id>/watched/remove/",
        UnmarkEpisodeWatchedView.as_view(),
        name="episode-unwatched",
    ),
    path(
        "seasons/<int:season_id>/watched/",
        MarkSeasonWatchedView.as_view(),
        name="season-watched",
    ),
    path(
        "seasons/<int:season_id>/watched/remove/",
        UnmarkSeasonWatchedView.as_view(),
        name="season-unwatched",
    ),
    path(
        "tv/<int:tmdb_id>/progress/",
        SeriesProgressView.as_view(),
        name="series-progress",
    ),

    path(
        "tmdb/<str:media_type>/<int:tmdb_id>/",
        MovieFullDetailView.as_view(),
        name="media-full-detail",
    ),
    path(
        "tmdb/<int:tmdb_id>/",
        MovieFullDetailView.as_view(),
        name="movie-full-detail-old",
    ),

    path(
        "tmdb/<str:media_type>/<int:tmdb_id>/recommendations/",
        MovieRecommendationsView.as_view(),
        name="media-recommendations",
    ),
    path(
        "tmdb/<int:tmdb_id>/recommendations/",
        MovieRecommendationsView.as_view(),
        name="movie-recommendations-old",
    ),

    path(
        "person/<int:person_id>/",
        PersonMoviesView.as_view(),
        name="person-media",
    ),

    path(
        "<int:pk>/",
        MovieDetailView.as_view(),
        name="movie-detail",
    ),
]