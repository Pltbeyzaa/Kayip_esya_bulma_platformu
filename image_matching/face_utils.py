"""
Yüz tanıma / FaceNet entegrasyonu için geçici yardımcı fonksiyonlar.

Projede gerçek FaceNet modeli entegre edilene kadar, bu dosya
`get_face_embedding` fonksiyonunu basit bir stub olarak sağlar.
"""

from typing import List, Tuple


def get_face_embedding(image_path: str) -> Tuple[bool, List[float] | None]:
    """
    Verilen görüntüde yüz algıla ve varsa embedding döndür.

    Dönüş:
        (is_face, embedding or None)

    Not: Şu an sadece stub; her zaman yüz yokmuş gibi (False, None) döner.
    Gerçek projede burası FaceNet / başka bir yüz modeli ile değiştirilmelidir.
    """
    return False, None


