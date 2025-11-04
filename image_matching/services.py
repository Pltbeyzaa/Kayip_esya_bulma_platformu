"""
Görüntü eşleştirme servisleri
"""
import os
import numpy as np
from typing import List, Tuple, Optional, Dict
from django.conf import settings
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
from google.cloud import vision
import cv2
from PIL import Image
import io
import base64
from .models import ImageVector, ImageMatch
from django.utils import timezone
from kayip_esya.mongodb import get_collection


class MilvusService:
    """Milvus vektör veritabanı servisi"""
    
    def __init__(self):
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        self.user = settings.MILVUS_USER
        self.password = settings.MILVUS_PASSWORD
        self.collection_name = "image_vectors"
        self.dimension = 2048  # Google Cloud Vision feature vector boyutu
        
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
            
            # Index oluştur
            index_params = {
                "metric_type": "L2",
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
            
            search_params = {
                "metric_type": "L2",
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
                    matches.append({
                        'id': hit.entity.get('id'),
                        'user_id': hit.entity.get('user_id'),
                        'image_path': hit.entity.get('image_path'),
                        'description': hit.entity.get('description'),
                        'distance': hit.distance,
                        'similarity': 1 - hit.distance  # L2 distance'ı similarity'ye çevir
                    })
            
            return matches
        except Exception as e:
            print(f"Search error: {e}")
            return []


class GoogleVisionService:
    """Google Cloud Vision API servisi"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Vision client'ı başlat"""
        try:
            if settings.GOOGLE_APPLICATION_CREDENTIALS:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.GOOGLE_APPLICATION_CREDENTIALS
            
            self.client = vision.ImageAnnotatorClient()
        except Exception as e:
            print(f"Google Vision client initialization error: {e}")
    
    def extract_features(self, image_path: str) -> Optional[List[float]]:
        """Görüntüden özellik vektörü çıkar"""
        if not self.client:
            return None
            
        try:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Object detection
            objects = self.client.object_localization(image=image).localized_object_annotations
            
            # Feature extraction için görüntüyü işle
            features = self._extract_visual_features(image_path)
            
            return features
            
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return None
    
    def _extract_visual_features(self, image_path: str) -> List[float]:
        """Görsel özellikleri çıkar"""
        try:
            # OpenCV ile görüntü işleme
            img = cv2.imread(image_path)
            img = cv2.resize(img, (224, 224))  # Standart boyut
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Basit özellik çıkarımı (gerçek uygulamada CNN kullanılabilir)
            features = []
            
            # Histogram özellikleri
            hist_r = cv2.calcHist([img], [0], None, [64], [0, 256])
            hist_g = cv2.calcHist([img], [1], None, [64], [0, 256])
            hist_b = cv2.calcHist([img], [2], None, [64], [0, 256])
            
            features.extend(hist_r.flatten())
            features.extend(hist_g.flatten())
            features.extend(hist_b.flatten())
            
            # Texture özellikleri
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            features.append(edge_density)
            
            # Renk istatistikleri
            mean_color = np.mean(img, axis=(0, 1))
            features.extend(mean_color)
            
            std_color = np.std(img, axis=(0, 1))
            features.extend(std_color)
            
            # Boyutu 2048'e çıkar (padding veya truncation)
            if len(features) < 2048:
                features.extend([0] * (2048 - len(features)))
            else:
                features = features[:2048]
            
            return features
            
        except Exception as e:
            print(f"Visual feature extraction error: {e}")
            return [0] * 2048
    
    def detect_objects(self, image_path: str) -> List[dict]:
        """Görüntüdeki nesneleri tespit et"""
        if not self.client:
            return []
            
        try:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            objects = self.client.object_localization(image=image).localized_object_annotations
            
            detected_objects = []
            for obj in objects:
                detected_objects.append({
                    'name': obj.name,
                    'confidence': obj.score,
                    'bounding_box': {
                        'x': obj.bounding_poly.normalized_vertices[0].x,
                        'y': obj.bounding_poly.normalized_vertices[0].y,
                        'width': obj.bounding_poly.normalized_vertices[2].x - obj.bounding_poly.normalized_vertices[0].x,
                        'height': obj.bounding_poly.normalized_vertices[2].y - obj.bounding_poly.normalized_vertices[0].y,
                    }
                })
            
            return detected_objects
            
        except Exception as e:
            print(f"Object detection error: {e}")
            return []


class ImageMatchingService:
    """Görüntü eşleştirme ana servisi"""
    
    def __init__(self):
        self.milvus = MilvusService()
        self.vision = GoogleVisionService()
    
    def process_image(self, image_path: str, user_id: str, description: str = "") -> dict:
        """Görüntüyü işle ve vektör veritabanına ekle"""
        try:
            # Özellik vektörünü çıkar
            features = self.vision.extract_features(image_path)
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
                image_vector = ImageVector.objects.create(
                    user_id=user_id,
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
            # Özellik vektörünü çıkar
            features = self.vision.extract_features(image_path)
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
        """Görüntüdeki nesneleri tespit et"""
        return self.vision.detect_objects(image_path)
