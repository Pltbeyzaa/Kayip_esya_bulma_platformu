# Kayıp Eşya Bulma Platformu

Bu proje, kayıp eşyaları bulma ve bulunan eşyaları sahiplerine ulaştırma amacıyla geliştirilmiş gelişmiş bir web platformudur.

## 🚀 Özellikler

### Temel Özellikler
- ✅ Kullanıcı kayıt ve giriş sistemi
- ✅ Modern ve responsive tasarım
- ✅ Güvenli şifre doğrulama
- ✅ Profil yönetimi
- ✅ Bootstrap 5 ile modern UI
- ✅ JavaScript ile gelişmiş form validasyonu

### Gelişmiş Özellikler
- 🔍 **Görüntü Eşleştirme**: Google Cloud Vision API ile görüntü analizi
- 🗺️ **Konum Tabanlı Arama**: Google Maps API ile konum servisleri
- 💬 **Anlık Mesajlaşma**: Firebase Cloud Messaging ile gerçek zamanlı iletişim
- 🎯 **Vektör Veritabanı**: Milvus ile görüntü vektörleri
- 📍 **MongoDB Entegrasyonu**: Konum ve mesajlaşma verileri
- 🔔 **Bildirim Sistemi**: FCM ile push bildirimleri

## 🛠️ Teknolojiler

### Backend
- **Django 4.2.7** - Python web framework
- **Django REST Framework** - API geliştirme
- **SQLite** - Ana veritabanı
- **MongoDB** - Konum ve mesajlaşma verileri
- **Milvus** - Vektör veritabanı (görüntü eşleştirme)
- **Redis** - Cache ve Celery broker
- **Celery** - Asenkron görevler

### Frontend
- **HTML5** - Yapısal markup
- **CSS3** - Styling ve animasyonlar
- **JavaScript (ES6+)** - İnteraktif özellikler
- **Bootstrap 5** - Responsive UI framework
- **Font Awesome** - İkonlar

### Dış Servisler
- **Google Cloud Vision API** - Görüntü analizi
- **Google Maps API** - Konum servisleri
- **Firebase Cloud Messaging** - Push bildirimleri
- **Firebase Realtime Database** - Anlık mesajlaşma

## 📦 Kurulum

### Gereksinimler
- Python 3.8+
- pip (Python paket yöneticisi)
- MongoDB (konum ve mesajlaşma için)
- Milvus (vektör veritabanı için)
- Redis (Celery için)

### Adımlar

1. **Projeyi klonlayın:**
```bash
git clone <repository-url>
cd Kayip_esya_bulma_platformu
```

2. **Sanal ortam oluşturun:**
```bash
python -m venv venv
```

3. **Sanal ortamı aktifleştirin:**
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

4. **Gerekli paketleri yükleyin:**
```bash
pip install -r requirements.txt
```

5. **Environment variables ayarlayın:**
```bash
cp env.example .env
# .env dosyasını düzenleyin ve API anahtarlarını ekleyin
```

6. **Veritabanı migrasyonlarını çalıştırın:**
```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Süper kullanıcı oluşturun:**
```bash
python manage.py createsuperuser
```

8. **Redis'i başlatın:**
```bash
# Windows (Redis for Windows)
redis-server

# macOS (Homebrew)
brew services start redis

# Linux
sudo systemctl start redis
```

9. **Celery worker'ı başlatın:**
```bash
celery -A kayip_esya worker --loglevel=info
```

10. **Sunucuyu başlatın:**
```bash
python manage.py runserver
```

11. **Tarayıcıda açın:**
```
http://127.0.0.1:8000/
```

## Proje Yapısı

```
Kayip_esya_bulma_platformu/
├── kayip_esya/              # Ana Django projesi
│   ├── __init__.py
│   ├── settings.py          # Proje ayarları
│   ├── urls.py              # Ana URL yapılandırması
│   ├── wsgi.py              # WSGI yapılandırması
│   └── asgi.py              # ASGI yapılandırması
├── accounts/                # Kullanıcı yönetimi uygulaması
│   ├── models.py            # Kullanıcı modeli
│   ├── views.py             # Görünümler
│   ├── forms.py             # Form sınıfları
│   ├── urls.py              # URL yapılandırması
│   └── admin.py             # Admin paneli
├── templates/               # HTML şablonları
│   ├── base.html            # Ana şablon
│   └── accounts/            # Hesap şablonları
│       ├── home.html        # Ana sayfa
│       ├── login.html       # Giriş sayfası
│       ├── register.html    # Kayıt sayfası
│       └── profile.html     # Profil sayfası
├── static/                  # Statik dosyalar
│   ├── css/
│   │   └── style.css        # Özel CSS stilleri
│   └── js/
│       └── main.js          # JavaScript işlevleri
├── requirements.txt         # Python bağımlılıkları
├── manage.py               # Django yönetim scripti
└── README.md               # Bu dosya
```

## Kullanım

### Ana Sayfa
- Platform hakkında bilgi
- Giriş/Kayıt butonları (giriş yapmamış kullanıcılar için)
- Platform özelliklerini tanıtan kartlar

### Kayıt Ol
- Ad, soyad, kullanıcı adı, e-posta, telefon numarası
- Güvenli şifre oluşturma
- Şifre güçlülük göstergesi
- Gerçek zamanlı form validasyonu

### Giriş Yap
- E-posta ve şifre ile giriş
- "Beni hatırla" seçeneği
- Form validasyonu

### Profil
- Kullanıcı bilgilerini görüntüleme
- İstatistikler (gelecekte eklenecek)
- Profil fotoğrafı (gelecekte eklenecek)

## Geliştirme

### Yeni Özellik Ekleme
1. Yeni model/views/forms oluşturun
2. URL yapılandırmasını güncelleyin
3. Template dosyalarını oluşturun
4. CSS/JS dosyalarını güncelleyin
5. Test edin

### Veritabanı Değişiklikleri
```bash
python manage.py makemigrations
python manage.py migrate
```

### Statik Dosyalar
```bash
python manage.py collectstatic
```

## Güvenlik

- CSRF koruması aktif
- Şifre hash'leme
- Form validasyonu
- XSS koruması
- Güvenli cookie ayarları

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## İletişim

Proje hakkında sorularınız için issue açabilirsiniz.

---

**Not:** Bu proje geliştirme aşamasındadır. Üretim ortamında kullanmadan önce güvenlik ayarlarını gözden geçirin.
