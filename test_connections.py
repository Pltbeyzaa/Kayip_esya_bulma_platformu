import sys
from pymongo import MongoClient
from pymilvus import connections, utility
import mysql.connector

# --- AYARLAR ---
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "FindUs123321.!"  # <-- BURAYA MYSQL ŞİFRENİ YAZ (Genelde: 'root', '1234', 'mysql' vb.)
MYSQL_DB_NAME = "sys"  # Test için varsayılan 'sys' tablosunu kullanıyoruz

MONGO_URI = "mongodb://localhost:27017/"
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"

def check_mysql():
    print("-" * 30)
    print("🐬 MySQL Bağlantısı Kontrol Ediliyor...")
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB_NAME
        )
        if conn.is_connected():
            print("✅ BAŞARILI: MySQL'e bağlanıldı!")
            conn.close()
            return True
    except Exception as e:
        print(f"❌ HATA: MySQL bağlantısı başarısız!\nSebep: {e}")
        return False

def check_mongo():
    print("-" * 30)
    print("🍃 MongoDB Bağlantısı Kontrol Ediliyor...")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        # Server bilgisini almayı dene (Ping at)
        client.server_info()
        print("✅ BAŞARILI: MongoDB'ye bağlanıldı!")
        return True
    except Exception as e:
        print(f"❌ HATA: MongoDB bağlantısı başarısız!\nSebep: {e}")
        return False

def check_milvus():
    print("-" * 30)
    print("🚀 Milvus (Vektör DB) Bağlantısı Kontrol Ediliyor...")
    try:
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
        print(f"✅ BAŞARILI: Milvus'a bağlanıldı!")
        
        # Ekstra kontrol: Koleksiyonları listeleme yetkisi var mı?
        try:
            col_list = utility.list_collections()
            print(f"   ℹ️  Mevcut Koleksiyonlar: {col_list}")
        except:
            print("   ℹ️  Bağlandı ama koleksiyonlar listelenemedi (sorun değil).")
            
        return True
    except Exception as e:
        print(f"❌ HATA: Milvus bağlantısı başarısız!\nSebep: {e}")
        print("   İPUCU: Docker'da Milvus portunun 19530 olduğundan emin ol.")
        return False

if __name__ == "__main__":
    print("🔍 FIND US PROJESİ - SİSTEM KONTROLÜ BAŞLIYOR...\n")
    
    mysql_ok = check_mysql()
    mongo_ok = check_mongo()
    milvus_ok = check_milvus()
    
    print("\n" + "="*30)
    if mysql_ok and mongo_ok and milvus_ok:
        print("🎉 SÜPER! BÜTÜN SİSTEMLER ÇALIŞIYOR.")
        print("Django geliştirmesine başlayabiliriz.")
    else:
        print("⚠️  BAZI BAĞLANTILARDA SORUN VAR. Lütfen hataları kontrol et.")
    print("="*30)



