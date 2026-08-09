from django.db import models

class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    release_date = models.DateField(null = True, blank = True)
    overview = models.TextField(blank=True)
    poster_path = models.CharField(max_length=500, blank = True)
    runtime = models.PositiveIntegerField(null = True, blank = True)

    def __str__(self):
        return self.title

