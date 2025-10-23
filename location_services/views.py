from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from .services import LocationSearchService, LocationMatchingService
from .models import Location, LostItem, FoundItem, LocationMatch


class LocationSearchAPIView(View):
    """Konum arama API"""
    
    def __init__(self):
        self.search_service = LocationSearchService()
        self.matching_service = LocationMatchingService()
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Konum tabanlı arama yap"""
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            data = json.loads(request.body)
            search_type = data.get('type')  # 'coordinates' or 'address'
            
            if search_type == 'coordinates':
                latitude = data.get('latitude')
                longitude = data.get('longitude')
                radius_km = data.get('radius_km', 5.0)
                item_type = data.get('item_type')
                
                if not latitude or not longitude:
                    return JsonResponse({'error': 'latitude and longitude required'}, status=400)
                
                result = self.search_service.search_by_location(
                    latitude, longitude, radius_km, item_type
                )
                
            elif search_type == 'address':
                address = data.get('address')
                radius_km = data.get('radius_km', 5.0)
                item_type = data.get('item_type')
                
                if not address:
                    return JsonResponse({'error': 'address required'}, status=400)
                
                result = self.search_service.search_by_address(
                    address, radius_km, item_type
                )
                
            else:
                return JsonResponse({'error': 'Invalid search type'}, status=400)
            
            return JsonResponse({
                'success': True,
                'results': result
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_lost_item(request):
    """Kayıp eşya ilanı oluştur"""
    try:
        data = request.data
        
        # Konum bilgilerini al
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        location_name = data.get('location_name', 'Unknown Location')
        
        if not latitude or not longitude:
            return Response({'error': 'latitude and longitude required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Konum oluştur
        matching_service = LocationMatchingService()
        location = matching_service.create_location_from_coordinates(
            latitude=float(latitude),
            longitude=float(longitude),
            name=location_name,
            user_id=str(request.user.id)
        )
        
        if not location:
            return Response({'error': 'Failed to create location'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Kayıp eşya ilanı oluştur
        lost_item = LostItem.objects.create(
            user=request.user,
            title=data.get('title'),
            description=data.get('description'),
            item_type=data.get('item_type'),
            location=location,
            lost_date=data.get('lost_date'),
            reward_amount=data.get('reward_amount'),
            contact_phone=data.get('contact_phone'),
            contact_email=data.get('contact_email')
        )
        
        # Potansiyel eşleştirmeleri ara
        matches = matching_service.find_potential_matches(str(lost_item.id))
        
        return Response({
            'success': True,
            'lost_item': {
                'id': str(lost_item.id),
                'title': lost_item.title,
                'description': lost_item.description,
                'item_type': lost_item.item_type,
                'location': {
                    'name': location.name,
                    'latitude': float(location.latitude),
                    'longitude': float(location.longitude),
                    'address': location.address
                },
                'created_at': lost_item.created_at.isoformat()
            },
            'potential_matches': len(matches)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_found_item(request):
    """Bulunan eşya ilanı oluştur"""
    try:
        data = request.data
        
        # Konum bilgilerini al
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        location_name = data.get('location_name', 'Unknown Location')
        
        if not latitude or not longitude:
            return Response({'error': 'latitude and longitude required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Konum oluştur
        matching_service = LocationMatchingService()
        location = matching_service.create_location_from_coordinates(
            latitude=float(latitude),
            longitude=float(longitude),
            name=location_name,
            user_id=str(request.user.id)
        )
        
        if not location:
            return Response({'error': 'Failed to create location'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Bulunan eşya ilanı oluştur
        found_item = FoundItem.objects.create(
            user=request.user,
            title=data.get('title'),
            description=data.get('description'),
            item_type=data.get('item_type'),
            location=location,
            found_date=data.get('found_date'),
            contact_phone=data.get('contact_phone'),
            contact_email=data.get('contact_email')
        )
        
        return Response({
            'success': True,
            'found_item': {
                'id': str(found_item.id),
                'title': found_item.title,
                'description': found_item.description,
                'item_type': found_item.item_type,
                'location': {
                    'name': location.name,
                    'latitude': float(location.latitude),
                    'longitude': float(location.longitude),
                    'address': location.address
                },
                'created_at': found_item.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lost_items(request):
    """Kayıp eşya ilanlarını getir"""
    try:
        # Filtreleme parametreleri
        item_type = request.GET.get('item_type')
        status_filter = request.GET.get('status', 'active')
        user_only = request.GET.get('user_only', 'false').lower() == 'true'
        
        # Sorgu oluştur
        lost_items = LostItem.objects.all()
        
        if user_only:
            lost_items = lost_items.filter(user=request.user)
        
        if item_type:
            lost_items = lost_items.filter(item_type__icontains=item_type)
        
        if status_filter:
            lost_items = lost_items.filter(status=status_filter)
        
        lost_items = lost_items.order_by('-created_at')
        
        # Sonuçları formatla
        items_list = []
        for item in lost_items:
            items_list.append({
                'id': str(item.id),
                'title': item.title,
                'description': item.description,
                'item_type': item.item_type,
                'status': item.status,
                'location': {
                    'name': item.location.name,
                    'latitude': float(item.location.latitude),
                    'longitude': float(item.location.longitude),
                    'address': item.location.address
                },
                'user': {
                    'id': str(item.user.id),
                    'username': item.user.username,
                    'first_name': item.user.first_name
                },
                'lost_date': item.lost_date.isoformat(),
                'reward_amount': float(item.reward_amount) if item.reward_amount else None,
                'created_at': item.created_at.isoformat()
            })
        
        return Response({
            'success': True,
            'items': items_list,
            'total_count': len(items_list)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_found_items(request):
    """Bulunan eşya ilanlarını getir"""
    try:
        # Filtreleme parametreleri
        item_type = request.GET.get('item_type')
        status_filter = request.GET.get('status', 'active')
        user_only = request.GET.get('user_only', 'false').lower() == 'true'
        
        # Sorgu oluştur
        found_items = FoundItem.objects.all()
        
        if user_only:
            found_items = found_items.filter(user=request.user)
        
        if item_type:
            found_items = found_items.filter(item_type__icontains=item_type)
        
        if status_filter:
            found_items = found_items.filter(status=status_filter)
        
        found_items = found_items.order_by('-created_at')
        
        # Sonuçları formatla
        items_list = []
        for item in found_items:
            items_list.append({
                'id': str(item.id),
                'title': item.title,
                'description': item.description,
                'item_type': item.item_type,
                'status': item.status,
                'location': {
                    'name': item.location.name,
                    'latitude': float(item.location.latitude),
                    'longitude': float(item.location.longitude),
                    'address': item.location.address
                },
                'user': {
                    'id': str(item.user.id),
                    'username': item.user.username,
                    'first_name': item.user.first_name
                },
                'found_date': item.found_date.isoformat(),
                'created_at': item.created_at.isoformat()
            })
        
        return Response({
            'success': True,
            'items': items_list,
            'total_count': len(items_list)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_location_matches(request):
    """Konum tabanlı eşleştirmeleri getir"""
    try:
        item_id = request.GET.get('item_id')
        item_type = request.GET.get('item_type')  # 'lost' or 'found'
        
        if not item_id or not item_type:
            return Response({'error': 'item_id and item_type required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if item_type == 'lost':
            matches = LocationMatch.objects.filter(lost_item_id=item_id)
        else:
            matches = LocationMatch.objects.filter(found_item_id=item_id)
        
        matches = matches.order_by('-match_score')
        
        matches_list = []
        for match in matches:
            matches_list.append({
                'id': str(match.id),
                'distance_km': match.distance_km,
                'match_score': match.match_score,
                'is_verified': match.is_verified,
                'lost_item': {
                    'id': str(match.lost_item.id),
                    'title': match.lost_item.title,
                    'item_type': match.lost_item.item_type
                },
                'found_item': {
                    'id': str(match.found_item.id),
                    'title': match.found_item.title,
                    'item_type': match.found_item.item_type
                },
                'created_at': match.created_at.isoformat()
            })
        
        return Response({
            'success': True,
            'matches': matches_list,
            'total_count': len(matches_list)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
