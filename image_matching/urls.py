from django.urls import path
from . import views

urlpatterns = [
    # API endpoints
    path('api/upload/', views.ImageMatchingAPIView.as_view(), name='image_upload'),
    path('api/upload-and-match/', views.upload_and_match_image, name='upload_and_match'),
    path('api/user-images/', views.get_user_images, name='user_images'),
    path('api/verify-match/', views.verify_match, name='verify_match'),
]
