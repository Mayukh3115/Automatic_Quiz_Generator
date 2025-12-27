from django.urls import path
from django.shortcuts import render
from . import views
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required

@ensure_csrf_cookie
@login_required
def quiz_page(request):
    return render(request, "quiz/quiz.html")


urlpatterns = [
    path('',quiz_page, name = 'home'),
    path('generate_quiz/', views.generate_quiz),
    path('download_quiz_pdf/', views.download_quiz_pdf),
    path("signup/", views.signup, name="signup"),
]
