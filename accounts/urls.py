from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),  # Giriş yapmayanlar için landing
    path('home/', views.home, name='home'),  # Giriş yapmış kullanıcılar için ana sayfa
    path('lost/', views.list_lost_posts, name='lost_posts'),
    path('found/', views.list_found_posts, name='found_posts'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('create-lost-item/', views.create_lost_item_post, name='create_lost_item'),
    path('create-found-item/', views.create_found_item_post, name='create_found_item'),
    path('create-post/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
]
