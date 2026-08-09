from django.urls import path
from .views import MovieListView, MovieDetailView

urlpatterns = [
    path("", MovieListView.as_view(), name= "movie-list"),
    path("<int:pk>/", MovieDetailView.as_view(), name="movie-detail"),
]

#int:pk , znaci ocekuj cijeli broj u Url-u i proslijedi ga viewu kao pk, primary key
