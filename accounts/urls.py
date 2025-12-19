from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),  # Giriş yapmayanlar için landing
    path('findus/', views.findus_info, name='findus_info'),
    path('home/', views.home, name='home'),  # Giriş yapmış kullanıcılar için ana sayfa
    path('lost/', views.list_lost_posts, name='lost_posts'),
    path('found/', views.list_found_posts, name='found_posts'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('create-lost-item/', views.create_lost_item_post, name='create_lost_item'),
    path('create-found-item/', views.create_found_item_post, name='create_found_item'),
    path('create-missing-child/', views.create_missing_child_post, name='create_missing_child'),
    path('create-found-child/', views.create_found_child_post, name='create_found_child'),
    path('create-lost-animal/', views.create_lost_animal_post, name='create_lost_animal'),
    path('create-found-animal/', views.create_found_animal_post, name='create_found_animal'),
    path('create-post/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/matches/', views.show_matches, name='show_matches'),
    path('post/<int:lost_post_id>/mark-found/<int:found_post_id>/', views.mark_match_as_found, name='mark_match_as_found'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
]
