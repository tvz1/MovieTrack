from django.contrib import admin
from .models import Movie, WatchedMovie, WatchlistMovie, FavoriteMovie

admin.site.register(Movie)
admin.site.register(WatchedMovie)
admin.site.register(WatchlistMovie)
admin.site.register(FavoriteMovie)



