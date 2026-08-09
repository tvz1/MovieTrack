from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .models import Movie
from .serializers import MovieSerializer

class MovieListView(ListCreateAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer


#radimo view koji vraca listu svih filmova 
#Movie.objects.all() znaci uzmi sve Movie zapise iz baze 
#serializer_class govori djangu kako te objekte pretvoriti u JSON

class MovieDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    