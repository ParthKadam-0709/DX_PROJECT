from . import views
from django.urls import path,include

urlpatterns = [
    
    path('base/', views.base, name='base'),
    path('home/', views.home, name='home'),
    path('header/', views.header, name='header'),
    path('footer/', views.footer, name='footer'),
    
]