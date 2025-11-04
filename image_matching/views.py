from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
import json
import os
from .services import ImageMatchingService
from .models import ImageVector, ImageMatch, ImageProcessingJob


class ImageMatchingAPIView(View):
    """Görüntü eşleştirme API"""
    
    def __init__(self):
        self.matching_service = ImageMatchingService()
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Görüntü yükle ve işle"""
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            # Görüntü dosyasını al
            if 'image' not in request.FILES:
                return JsonResponse({'error': 'No image file provided'}, status=400)
            
            image_file = request.FILES['image']
            description = request.POST.get('description', '')
            
            # Geçici dosya olarak kaydet
            temp_dir = settings.MEDIA_ROOT / 'temp'
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, image_file.name)
            
            with open(temp_path, 'wb') as f:
                for chunk in image_file.chunks():
                    f.write(chunk)
            
            # Görüntüyü işle
            result = self.matching_service.process_image(
                image_path=temp_path,
                user_id=str(request.user.id),
                description=description
            )
            
            if result['success']:
                # İşleme işi kaydı oluştur
                job = ImageProcessingJob.objects.create(
                    user=request.user,
                    image_path=temp_path,
                    status='completed'
                )
                
                return JsonResponse({
                    'success': True,
                    'vector_id': result['vector_id'],
                    'job_id': str(job.id),
                    'message': 'Image processed successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def get(self, request):
        """Benzer görüntüleri ara"""
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            image_path = request.GET.get('image_path')
            top_k = int(request.GET.get('top_k', 10))
            
            if not image_path:
                return JsonResponse({'error': 'image_path parameter required'}, status=400)
            
            # Benzer görüntüleri bul
            matches = self.matching_service.find_similar_images(image_path, top_k)
            
            return JsonResponse({
                'success': True,
                'matches': matches,
                'total_matches': len(matches)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_and_match_image(request):
    """Görüntü yükle ve eşleştir"""
    try:
        if 'image' not in request.FILES:
            return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES['image']
        description = request.data.get('description', '')
        
        # Geçici dosya olarak kaydet
        temp_dir = settings.MEDIA_ROOT / 'temp'
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, image_file.name)
        
        with open(temp_path, 'wb') as f:
            for chunk in image_file.chunks():
                f.write(chunk)
        
        matching_service = ImageMatchingService()
        
        # Görüntüyü işle
        process_result = matching_service.process_image(
            image_path=temp_path,
            user_id=str(request.user.id),
            description=description
        )
        
        if not process_result['success']:
            return Response({
                'success': False,
                'error': process_result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Benzer görüntüleri bul ve eşleşmeleri kaydet
        matches = matching_service.find_similar_images(
            temp_path, top_k=10, source_vector_id=process_result.get('vector_id')
        )
        
        return Response({
            'success': True,
            'vector_id': process_result['vector_id'],
            'matches': matches,
            'total_matches': len(matches)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_images(request):
    """Kullanıcının görüntülerini getir"""
    try:
        images = ImageVector.objects.filter(user=request.user).order_by('-created_at')
        
        image_list = []
        for image in images:
            image_list.append({
                'id': str(image.id),
                'vector_id': image.vector_id,
                'image_path': image.image_path,
                'description': image.description,
                'location': image.location,
                'is_found': image.is_found,
                'created_at': image.created_at.isoformat()
            })
        
        return Response({
            'success': True,
            'images': image_list,
            'total_count': len(image_list)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_match(request):
    """Eşleştirmeyi doğrula"""
    try:
        match_id = request.data.get('match_id')
        is_verified = request.data.get('is_verified', False)
        
        if not match_id:
            return Response({'error': 'match_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            match = ImageMatch.objects.get(id=match_id)
            match.is_verified = is_verified
            match.verified_by = request.user
            match.save()
            
            return Response({
                'success': True,
                'message': 'Match verification updated'
            })
            
        except ImageMatch.DoesNotExist:
            return Response({'error': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
