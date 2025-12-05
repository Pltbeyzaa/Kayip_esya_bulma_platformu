from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from django.core.files.storage import default_storage
import json
import os

from .services import ImageMatchingService
from .models import ImageVector, ImageMatch, ImageProcessingJob
from .utils import vectorize_object_clip
from .face_utils import get_face_embedding
from .milvus_connector import (
    insert_vector,
    OBJECT_COLLECTION,
    PERSON_COLLECTION,
)



class ImageMatchingAPIView(View):
    """Görüntü eşleştirme API"""
    
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
            matching_service = ImageMatchingService()
            result = matching_service.process_image(
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
            matching_service = ImageMatchingService()
            matches = matching_service.find_similar_images(image_path, top_k)
            
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


# --- GEREKLİ YARDIMCI FONKSİYONLARIN SIMÜLASYONU ---

def save_to_mysql_and_get_id(metadata: dict) -> int | None:
    """
    >>> Cursor Notu: BU FONKSİYONU GERÇEK DJANGO MODEL SAVE KOMUTUYLA DEĞİŞTİR.
    >>> Gelen metadata (Harita verileri dahil) ile yeni bir ilan objesi oluştur.
    >>> Obje kaydedildikten sonra, onun ID'sini (MySQL Primary Key) döndür.
    """
    # Burası, sizin Item/Ilan modelinizi MySQL'e kaydetmeli.
    # Örnek: Item.objects.create(**metadata).id

    # Şimdilik simüle ediyoruz:
    if "title" in metadata:
        return 12345  # Başarılı bir kayıt sonrası dönen ilan ID'si
    return None


class ImageUploadAPIView(APIView):
    """Yeni CLIP / FaceNet + Milvus tabanlı ilan yükleme API'si."""

    def post(self, request, *args, **kwargs):
        # Zorunlu alanları kontrol et
        if (
            "image" not in request.FILES
            or "location_query" not in request.data
            or "title" not in request.data
        ):
            return Response(
                {
                    "error": "Lütfen 'image', 'location_query' ve 'title' alanlarını gönderin."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        uploaded_file = request.FILES["image"]
        location_query = request.data["location_query"]

        # 1. Dosyayı Geçici Olarak Kaydet (Vektörleme için)
        try:
            file_name = default_storage.save(uploaded_file.name, uploaded_file)
            file_path = os.path.join(default_storage.location, file_name)
        except Exception as e:  # pragma: no cover - IO hataları runtime
            return Response(
                {"error": f"Dosya kaydetme hatası: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 2. Coğrafi Veriyi Çek
        # Not: Gerçek projede burası Google Maps / başka bir servisle doldurulmalı.
        # Biz şimdilik sadece sorguyu metadata'ya ekleyelim.
        maps_data = {"location_query": location_query}

        # 3. Vektör Üretimini Hazırla
        is_face, vector_to_save = get_face_embedding(file_path)  # Önce FaceNet'i dene
        collection_to_use = None
        processing_model = None

        if is_face and vector_to_save:
            collection_to_use = PERSON_COLLECTION
            processing_model = "FaceNet"
        else:
            # Yüz yoksa, CLIP ile nesne vektörünü üret
            vector_to_save = vectorize_object_clip(file_path)
            if vector_to_save:
                collection_to_use = OBJECT_COLLECTION
                processing_model = "CLIP"

        # Vektörleme başarısız olduysa
        if not vector_to_save:
            default_storage.delete(file_name)
            return Response(
                {"error": "Görsel işlenemedi: Vektör üretilemedi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. MySQL'e Kaydet ve İlan ID'sini Al (ÖNCE METADATA KAYDI!)
        metadata = {
            "title": request.data.get("title"),
            "description": request.data.get("description", ""),
            "image_path": file_path,  # İlanın kalıcı dosya yolu
            **(maps_data if maps_data else {}),  # Harita verilerini ekle
            # ... diğer ilan alanları
        }
        ilan_id = save_to_mysql_and_get_id(metadata)

        if not ilan_id:
            return Response(
                {"error": "MySQL kaydı başarısız oldu."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 5. Milvus'a Vektörü Kaydet (MySQL'den gelen gerçek ilan ID'si ile)
        milvus_success = insert_vector(collection_to_use, vector_to_save, ilan_id)

        if milvus_success:
            return Response(
                {
                    "message": "İlan başarıyla yüklendi ve işlendi.",
                    "ilan_id": ilan_id,
                    "vector_collection": collection_to_use,
                    "location_found": maps_data is not None,
                    "processing_model": processing_model,
                },
                status=status.HTTP_201_CREATED,
            )

        # Milvus hatası varsa, MySQL'den kaydı geri almayı düşünün (Rollback)
        return Response(
            {"error": "Vektör veritabanı kaydı başarısız oldu."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
