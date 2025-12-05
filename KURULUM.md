# Findus Kurulum Rehberi

## Sorun: Django Modülü Bulunamadı

Bu hata, virtual environment'ın aktif olmadığını veya paketlerin yüklenmediğini gösterir.

## Çözüm Adımları

### 1. Virtual Environment'ı Aktifleştirin

**PowerShell'de:**
```powershell
cd C:\Users\Beyza\Desktop\findus\Kayip_esya_bulma_platformu
.\venv\Scripts\Activate.ps1
```

**Eğer execution policy hatası alırsanız:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Alternatif (CMD):**
```cmd
cd C:\Users\Beyza\Desktop\findus\Kayip_esya_bulma_platformu
venv\Scripts\activate.bat
```

### 2. Paketleri Yükleyin

Virtual environment aktif olduktan sonra (komut satırında `(venv)` görünecek):

```powershell
pip install -r requirements.txt
```

**Not:** Bazı paketler (özellikle `mysqlclient`) Windows'ta sorun çıkarabilir. Bu durumda:

```powershell
pip install -r requirements.txt --no-deps
pip install Django djangorestframework django-cors-headers Pillow python-decouple
pip install pymongo pymilvus google-cloud-vision firebase-admin googlemaps
pip install opencv-python numpy scikit-learn celery redis
```

**MySQL için alternatif:**
```powershell
pip install PyMySQL
```

Sonra `settings.py`'de PyMySQL'i kullanmak için:
```python
import pymysql
pymysql.install_as_MySQLdb()
```

### 3. .env Dosyası Oluşturun

`env.example` dosyasını kopyalayın:
```powershell
Copy-Item env.example .env
```

`.env` dosyasını düzenleyip API anahtarlarınızı ekleyin.

### 4. Veritabanlarını Hazırlayın

#### MySQL (Konum verileri için)
```sql
CREATE DATABASE findus_locations CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### MongoDB (Mesajlaşma için)
MongoDB'nin çalıştığından emin olun:
```powershell
# MongoDB servisini başlat
net start MongoDB
```

#### Milvus (Görüntü eşleştirme için)
Docker ile başlatın:
```powershell
docker-compose -f milvus.docker-compose.yml up -d
```

### 5. Migration'ları Çalıştırın

```powershell
python manage.py makemigrations
python manage.py migrate
```

### 6. Sunucuyu Başlatın

```powershell
python manage.py runserver
```

## Hala Sorun Yaşıyorsanız

1. **Python versiyonunu kontrol edin:**
   ```powershell
   python --version
   ```
   Python 3.8+ olmalı.

2. **Virtual environment'ı yeniden oluşturun:**
   ```powershell
   Remove-Item -Recurse -Force venv
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Django'nun yüklü olup olmadığını kontrol edin:**
   ```powershell
   python -c "import django; print(django.get_version())"
   ```

