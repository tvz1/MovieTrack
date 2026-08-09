from rest_framework import serializers
from .models import Movie 

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = "__all__"

#serializer pretvara Django objekt iz baze podataka u JSON koji mobilna aplikacija moze koristiti
