"""
Milvus ile çalışmak için basit bir sarmalayıcı.

Bu dosya, yeni ImageUploadAPIView için gereken `insert_vector`,
`OBJECT_COLLECTION` ve `PERSON_COLLECTION` sabitlerini sağlar.

Gerçek projede burada daha gelişmiş bir yapı (örneğin ayrı indexler,
alanlar vb.) kurulabilir.
"""

from typing import List

from django.conf import settings
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)


OBJECT_COLLECTION = "object_vectors"
PERSON_COLLECTION = "person_vectors"


def _connect():
    """Varsayılan Milvus bağlantısını kur."""
    host = getattr(settings, "MILVUS_HOST", "localhost")
    port = getattr(settings, "MILVUS_PORT", 19530)
    connections.connect("default", host=host, port=port)


def _ensure_collection(name: str, dim: int = 512) -> Collection:
    """Basit bir [id:int64, ilan_id:int64, vector:FLOAT_VECTOR] koleksiyonu hazırla."""
    _connect()

    if not utility.has_collection(name):
        fields = [
            FieldSchema(
                name="id", dtype=DataType.INT64, is_primary=True, auto_id=True
            ),
            FieldSchema(name="ilan_id", dtype=DataType.INT64),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim),
        ]
        schema = CollectionSchema(fields, description="FindUs image vectors")
        col = Collection(name=name, schema=schema)
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        }
        col.create_index("vector", index_params)
        return col

    return Collection(name=name)


def insert_vector(collection_name: str, vector: List[float], ilan_id: int) -> bool:
    """
    Verilen vektörü belirtilen koleksiyona (Milvus) ekle.

    Not: Hata durumunda False döner; gerçek projede logging / retry eklenebilir.
    """
    try:
        col = _ensure_collection(collection_name, dim=len(vector))
        col.load()
        # Milvus insert() metodu field sırasına göre liste bekler
        # Schema: id (auto), ilan_id, vector
        # Her field için bir liste, her liste aynı uzunlukta (1 kayıt için)
        col.insert([[ilan_id], [vector]])
        col.flush()
        return True
    except Exception as exc:  # pragma: no cover - runtime
        print(f"Milvus insert_vector hatası: {exc}")
        return False


