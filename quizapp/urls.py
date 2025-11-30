from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # empty path for homepage

    path('upload/', views.upload_file, name='upload_file'),
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('history/', views.quiz_history, name='quiz_history'),
 path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path("download-pdf/", views.download_quiz_pdf, name="download_quiz_pdf"),
path('download-quiz-details-pdf/', views.download_quiz_details_pdf, name='download_quiz_details_pdf'),

]
