from django.urls import path
from .views import MovieListView, MovieDetailView, MovieSearchView, MovieImportView, MarkWatchedView, WatchedMovieListView,UnmarkWatchedView, RegisterView,MeView,WatchlistView,RemoveFromWatchlistView,FavoriteView,RemoveFavoriteView

urlpatterns = [
    path("", MovieListView.as_view(), name= "movie-list"),
    path("register/",RegisterView.as_view(),name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("search/", MovieSearchView.as_view(), name="movie-search"),
    path("watched/",WatchedMovieListView.as_view(), name="watched-list"),
    path("import/<int:tmdb_id>/", MovieImportView.as_view(),name="movie-import"),
    path("<int:movie_id>/watched/",MarkWatchedView.as_view(),name="movie-watched"),
    path("<int:movie_id>/watched/remove/", UnmarkWatchedView.as_view(), name="movie-unwatched"),
    path("<int:pk>/", MovieDetailView.as_view(), name="movie-detail"),

    path("watchlist/", WatchlistView.as_view(), name="watchlist"),
    path("<int:movie_id>/watchlist/",WatchlistView.as_view(), name="watchlist-add"),
    path("<int:movie_id>/watchlist/remove/",RemoveFromWatchlistView.as_view(),name="watchlist-remove"),

    path("favorites/",FavoriteView.as_view(),name="favorites"),
    path("<int:movie_id>/favorite/", FavoriteView.as_view(),name="favorite-add"),
    path("<int:movie_id>/favorite/remove/", RemoveFavoriteView.as_view(),name="favorite-remove"),

    

]

#int:pk , znaci ocekuj cijeli broj u Url-u i proslijedi ga viewu kao pk, primary key
