from rest_framework import serializers
from .models import Movie, WatchedMovie, WatchlistMovie, FavoriteMovie
from django.contrib.auth.models import User

class MovieSerializer(serializers.ModelSerializer):
    watched = serializers.SerializerMethodField()
    in_watchlist = serializers.SerializerMethodField()
    favorite = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            "id",
            "tmdb_id",
            "title",
            "release_date",
            "overview",
            "poster_path",
            "runtime",
            "genres",
            "watched",
            "in_watchlist",
            "favorite",
            
        ]

    def get_watched(self, obj):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        return WatchedMovie.objects.filter(
            user=request.user,
            movie=obj
        ).exists()

    def get_in_watchlist(self, obj):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        return WatchlistMovie.objects.filter(
            user = request.user,
            movie = obj
        ).exists()

    def get_favorite(self, obj):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        return FavoriteMovie.objects.filter(
            user = request.user,
            movie=obj
        ).exists()
    
    



#serializer pretvara Django objekt iz baze podataka u JSON koji mobilna aplikacija moze koristiti

class WatchedMovieSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only = True)

    class Meta:
        model = WatchedMovie
        fields = ["id", "movie", "watched_at"]

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only = True)

    class Meta:
        model = User
        fields = ["username","email","password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username = validated_data["username"],
            email = validated_data.get("email", ""),
            password = validated_data["password"]
        )

        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class WatchlistMovieSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only = True)

    class Meta:
        model = WatchlistMovie
        fields = ["id", "movie", "added_at"]

class FavoriteMovieSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = FavoriteMovie
        fields = ["id", "movie", "added_at"]
        

