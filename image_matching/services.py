"""
Görüntü eşleştirme servisleri

Not: Bu sürümde Google Cloud Vision kaldırıldı ve yerine
CLIP tabanlı vektörleme kullanılmaktadır (bkz. image_matching.utils).
"""
from typing import List, Optional

from django.conf import settings
from django.utils import timezone
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from kayip_esya.mongodb import get_collection
from .models import ImageMatch, ImageVector
from .utils import image_to_clip_vector


class MilvusService:
    """Milvus vektör veritabanı servisi"""
    
    def __init__(self):
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        self.user = settings.MILVUS_USER
        self.password = settings.MILVUS_PASSWORD
        self.collection_name = "image_vectors"
        # CLIP ViT-B/32 embedding boyutu (open-clip default: 512)
        self.dimension = 512
        
    def connect(self):
        """Milvus'a bağlan (retry ve host fallback ile)"""
        import time

        hosts_to_try = [self.host]
        if self.host == 'localhost':
            hosts_to_try.append('127.0.0.1')

        last_error = None
        for host_candidate in hosts_to_try:
            for _ in range(10):  # ~10 deneme, toplam ~10-15 sn bekleme
                try:
                    connections.connect(
                        alias="default",
                        host=host_candidate,
                        port=self.port,
                        user=self.user if self.user else None,
                        password=self.password if self.password else None
                    )
                    # Sunucu hazır mı diye kontrol et
                    try:
                        _ = utility.get_server_version()
                    except Exception:
                        time.sleep(1)
                        continue
                    return True
                except Exception as e:
                    last_error = e
                    time.sleep(1)
        print(f"Milvus connection error: {last_error}")
        return False
    
    def create_collection(self):
        """Koleksiyon oluştur"""
        if not self.connect():
            return False
            
        try:
            # Field tanımları
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
                FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="image_path", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=1000),
            ]
            
            schema = CollectionSchema(fields, "Image vectors collection")
            
            # Koleksiyon var mı kontrol et
            if utility.has_collection(self.collection_name):
                return True

            # Koleksiyon oluştur
            collection = Collection(self.collection_name, schema)
            
            # Index oluştur (IP metric'i normalize edilmiş vektörler için cosine similarity sağlar)
            index_params = {
                "metric_type": "IP",  # Inner Product (cosine similarity için)
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            collection.create_index("vector", index_params)
            
            return True
        except Exception as e:
            print(f"Collection creation error: {e}")
            return False
    
    def insert_vector(self, vector_id: str, vector: List[float], user_id: str, 
                     image_path: str, description: str = ""):
        """Vektör ekle"""
        if not self.connect():
            return False
            
        try:
            collection = Collection(self.collection_name)
            collection.load()
            
            data = [
                [vector_id],
                [vector],
                [user_id],
                [image_path],
                [description]
            ]
            
            collection.insert(data)
            collection.flush()
            return True
        except Exception as e:
            print(f"Vector insertion error: {e}")
            return False
    
    def search_similar(self, query_vector: List[float], top_k: int = 10) -> List[dict]:
        """Benzer vektörleri ara"""
        if not self.connect():
            return []
            
        try:
            collection = Collection(self.collection_name)
            collection.load()
            
            # Normalize edilmiş vektörler için IP (Inner Product) kullan
            # IP = cosine similarity (normalize edilmiş vektörler için)
            search_params = {
                "metric_type": "IP",  # Inner Product (cosine similarity için)
                "params": {"nprobe": 10}
            }
            
            results = collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                output_fields=["id", "user_id", "image_path", "description"]
            )
            
            matches = []
            for hits in results:
                for hit in hits:
                    # IP metric: normalize edilmiş vektörler için IP = cosine similarity
                    # Milvus IP score'u -1 ile 1 arasında değerler döner
                    # En yüksek benzerlik için en yüksek IP değeri aranır
                    ip_score = hit.score  # IP score (-1 ile 1 arası)
                    
                    # Cosine similarity'yi 0-1 aralığına normalize et
                    # IP score zaten cosine similarity (normalize edilmiş vektörler için)
                    cosine_similarity = max(0.0, min(1.0, (ip_score + 1) / 2))
                    
                    matches.append({
                        'id': hit.entity.get('id'),
                        'user_id': hit.entity.get('user_id'),
                        'image_path': hit.entity.get('image_path'),
                        'description': hit.entity.get('description'),
                        'distance': 1 - cosine_similarity,
                        'similarity': cosine_similarity,  # Cosine similarity (0-1 arası)
                        'raw_ip_score': ip_score  # Debug için ham IP score
                    })
            
            return matches
        except Exception as e:
            print(f"Search error: {e}")
            return []


