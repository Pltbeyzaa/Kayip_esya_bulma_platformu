"""
Konum tabanlı servisler
"""
import math
import googlemaps
from typing import List, Tuple, Dict, Optional
from django.conf import settings
from .models import Location, LostItem, FoundItem, LocationMatch, SearchRadius


class GoogleMapsService:
    """Google Maps API servisi"""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.client = None
        if self.api_key:
            self.client = googlemaps.Client(key=self.api_key)
    
    def geocode_address(self, address: str) -> Optional[Dict]:
        """Adresi koordinatlara çevir"""
        if not self.client:
            return None
            
        try:
            geocode_result = self.client.geocode(address)
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                return {
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'formatted_address': geocode_result[0]['formatted_address'],
                    'place_id': geocode_result[0]['place_id']
                }
        except Exception as e:
            print(f"Geocoding error: {e}")
        return None
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Koordinatları adrese çevir"""
        if not self.client:
            return None
            
        try:
            reverse_geocode_result = self.client.reverse_geocode((latitude, longitude))
            if reverse_geocode_result:
                return {
                    'formatted_address': reverse_geocode_result[0]['formatted_address'],
                    'place_id': reverse_geocode_result[0]['place_id'],
                    'address_components': reverse_geocode_result[0]['address_components']
                }
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
        return None
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """İki nokta arasındaki mesafeyi hesapla (km)"""
        if not self.client:
            # Haversine formülü ile hesapla
            return self._haversine_distance(lat1, lon1, lat2, lon2)
        
        try:
            # Google Maps Distance Matrix API kullan
            result = self.client.distance_matrix(
                origins=[(lat1, lon1)],
                destinations=[(lat2, lon2)],
                mode="driving",
                units="metric"
            )
            
            if result['rows'][0]['elements'][0]['status'] == 'OK':
                distance_km = result['rows'][0]['elements'][0]['distance']['value'] / 1000
                return distance_km
            else:
                # Fallback to Haversine
                return self._haversine_distance(lat1, lon1, lat2, lon2)
        except Exception as e:
            print(f"Distance calculation error: {e}")
            return self._haversine_distance(lat1, lon1, lat2, lon2)
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine formülü ile mesafe hesapla"""
        R = 6371  # Dünya'nın yarıçapı (km)
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def get_nearby_places(self, latitude: float, longitude: float, 
                         radius: float = 1000, place_type: str = None) -> List[Dict]:
        """Yakındaki yerleri bul"""
        if not self.client:
            return []
            
        try:
            places_result = self.client.places_nearby(
                location=(latitude, longitude),
                radius=radius,
                type=place_type
            )
            
            places = []
            for place in places_result.get('results', []):
                places.append({
                    'name': place.get('name'),
                    'place_id': place.get('place_id'),
                    'rating': place.get('rating'),
                    'vicinity': place.get('vicinity'),
                    'types': place.get('types', [])
                })
            
            return places
        except Exception as e:
            print(f"Nearby places error: {e}")
            return []


