from django.shortcuts import render, get_object_or_404
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView
from .models import Movie, WatchedMovie, WatchlistMovie, FavoriteMovie
from .serializers import MovieSerializer, WatchedMovieSerializer, WatchlistMovieSerializer, FavoriteMovieSerializer, RegisterSerializer, UserSerializer

import requests

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


class MovieListView(ListCreateAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer


#radimo view koji vraca listu svih filmova 
#Movie.objects.all() znaci uzmi sve Movie zapise iz baze 
#serializer_class govori djangu kako te objekte pretvoriti u JSON

class MovieDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer


class MovieSearchView(APIView):
    def get(self, request):
        query = request.query_params.get("query")

        if not query:
            return Response(
                {"error": "Query parameter is required."},
                status=400
            )

        url = "https://api.themoviedb.org/3/search/movie"

        headers = {
            "Authorization": f"Bearer {settings.TMDB_ACCESS_TOKEN}",
            "accept": "application/json",
        }

        params = {
            "query": query,
            "include_adult": False,
            "language": "en-US",
            "page": 1,
        }

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )

        data = response.json()
        results = data.get("results", [])

        if request.user.is_authenticated:
            watched_tmdb_ids = set(
                WatchedMovie.objects.filter(
                    user=request.user
                ).values_list(
                    "movie__tmdb_id",
                    flat=True
                )
            )
        else:
            watched_tmdb_ids = set()

        if request.user.is_authenticated:
            watched_tmdb_ids = set(
                WatchedMovie.objects.filter(
                    user=request.user
                ).values_list(
                    "movie__tmdb_id",
                    flat=True
                )
            )

            watchlist_tmdb_ids = set(
                WatchlistMovie.objects.filter(
                    user=request.user
                ).values_list(
                    "movie__tmdb_id",
                    flat=True
                )
            )

            favorite_tmdb_ids = set(
                FavoriteMovie.objects.filter(
                    user = request.user
                ).values_list(
                    "movie__tmdb_id",
                    flat=True
                )
            )
        else:
            watched_tmdb_ids = set()
            watchlist_tmdb_ids = set()
            favorite_tmdb_ids = set()

        for movie in results:
            movie["watched"] = movie["id"] in watched_tmdb_ids
            movie["in_watchlist"] = movie["id"] in watchlist_tmdb_ids
            movie["favorite"] = movie["id"] in favorite_tmdb_ids

        return Response(
            data,
            status=response.status_code
        )


class MovieImportView(APIView):
    def post(self, request, tmdb_id):
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"


        headers = {
            "Authorization": f"Bearer {settings.TMDB_ACCESS_TOKEN}",
            "accept": "application/json",
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            return Response(
                {"error": "Movie could not be fetched from TMDb."},
                status=response.status_code
            )

        data = response.json()

        movie, created = Movie.objects.get_or_create(
            tmdb_id=data["id"],
            defaults={
                "title": data["title"],
                "release_date": data.get("release date") or None,
                "overview": data.get("overview", ""),
                "poster_path": data.get("poster_path") or "",
                "runtime": data.get("runtime"),
            }
        )

        serializer = MovieSerializer(movie)

        return Response(
            {
                "created": created,
                "movie": serializer.data
            },
            status=201 if created else 200
        )

class MarkWatchedView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)

        watched_movie, created = WatchedMovie.objects.get_or_create(
            user = request.user,
            movie = movie
        )

        serializer = WatchedMovieSerializer(watched_movie)

        return Response(
            {
                "created": created,
                "watched":serializer.data
            },
            status=201 if created else 200
        )

class WatchedMovieListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        watched_movies = WatchedMovie.objects.filter(user=request.user).select_related("movie")

        serializer = WatchedMovieSerializer(watched_movies, many=True)

        return Response(serializer.data)

class UnmarkWatchedView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, movie_id):
        watched_movie = get_object_or_404(WatchedMovie, user = request.user,movie_id = movie_id)

        watched_movie.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class WatchlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = WatchlistMovie.objects.filter(
            user=request.user
        ).select_related("movie")

        serializer = WatchlistMovieSerializer(
            items,
            many = True,
            context = {"request": request}
        )

        return Response(serializer.data)

    def post(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)

        item, created = WatchlistMovie.objects.get_or_create(
            user = request.user,
            movie = movie
        )

        serializer = WatchlistMovieSerializer(
            item,
            context = {"request": request}
        )

        return Response(
            {
                "created": created,
                "watchlist": serializer.data
            },
            status=201 if created else 200
        )

class RemoveFromWatchlistView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, movie_id):
        item = get_object_or_404(
            WatchlistMovie,
            user = request.user,
            movie_id = movie_id
        )

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = FavoriteMovie.objects.filter(
            user = request.user
        ).select_related("movie")

        serializer = FavoriteMovieSerializer(
            items,
            many = True,
            context = {"request": request}
        )

        return Response(serializer.data)

    def post(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)

        item, created = FavoriteMovie.objects.get_or_create(
            user = request.user,
            movie = movie
        )

        serializer = FavoriteMovieSerializer(
            item,
            context={"request": request}
        )

        return Response(
            {
                "created": created,
                "favorite": serializer.data
            },
            status=201 if created else 200
        )

class RemoveFavoriteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, movie_id):
        item = get_object_or_404(
            FavoriteMovie,
            user=request.user,
            movie_id=movie_id
        )

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
    