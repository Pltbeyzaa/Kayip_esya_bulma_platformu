from django.urls import path
from . import views

urlpatterns = [
    # API endpoints
    path('api/search/', views.LocationSearchAPIView.as_view(), name='location_search'),
    path('api/lost-items/create/', views.create_lost_item, name='create_lost_item'),
    path('api/found-items/create/', views.create_found_item, name='create_found_item'),
    path('api/lost-items/', views.get_lost_items, name='get_lost_items'),
    path('api/found-items/', views.get_found_items, name='get_found_items'),
    path('api/location-matches/', views.get_location_matches, name='get_location_matches'),
]
