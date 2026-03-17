from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('upload/', views.upload_text, name='upload'),
    path('contact/', views.contact, name='contact'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]