# Turkish Character Encoding Fix

Bu dosya, Kayıp Eşya Bulma Platformu'ndaki Türkçe karakter kodlama sorunlarının çözümünü açıklar.

## Sorun

Web uygulamasında Türkçe karakterler (ç, ğ, ı, ö, ş, ü, Ç, Ğ, İ, Ö, Ş, Ü) bozuk görünüyor.

## Çözüm Adımları

### 1. Django Ayarları (settings.py)

```python
# Internationalization
LANGUAGE_CODE = 'tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True

# UTF-8 Encoding
DEFAULT_CHARSET = 'utf-8'
FILE_CHARSET = 'utf-8'
```

### 2. HTML Meta Tags (base.html)

```html
<meta charset="UTF-8">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
```

### 3. Veritabanı Kontrolü

```bash
# Veritabanı kodlamasını kontrol et
python manage.py check_encoding

# Örnek veri oluştur
python manage.py create_sample_data
```

### 4. Test Dosyaları

- `test_turkish_display.html` - Tarayıcıda Türkçe karakter testi
- `test_turkish_chars.py` - Python'da Türkçe karakter testi
- `run_sample_data.py` - Örnek veri oluşturma scripti

### 5. Sunucu Çalıştırma

```bash
# Geliştirme sunucusunu başlat
python run_server.py

# Veya doğrudan Django ile
python manage.py runserver
```

## Test Etme

1. **Tarayıcı Testi**: `test_turkish_display.html` dosyasını tarayıcıda açın
2. **Veritabanı Testi**: `python test_turkish_chars.py` komutunu çalıştırın
3. **Web Uygulaması**: Ana sayfada Türkçe karakterlerin doğru göründüğünü kontrol edin

## Beklenen Sonuçlar

- ✅ "Kayıp Gözlük - Antalya Muratpaşa" (doğru görünüm)
- ✅ "Güneş gözlüğümü plajda kaybettim" (doğru görünüm)
- ✅ "Çankaya'da anahtar buldum" (doğru görünüm)
- ✅ "İstanbul Kadıköy" (doğru görünüm)

## Sorun Giderme

### Eğer karakterler hala bozuk görünüyorsa:

1. **Tarayıcı ayarlarını kontrol edin**:
   - Encoding: UTF-8
   - Language: Turkish (tr)

2. **Dosya kodlamasını kontrol edin**:
   ```bash
   file -bi templates/accounts/home.html
   ```

3. **Veritabanını yeniden oluşturun**:
   ```bash
   rm db.sqlite3
   python manage.py migrate
   python manage.py create_sample_data
   ```

## Ek Notlar

- Tüm dosyalar UTF-8 kodlamasında kaydedilmelidir
- IDE/Editör UTF-8 kodlamasını desteklemelidir
- Sunucu ortamında da UTF-8 kodlaması aktif olmalıdır
