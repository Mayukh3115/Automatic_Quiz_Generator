from django.urls import path
from django.shortcuts import render
from . import views

def quiz_page(request):
    return render(request, "quiz/quiz.html")


urlpatterns = [
    path('',quiz_page),
    path('generate_quiz/', views.generate_quiz),
]