class ImageMatchingService:
    """Görüntü eşleştirme ana servisi"""
    
    def __init__(self):
        self.milvus = MilvusService()
    
    def process_image(self, image_path: str, user_id: str, description: str = "") -> dict:
        """Görüntüyü işle ve vektör veritabanına ekle"""
        try:
            # CLIP ile özellik vektörünü çıkar
            features = image_to_clip_vector(image_path)
            if not features:
                return {'success': False, 'error': 'Feature extraction failed'}
            
            # Milvus koleksiyonunu oluştur (yoksa)
            self.milvus.create_collection()
            
            # Benzersiz ID oluştur
            import uuid
            vector_id = str(uuid.uuid4())
            
            # Vektörü ekle
            success = self.milvus.insert_vector(
                vector_id=vector_id,
                vector=features,
                user_id=user_id,
                image_path=image_path,
                description=description
            )
            
            if success:
                # Django DB: ImageVector kaydet
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user = User.objects.get(id=int(user_id))
                except (User.DoesNotExist, ValueError):
                    return {'success': False, 'error': f'User with id {user_id} not found'}
                
                image_vector = ImageVector.objects.create(
                    user=user,
                    image_path=image_path,
                    vector_id=vector_id,
                    description=description
                )
                # MongoDB log
                try:
                    logs = get_collection('image_processing_logs')
                    logs.insert_one({
                        'event': 'process_image',
                        'user_id': user_id,
                        'vector_id': vector_id,
                        'image_path': image_path,
                        'description': description,
                        'features_count': len(features),
                        'created_at': timezone.now().isoformat()
                    })
                except Exception:
                    pass
                return {
                    'success': True,
                    'vector_id': vector_id,
                    'image_vector_id': str(image_vector.id),
                    'features_count': len(features)
                }
            else:
                return {'success': False, 'error': 'Vector insertion failed'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def find_similar_images(self, image_path: str, top_k: int = 10, source_vector_id: Optional[str] = None) -> List[dict]:
        """Benzer görüntüleri bul"""
        try:
            # CLIP ile özellik vektörünü çıkar
            features = image_to_clip_vector(image_path)
            if not features:
                return []
            
            # Benzer vektörleri ara
            matches = self.milvus.search_similar(features, top_k)
            # MongoDB log (search)
            try:
                logs = get_collection('image_processing_logs')
                logs.insert_one({
                    'event': 'find_similar_images',
                    'image_path': image_path,
                    'top_k': top_k,
                    'results': len(matches),
                    'created_at': timezone.now().isoformat()
                })
            except Exception:
                pass

            # Eşleşmeleri veritabanına yaz (varsa kaynak vector)
            if source_vector_id:
                try:
                    source_vector = ImageVector.objects.get(vector_id=source_vector_id)
                    for m in matches:
                        try:
                            target_vector = ImageVector.objects.filter(vector_id=m.get('id')).first()
                            if not target_vector:
                                continue
                            ImageMatch.objects.get_or_create(
                                source_vector=source_vector,
                                target_vector=target_vector,
                                defaults={
                                    'similarity_score': float(m.get('similarity', 0.0)),
                                    'match_confidence': max(0.0, min(1.0, float(m.get('similarity', 0.0))))
                                }
                            )
                        except Exception:
                            continue
                except ImageVector.DoesNotExist:
                    pass

            return matches
            
        except Exception as e:
            print(f"Similar image search error: {e}")
            return []
    
    def get_image_objects(self, image_path: str) -> List[dict]:
        """Nesne tespiti şu an devre dışı (Cloud Vision kaldırıldı)."""
        return []
