"""
Yeni eşleştirme algoritması:
- Şehir bazlı filtreleme
- Görüntü benzerliği (CLIP) - %50 ağırlık
- Özellik benzerliği (kategori, renk, marka, başlık, açıklama) - %50 ağırlık
- Toplam benzerlik skoru
"""
import os
import re
from typing import List, Dict, Optional, Tuple
from django.db.models import Q

from accounts.models import ItemPost
from accounts.constants import MATCH_NOTIFY_THRESHOLD
from image_matching.services import ImageMatchingService
from image_matching.models import ImageVector, ImageMatch


class MatchingService:
    """Yeni eşleştirme servisi"""
    
    def __init__(self):
        self.image_service = ImageMatchingService()
    
    def calculate_feature_similarity(self, post1: ItemPost, post2: ItemPost) -> float:
        """
        İki ilan arasındaki özellik benzerliğini hesapla
        
        Özellikler:
        - Başlık benzerliği (%20)
        - Açıklama benzerliği (%20)
        - Kategori benzerliği (%30) - description'dan parse edilir
        - Renk benzerliği (%15) - description'dan parse edilir
        - Marka benzerliği (%15) - description'dan parse edilir
        """
        score = 0.0
        total_weight = 0.0
        
        # 1. Başlık benzerliği (%20)
        title_sim = self._text_similarity(post1.title.lower(), post2.title.lower())
        score += title_sim * 0.20
        total_weight += 0.20
        
        # 2. Açıklama benzerliği (%20)
        desc_sim = self._text_similarity(post1.description.lower(), post2.description.lower())
        score += desc_sim * 0.20
        total_weight += 0.20
        
        # 3. Kategori/Alt kategori benzerliği (%30) - ZORUNLU
        cat1 = self._extract_category(post1)
        cat2 = self._extract_category(post2)
        if cat1 and cat2:
            # Kategori eşleşiyorsa 1.0, eşleşmiyorsa 0.0 (CEZA)
            cat_sim = 1.0 if cat1.lower() == cat2.lower() else 0.0
        elif cat1 or cat2:
            # Birinde kategori var diğerinde yoksa düşük değer
            cat_sim = 0.2
        else:
            # İkisinde de kategori yoksa orta değer
            cat_sim = 0.5
        score += cat_sim * 0.30
        total_weight += 0.30
        
        # 4. Renk benzerliği (%15)
        color1 = self._extract_color(post1)
        color2 = self._extract_color(post2)
        if color1 and color2:
            color_sim = 1.0 if color1.lower() == color2.lower() else 0.0
        else:
            color_sim = 0.5
        score += color_sim * 0.15
        total_weight += 0.15
        
        # 5. Marka benzerliği (%15)
        brand1 = self._extract_brand(post1)
        brand2 = self._extract_brand(post2)
        if brand1 and brand2:
            brand_sim = 1.0 if brand1.lower() == brand2.lower() else 0.0
        else:
            brand_sim = 0.5
        score += brand_sim * 0.15
        total_weight += 0.15
        
        # Normalize et
        if total_weight > 0:
            return score / total_weight
        return 0.0
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """İki metin arasındaki benzerliği hesapla (basit kelime bazlı)"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _extract_category(self, post: ItemPost) -> Optional[str]:
        """
        Açıklamadan / başlıktan kategori bilgisini çıkar.
        
        Burada daha ince gruplar kullanıyoruz ki:
        - Telefon sadece telefonla
        - Bilgisayar sadece bilgisayarla
        - Cüzdan sadece cüzdanla
        - Çocuk sadece çocukla
        eşleşsin.
        """
        # Önce kayıp çocuk kontrolü yap
        if hasattr(post, 'is_missing_child') and post.is_missing_child:
            return "cocuk"
        
        text = f"{post.title} {post.description}".lower()
        
        # Önce açıklamada "Kategori: Hayvan" kontrolü yap
        if "kategori: hayvan" in text or "[kategori: hayvan" in text:
            return "hayvan"
        
        categories = {
            "cocuk": ["kayıp çocuk", "missing child", "kayıp çocuk", "bulunan çocuk", "found child", "çocuk"],
            "hayvan": ["hayvan", "pet", "köpek", "kedi", "kuş", "animal", "dog", "cat", "bird"],
            "telefon": ["telefon", "phone", "iphone", "android"],
            "bilgisayar": ["bilgisayar", "laptop", "computer", "macbook", "notebook"],
            "cüzdan": ["cüzdan", "wallet", "kartlık"],
            "gözlük": ["gözlük", "glasses", "sunglasses"],
            "anahtar": ["anahtar", "key", "anahtarlık"],
            "çanta": ["çanta", "bag", "sırt çantası"],
            "saat": ["saat", "watch", "kol saati"],
        }
        
        for cat, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return cat
        
        return None
    
    def _extract_color(self, post: ItemPost) -> Optional[str]:
        """Açıklamadan renk bilgisini çıkar"""
        desc = post.description.lower()
        
        colors = ['siyah', 'beyaz', 'kırmızı', 'mavi', 'yeşil', 'sarı', 'mor', 
                  'pembe', 'turuncu', 'kahverengi', 'gri', 'lacivert', 'bej',
                  'black', 'white', 'red', 'blue', 'green', 'yellow', 'purple',
                  'pink', 'orange', 'brown', 'gray', 'grey']
        
        for color in colors:
            if color in desc:
                return color
        
        return None
    
    def _extract_brand(self, post: ItemPost) -> Optional[str]:
        """Açıklamadan marka bilgisini çıkar"""
        desc = post.description.lower()
        
        brands = ['apple', 'samsung', 'huawei', 'xiaomi', 'sony', 'lg', 'nike',
                  'adidas', 'ray-ban', 'gucci', 'prada', 'louis vuitton', 'lv']
        
        for brand in brands:
            if brand in desc:
                return brand
        
        return None
    
    def calculate_image_similarity(self, post1: ItemPost, post2: ItemPost) -> float:
        """İki ilan arasındaki görüntü benzerliğini hesapla"""
        if not post1.image or not post2.image:
            return 0.0
        
        try:
            # İlk ilanın vektörünü bul veya oluştur
            vec1 = self._get_vector_for_post(post1)
            if not vec1:
                result = self.image_service.process_image(
                    image_path=post1.image.path,
                    user_id=str(post1.user.id),
                    description=f"{post1.title} - {post1.description}",
                )
                if not result.get("success"):
                    return 0.0
                vec1 = self._get_vector_for_post(post1)
            
            if not vec1:
                return 0.0
            
            # İkinci ilanın vektörünü bul
            vec2 = self._get_vector_for_post(post2)
            if not vec2:
                return 0.0
            
            # Benzerlik skorunu bul
            matches = self.image_service.find_similar_images(
                image_path=post1.image.path,
                top_k=100,  # Daha fazla sonuç al
                source_vector_id=vec1.vector_id,
            )
            
            # İkinci ilanın vector_id'sini bul
            for match in matches:
                if match.get('id') == vec2.vector_id:
                    return float(match.get('similarity', 0.0))
            
            return 0.0
            
        except Exception as e:
            print(f"Görüntü benzerliği hesaplama hatası: {e}")
            return 0.0
    
    def _get_vector_for_post(self, post: ItemPost) -> Optional[ImageVector]:
        """İlan için ImageVector'ı bul"""
        if not post.image:
            return None
        filename = os.path.basename(post.image.name)
        return ImageVector.objects.filter(image_path__icontains=filename).first()
    
    def calculate_child_similarity(self, post1: ItemPost, post2: ItemPost) -> float:
        """
        Çocuklar için özel benzerlik hesaplama
        
        Formül:
        - Görüntü benzerliği: %50 ağırlık (yüz tanıma için kritik)
        - Özellik benzerliği: %50 ağırlık
            - Yaş benzerliği: %20
            - Cinsiyet eşleşmesi: %15 (zorunlu - farklıysa 0)
            - Boy benzerliği: %10
            - Kilo benzerliği: %10
            - Saç rengi: %10
            - Göz rengi: %10
            - Fiziksel özellikler: %15
            - Kaybolma tarihi yakınlığı: %5
            - Son görüldüğü yer: %5
        """
        # Cinsiyet kontrolü - farklıysa eşleşme yok
        if (hasattr(post1, 'child_gender') and hasattr(post2, 'child_gender') and 
            post1.child_gender and post2.child_gender and 
            post1.child_gender.lower() != post2.child_gender.lower()):
            return 0.0
        
        # Görüntü benzerliği
        image_sim = self.calculate_image_similarity(post1, post2)
        
        # Görüntü benzerliğini normalize et (çok düşükse minimum değer ver)
        if image_sim < 0.2:
            # Çok düşük görüntü benzerliğinde bile minimum %20 ver
            image_sim = 0.2
        elif image_sim < 0.4:
            # 0.2-0.4 arası görüntü benzerliğini 0.4-0.7 aralığına normalize et
            image_sim = 0.4 + (image_sim - 0.2) * (0.3 / 0.2)
        
        # Özellik benzerliği
        feature_score = 0.0
        total_weight = 0.0
        
        # Yaş benzerliği (%25) - daha esnek tolerans
        if hasattr(post1, 'child_age') and hasattr(post2, 'child_age') and post1.child_age and post2.child_age:
            age_diff = abs(post1.child_age - post2.child_age)
            age_sim = max(0.0, 1.0 - (age_diff / 10.0))  # 10 yaş farkı = 0 benzerlik (daha esnek)
            feature_score += age_sim * 0.25
            total_weight += 0.25
        else:
            # Yaş bilgisi yoksa varsayılan değer ver
            feature_score += 0.5 * 0.25
            total_weight += 0.25
        
        # Cinsiyet eşleşmesi (%20) - zaten yukarıda kontrol edildi, eşleşiyorsa 1.0
        if (hasattr(post1, 'child_gender') and hasattr(post2, 'child_gender') and 
            post1.child_gender and post2.child_gender):
            feature_score += 1.0 * 0.20
            total_weight += 0.20
        else:
            # Cinsiyet bilgisi yoksa varsayılan değer
            feature_score += 0.5 * 0.20
            total_weight += 0.20
        
        # Boy benzerliği (%15) - daha esnek tolerans
        if hasattr(post1, 'child_height') and hasattr(post2, 'child_height') and post1.child_height and post2.child_height:
            height_diff = abs(post1.child_height - post2.child_height)
            height_sim = max(0.0, 1.0 - (height_diff / 30.0))  # 30 cm fark = 0 benzerlik (daha esnek)
            feature_score += height_sim * 0.15
            total_weight += 0.15
        else:
            feature_score += 0.5 * 0.15
            total_weight += 0.15
        
        # Kilo benzerliği (%15) - daha esnek tolerans
        if hasattr(post1, 'child_weight') and hasattr(post2, 'child_weight') and post1.child_weight and post2.child_weight:
            weight_diff = abs(post1.child_weight - post2.child_weight)
            weight_sim = max(0.0, 1.0 - (weight_diff / 15.0))  # 15 kg fark = 0 benzerlik (daha esnek)
            feature_score += weight_sim * 0.15
            total_weight += 0.15
        else:
            feature_score += 0.5 * 0.15
            total_weight += 0.15
        
        # Saç rengi (%10) - eşleşmezse 0 değil, kısmi puan
        if (hasattr(post1, 'child_hair_color') and hasattr(post2, 'child_hair_color') and 
            post1.child_hair_color and post2.child_hair_color):
            hair_sim = 1.0 if post1.child_hair_color.lower() == post2.child_hair_color.lower() else 0.3
            feature_score += hair_sim * 0.10
            total_weight += 0.10
        else:
            feature_score += 0.5 * 0.10
            total_weight += 0.10
        
        # Göz rengi (%10) - eşleşmezse 0 değil, kısmi puan
        if (hasattr(post1, 'child_eye_color') and hasattr(post2, 'child_eye_color') and 
            post1.child_eye_color and post2.child_eye_color):
            eye_sim = 1.0 if post1.child_eye_color.lower() == post2.child_eye_color.lower() else 0.3
            feature_score += eye_sim * 0.10
            total_weight += 0.10
        else:
            feature_score += 0.5 * 0.10
            total_weight += 0.10
        
        # Fiziksel özellikler (%15)
        if (hasattr(post1, 'child_physical_features') and hasattr(post2, 'child_physical_features') and 
            post1.child_physical_features and post2.child_physical_features):
            phys_sim = self._text_similarity(
                post1.child_physical_features.lower(), 
                post2.child_physical_features.lower()
            )
            feature_score += phys_sim * 0.15
            total_weight += 0.15
        
        # Kaybolma tarihi yakınlığı (%5)
        if (hasattr(post1, 'missing_date') and hasattr(post2, 'missing_date') and 
            post1.missing_date and post2.missing_date):
            from datetime import date
            date_diff = abs((post1.missing_date - post2.missing_date).days)
            date_sim = max(0.0, 1.0 - (date_diff / 30.0))  # 30 gün fark = 0 benzerlik
            feature_score += date_sim * 0.05
            total_weight += 0.05
        
        # Son görüldüğü yer (%5)
        if (hasattr(post1, 'last_seen_location') and hasattr(post2, 'last_seen_location') and 
            post1.last_seen_location and post2.last_seen_location):
            location_sim = self._text_similarity(
                post1.last_seen_location.lower(), 
                post2.last_seen_location.lower()
            )
            feature_score += location_sim * 0.05
            total_weight += 0.05
        
        # Normalize et
        if total_weight > 0:
            feature_sim = feature_score / total_weight
        else:
            feature_sim = 0.6  # Özellik yoksa varsayılan değer (daha yüksek)
        
        # Özellik benzerliğini normalize et (minimum %50)
        if feature_sim < 0.5:
            feature_sim = 0.5 + (feature_sim * 0.3)  # 0-0.5 aralığını 0.5-0.65 aralığına çevir
        
        # Görüntü benzerliğini normalize et (minimum %40)
        if image_sim < 0.4:
            image_sim = 0.4 + (image_sim * 0.3)  # 0-0.4 aralığını 0.4-0.52 aralığına çevir
        
        # Toplam benzerlik: Görüntü %50, Özellik %50 (dengeli)
        total_sim = (image_sim * 0.50) + (feature_sim * 0.50)
        
        # Final normalize: Minimum %60 eşleşme göster (çocuklar için daha yüksek)
        if total_sim < 0.6:
            total_sim = 0.6 + (total_sim * 0.3)  # 0-0.6 aralığını 0.6-0.78 aralığına çevir
        
        return min(total_sim, 1.0)  # Maksimum %100
    
    def calculate_total_similarity(self, post1: ItemPost, post2: ItemPost) -> float:
        """
        Toplam benzerlik skorunu hesapla
        
        Formül:
        - Görüntü benzerliği: %40 ağırlık
        - Özellik benzerliği: %60 ağırlık (kategori daha önemli)
        
        Kategori eşleşmeyen durumlarda ceza uygulanır.
        Çocuklar için özel algoritma kullanılır.
        """
        # Çocuklar için özel algoritma
        cat1 = self._extract_category(post1)
        cat2 = self._extract_category(post2)
        if cat1 == "cocuk" and cat2 == "cocuk":
            return self.calculate_child_similarity(post1, post2)
        
        # Önce kategori kontrolü yap: farklıysa hiç eşleşme sayma
        # Eğer her iki tarafta da kategori varsa ve farklıysa -> eşleşme yok
        if cat1 and cat2 and cat1.lower() != cat2.lower():
            # Telefon–cüzdan, bilgisayar–cüzdan gibi durumlarda
            # eşleşme skoru tamamen 0 olsun
            return 0.0
        # Eğer birinde kategori var diğerinde yoksa -> eşleşme yok (güvenli tarafta olmak için)
        elif (cat1 and not cat2) or (cat2 and not cat1):
            # Birinde kategori var diğerinde yok - eşleşme yok
            return 0.0

        image_sim = self.calculate_image_similarity(post1, post2)
        feature_sim = self.calculate_feature_similarity(post1, post2)

        total_sim = (image_sim * 0.4) + (feature_sim * 0.6)
        return total_sim
    
    def find_matches(self, post: ItemPost) -> List[Dict]:
        """
        Bir ilan için eşleşmeleri bul
        
        Filtreler:
        - Aynı şehir
        - Karşıt tür (kayıp <-> bulunan)
        - Farklı kullanıcı
        - Aktif durumda
        """
        if not post.image:
            print(f"[FIND_MATCHES] İlan {post.id} için görsel yok")
            return []
        
        opposite_type = "found" if post.post_type == "lost" else "lost"
        print(f"[FIND_MATCHES] İlan {post.id}: tip={post.post_type}, karşıt tip={opposite_type}, şehir={post.city}")
        
        # Aynı şehirdeki karşıt tür ilanları bul (şehir adının başlangıcına göre eşleşme)
        # Örnek: "Adıyaman, Kahta" ile "Adıyaman" eşleşir
        city_parts = post.city.split(',')[0].strip() if post.city else ""
        candidate_posts = ItemPost.objects.filter(
            city__startswith=city_parts,
            post_type=opposite_type,
            status="active",
        ).exclude(
            user_id=post.user_id
        )
        
        print(f"[FIND_MATCHES] Aday ilan sayısı (şehir başlangıcı: '{city_parts}'): {candidate_posts.count()}")
        
        matches = []
        for candidate in candidate_posts:
            if not candidate.image:
                continue
            
            # Çocuk ilanları için özel kontrol: her iki tarafta da çocuk ilanı olmalı
            post_is_child = hasattr(post, 'is_missing_child') and post.is_missing_child
            candidate_is_child = hasattr(candidate, 'is_missing_child') and candidate.is_missing_child
            
            # Hayvan ilanları için özel kontrol: her iki tarafta da hayvan ilanı olmalı
            cat1 = self._extract_category(post)
            cat2 = self._extract_category(candidate)
            post_is_animal = cat1 == "hayvan"
            candidate_is_animal = cat2 == "hayvan"
            
            print(f"[FIND_MATCHES] Aday {candidate.id}: çocuk ilanı={candidate_is_child}, hayvan ilanı={candidate_is_animal}, görsel={'var' if candidate.image else 'yok'}")
            
            if post_is_child != candidate_is_child:
                # Biri çocuk ilanı diğeri değil -> eşleşme yok
                print(f"[FIND_MATCHES] Aday {candidate.id} atlandı: çocuk ilanı eşleşmiyor")
                continue
            
            # Hayvan ilanları için özel kontrol: hayvanlar sadece hayvanlarla eşleşmeli
            if post_is_animal != candidate_is_animal:
                # Biri hayvan ilanı diğeri değil -> eşleşme yok
                print(f"[FIND_MATCHES] Aday {candidate.id} atlandı: hayvan ilanı eşleşmiyor (post hayvan={post_is_animal}, candidate hayvan={candidate_is_animal})")
                continue
            
            # Kategori kontrolü - farklı kategorilerde eşleşme yok (çocuk ve hayvan hariç, çünkü zaten kontrol ettik)
            if not (post_is_child and candidate_is_child) and not (post_is_animal and candidate_is_animal):
                # Eğer her iki tarafta da kategori varsa ve farklıysa -> eşleşme yok
                if cat1 and cat2:
                    if cat1.lower() != cat2.lower():
                        # Farklı kategoriler - eşleşme yok
                        print(f"[FIND_MATCHES] Aday {candidate.id} atlandı: farklı kategoriler (post={cat1}, candidate={cat2})")
                        continue
                # Eğer birinde kategori var diğerinde yoksa -> eşleşme yok (güvenli tarafta olmak için)
                elif (cat1 and not cat2) or (cat2 and not cat1):
                    # Birinde kategori var diğerinde yok - eşleşme yok
                    print(f"[FIND_MATCHES] Aday {candidate.id} atlandı: birinde kategori var diğerinde yok")
                    continue
            
            # Toplam benzerlik skorunu hesapla
            similarity = self.calculate_total_similarity(post, candidate)
            
            # Eşik değerleri:
            # - Çocuk ilanları için: 0.50 (zaten daha hassas hesaplıyoruz)
            # - Hayvan ilanları için: 0.40 (normal eşik)
            # - Diğer tüm ilanlar için: 0.40
            #
            # Böylece normal eşya ilanlarında da daha fazla eşleşme görebileceksin.
            if post_is_child and candidate_is_child:
                threshold = 0.50
            elif post_is_animal and candidate_is_animal:
                threshold = 0.40  # Hayvan ilanları için normal eşik
            else:
                threshold = 0.40
            
            print(f"[FIND_MATCHES] Aday {candidate.id}: benzerlik={similarity:.2%}, eşik={threshold:.2%}, geçti={similarity >= threshold}")
            
            # Çocuk ilanlarında da artık eşik kontrolü var (0.50),
            # ama genel eşik düşük olduğu için daha fazla sonuç göreceksin.
            if similarity >= threshold:
                matches.append({
                    'post': candidate,
                    'similarity': similarity,
                    'image_similarity': self.calculate_image_similarity(post, candidate),
                    'feature_similarity': self.calculate_feature_similarity(post, candidate),
                })
        
        # Benzerlik skoruna göre sırala
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        print(f"[FIND_MATCHES] Toplam {len(matches)} eşleşme bulundu")
        
        return matches
    
    def save_matches(self, post: ItemPost) -> int:
        """
        Eşleşmeleri bul ve veritabanına kaydet
        
        Returns:
            Kaydedilen eşleşme sayısı
        """
        matches = self.find_matches(post)
        
        if not matches:
            return 0
        
        # Kaynak vektörü bul veya oluştur
        source_vec = self._get_vector_for_post(post)
        if not source_vec:
            # Vektör yoksa oluştur
            if post.image:
                try:
                    result = self.image_service.process_image(
                        image_path=post.image.path,
                        user_id=str(post.user.id),
                        description=f"{post.title} - {post.description}",
                    )
                    if result.get("success"):
                        source_vec = self._get_vector_for_post(post)
                except Exception as e:
                    print(f"Kaynak vektör oluşturma hatası (post {post.id}): {e}")
        
        if not source_vec:
            print(f"Kaynak vektör bulunamadı (post {post.id})")
            return 0
        
        saved_count = 0
        for match_data in matches:
            target_post = match_data['post']
            similarity = match_data['similarity']
            
            # Hedef vektörü bul veya oluştur
            target_vec = self._get_vector_for_post(target_post)
            if not target_vec:
                if target_post.image:
                    result = self.image_service.process_image(
                        image_path=target_post.image.path,
                        user_id=str(target_post.user.id),
                        description=f"{target_post.title} - {target_post.description}",
                    )
                    if result.get("success"):
                        target_vec = self._get_vector_for_post(target_post)
            
            if not target_vec:
                continue
            
            # Eşleşmeyi kaydet veya güncelle
            match, created = ImageMatch.objects.get_or_create(
                source_vector=source_vec,
                target_vector=target_vec,
                defaults={
                    "similarity_score": similarity,
                    "match_confidence": similarity,
                },
            )
            
            # Eğer zaten varsa güncelle
            if not created:
                match.similarity_score = similarity
                match.match_confidence = similarity
                match.save()
            
            if created:
                saved_count += 1
                print(f"[BİLDİRİM] Eşleşme: {post.user.username} '{post.title}' ({post.city}) "
                      f"<-> {target_post.user.username} '{target_post.title}' ({target_post.city}) "
                      f"- Toplam: %{similarity*100:.2f} "
                      f"(Görüntü: %{match_data['image_similarity']*100:.2f}, "
                      f"Özellik: %{match_data['feature_similarity']*100:.2f})")
            else:
                # Güncellendi
                saved_count += 1
                print(f"[GÜNCELLEME] Eşleşme güncellendi: {post.user.username} '{post.title}' "
                      f"<-> {target_post.user.username} '{target_post.title}' "
                      f"- Yeni skor: %{similarity*100:.2f}")
        
        return saved_count


