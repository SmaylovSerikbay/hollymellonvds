from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('brands/', views.brands, name='brands'),
    path('brands/<slug:slug>/', views.brand_detail, name='brand_detail'),
    path('set-city/', views.set_city, name='set_city'),
    path('photos/', views.photo_gallery, name='photo_gallery'),
    path('photos/<int:pk>/', views.album_detail, name='album_detail'),
] 