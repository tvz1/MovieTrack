from django.db import models
from django.contrib.auth.models import User 

class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    release_date = models.DateField(null = True, blank = True)
    overview = models.TextField(blank=True)
    poster_path = models.CharField(max_length=500, blank = True)
    runtime = models.PositiveIntegerField(null = True, blank = True)

    def __str__(self):
        return self.title


class WatchedMovie(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="watched_movies")
    movie = models.ForeignKey(Movie,on_delete=models.CASCADE,related_name="watched_by")

    watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user","movie"],
                name="unique_user_watched_movie"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"

class WatchlistMovie(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="watchlist_movies")

    movie = models.ForeignKey(Movie,on_delete=models.CASCADE,related_name="watchlisted_by") 

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "movie"],
                name="unique_user_watchlist_movie"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"


class FavoriteMovie(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="favorite_movies")

    movie = models.ForeignKey(Movie,on_delete=models.CASCADE,related_name="favorited_by")

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user","movie"],
                name="unique_user_favorite_movie"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"

    

     

