from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    path('crop-recommendation/', views.home, name='crop_recommendation'),

    # Quick Links
    path('about/', views.about, name='about'),
    path('solutions/', views.solutions, name='solutions'),
    path('pricing/', views.pricing, name='pricing'),
    path('case-studies/', views.case_studies, name='case_studies'),

    # Resources
    path('documentation/', views.documentation, name='documentation'),
    path('api-reference/', views.api_reference, name='api_reference'),
    path('blog/', views.blog, name='blog'),
    path('help-center/', views.help_center, name='help_center'),
    path('community/', views.community, name='community'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('password-reset/', views.password_reset_view, name='password_reset'),

    # Features
    path('market-insights/', views.market_insights, name='market_insights'),
    path('disease-diagnosis/', views.disease_diagnosis, name='disease_diagnosis'),

]