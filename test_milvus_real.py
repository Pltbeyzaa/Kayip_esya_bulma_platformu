import random
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility

# 1. Milvus'a Bağlan
print("🔌 Milvus'a bağlanılıyor...")
connections.connect("default", host="localhost", port="19530")

# 2. Koleksiyon Ayarları (Test için basit bir tablo)
collection_name = "test_image_collection"
dim = 128  # Vektör boyutu (Örn: Resimden çıkan sayı adedi)

# Eğer eski test tablosu varsa sil (Temiz başlangıç)
if utility.has_collection(collection_name):
    utility.drop_collection(collection_name)

# 3. Tablo Şemasını Oluştur
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
]
schema = CollectionSchema(fields, "Görsel eşleştirme testi için geçici tablo")
hello_milvus = Collection(collection_name, schema)

print(f"✅ Koleksiyon oluşturuldu: {collection_name}")

# 4. Rastgele Vektörler Üret (Sanki 10 farklı resim yüklemişiz gibi)
vectors = [[random.random() for _ in range(dim)] for _ in range(10)]
# Veriyi Milvus'a sok
hello_milvus.insert([vectors])
print(f"💾 10 adet test vektörü (sanal resim) başarıyla kaydedildi.")

# 5. İndeks Oluştur (Arama yapabilmek için şart)
index_params = {
    "metric_type": "L2",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 128}
}
hello_milvus.create_index("embedding", index_params)
print("⚡ İndeksleme tamamlandı.")

# 6. Belleğe Yükle
hello_milvus.load()

# 7. ARAMA TESTİ: İlk vektörü aratalım (Kendini bulması lazım)
print("-" * 30)
print("🔍 Arama Testi Başlıyor...")
search_vectors = [vectors[0]]  # İlk 'resmi' aratıyoruz
search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

results = hello_milvus.search(search_vectors, "embedding", search_params, limit=3)

for hits in results:
    for hit in hits:
        print(f"🎯 Eşleşme Bulundu! ID: {hit.id}, Benzerlik Mesafesi: {hit.distance}")

print("-" * 30)
print("🎉 TEBRİKLER! Milvus, vektörleri kaydedip arayabiliyor.")

# Temizlik (İsteğe bağlı, tabloyu silmeyelim ki görebil)
# utility.drop_collection(collection_name)