class LocationMatchingService:
    """Konum tabanlı eşleştirme servisi"""
    
    def __init__(self):
        self.maps = GoogleMapsService()
    
    def find_nearby_lost_items(self, latitude: float, longitude: float, 
                              radius_km: float = 5.0, item_type: str = None) -> List[Dict]:
        """Yakındaki kayıp eşyaları bul"""
        try:
            # Tüm kayıp eşyaları al
            lost_items = LostItem.objects.filter(status='active')
            
            if item_type:
                lost_items = lost_items.filter(item_type__icontains=item_type)
            
            nearby_items = []
            for item in lost_items:
                distance = self.maps.calculate_distance(
                    latitude, longitude,
                    float(item.location.latitude), float(item.location.longitude)
                )
                
                if distance <= radius_km:
                    nearby_items.append({
                        'item': item,
                        'distance_km': round(distance, 2),
                        'match_score': self._calculate_match_score(distance, radius_km)
                    })
            
            # Mesafeye göre sırala
            nearby_items.sort(key=lambda x: x['distance_km'])
            return nearby_items
            
        except Exception as e:
            print(f"Nearby lost items search error: {e}")
            return []
    
    def find_nearby_found_items(self, latitude: float, longitude: float, 
                               radius_km: float = 5.0, item_type: str = None) -> List[Dict]:
        """Yakındaki bulunan eşyaları bul"""
        try:
            # Tüm bulunan eşyaları al
            found_items = FoundItem.objects.filter(status='active')
            
            if item_type:
                found_items = found_items.filter(item_type__icontains=item_type)
            
            nearby_items = []
            for item in found_items:
                distance = self.maps.calculate_distance(
                    latitude, longitude,
                    float(item.location.latitude), float(item.location.longitude)
                )
                
                if distance <= radius_km:
                    nearby_items.append({
                        'item': item,
                        'distance_km': round(distance, 2),
                        'match_score': self._calculate_match_score(distance, radius_km)
                    })
            
            # Mesafeye göre sırala
            nearby_items.sort(key=lambda x: x['distance_km'])
            return nearby_items
            
        except Exception as e:
            print(f"Nearby found items search error: {e}")
            return []
    
    def find_potential_matches(self, lost_item_id: str, max_distance_km: float = 10.0) -> List[Dict]:
        """Kayıp eşya için potansiyel eşleştirmeleri bul"""
        try:
            lost_item = LostItem.objects.get(id=lost_item_id)
            
            # Aynı türdeki bulunan eşyaları ara
            found_items = FoundItem.objects.filter(
                status='active',
                item_type__icontains=lost_item.item_type
            ).exclude(user=lost_item.user)  # Kendi eşyasını hariç tut
            
            matches = []
            for found_item in found_items:
                distance = self.maps.calculate_distance(
                    float(lost_item.location.latitude), float(lost_item.location.longitude),
                    float(found_item.location.latitude), float(found_item.location.longitude)
                )
                
                if distance <= max_distance_km:
                    match_score = self._calculate_match_score(distance, max_distance_km)
                    
                    # Eşleştirme kaydı oluştur (varsa güncelle)
                    match, created = LocationMatch.objects.get_or_create(
                        lost_item=lost_item,
                        found_item=found_item,
                        defaults={
                            'distance_km': distance,
                            'match_score': match_score
                        }
                    )
                    
                    if not created:
                        match.distance_km = distance
                        match.match_score = match_score
                        match.save()
                    
                    matches.append({
                        'match': match,
                        'found_item': found_item,
                        'distance_km': round(distance, 2),
                        'match_score': match_score
                    })
            
            # Eşleşme puanına göre sırala
            matches.sort(key=lambda x: x['match_score'], reverse=True)
            return matches
            
        except Exception as e:
            print(f"Potential matches search error: {e}")
            return []
    
    def _calculate_match_score(self, distance_km: float, max_distance_km: float) -> float:
        """Eşleşme puanını hesapla (0-1 arası)"""
        if distance_km <= 0:
            return 1.0
        elif distance_km >= max_distance_km:
            return 0.0
        else:
            # Mesafe arttıkça puan azalır
            return 1.0 - (distance_km / max_distance_km)
    
    def create_location_from_coordinates(self, latitude: float, longitude: float, 
                                       name: str, user_id: str) -> Optional[Location]:
        """Koordinatlardan konum oluştur"""
        try:
            # Reverse geocoding ile adres bilgisi al
            address_info = self.maps.reverse_geocode(latitude, longitude)
            
            location = Location.objects.create(
                user_id=user_id,
                name=name,
                latitude=latitude,
                longitude=longitude,
                address=address_info.get('formatted_address', '') if address_info else '',
                city=self._extract_city_from_address(address_info) if address_info else '',
                district=self._extract_district_from_address(address_info) if address_info else ''
            )
            
            return location
        except Exception as e:
            print(f"Location creation error: {e}")
            return None
    
    def _extract_city_from_address(self, address_info: Dict) -> str:
        """Adres bilgisinden şehir çıkar"""
        if not address_info or 'address_components' not in address_info:
            return ''
        
        for component in address_info['address_components']:
            if 'locality' in component.get('types', []):
                return component['long_name']
        return ''
    
    def _extract_district_from_address(self, address_info: Dict) -> str:
        """Adres bilgisinden ilçe çıkar"""
        if not address_info or 'address_components' not in address_info:
            return ''
        
        for component in address_info['address_components']:
            if 'sublocality' in component.get('types', []):
                return component['long_name']
        return ''


class LocationSearchService:
    """Konum arama servisi"""
    
    def __init__(self):
        self.matching = LocationMatchingService()
    
    def search_by_location(self, latitude: float, longitude: float, 
                          radius_km: float = 5.0, item_type: str = None) -> Dict:
        """Konuma göre arama yap"""
        try:
            lost_items = self.matching.find_nearby_lost_items(
                latitude, longitude, radius_km, item_type
            )
            
            found_items = self.matching.find_nearby_found_items(
                latitude, longitude, radius_km, item_type
            )
            
            return {
                'lost_items': lost_items,
                'found_items': found_items,
                'search_center': {
                    'latitude': latitude,
                    'longitude': longitude,
                    'radius_km': radius_km
                },
                'total_results': len(lost_items) + len(found_items)
            }
            
        except Exception as e:
            print(f"Location search error: {e}")
            return {
                'lost_items': [],
                'found_items': [],
                'search_center': {
                    'latitude': latitude,
                    'longitude': longitude,
                    'radius_km': radius_km
                },
                'total_results': 0,
                'error': str(e)
            }
    
    def search_by_address(self, address: str, radius_km: float = 5.0, 
                         item_type: str = None) -> Dict:
        """Adrese göre arama yap"""
        try:
            # Adresi koordinatlara çevir
            maps = GoogleMapsService()
            coordinates = maps.geocode_address(address)
            
            if not coordinates:
                return {
                    'error': 'Address not found',
                    'lost_items': [],
                    'found_items': [],
                    'total_results': 0
                }
            
            # Koordinatlarla arama yap
            return self.search_by_location(
                coordinates['latitude'],
                coordinates['longitude'],
                radius_km,
                item_type
            )
            
        except Exception as e:
            print(f"Address search error: {e}")
            return {
                'error': str(e),
                'lost_items': [],
                'found_items': [],
                'total_results': 0
            }
