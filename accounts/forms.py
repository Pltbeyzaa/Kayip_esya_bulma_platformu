from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import User, ItemPost


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control register-input',
            'placeholder': 'E-posta adresinizi girin',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control register-input',
            'placeholder': 'Adınız',
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control register-input',
            'placeholder': 'Soyadınız',
            'autocomplete': 'family-name'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control register-input',
            'placeholder': 'Telefon numaranız (opsiyonel)',
            'autocomplete': 'tel'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control register-input',
            'placeholder': 'Kullanıcı adınız',
            'autocomplete': 'username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control register-input',
            'placeholder': 'Şifreniz',
            'autocomplete': 'new-password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control register-input',
            'placeholder': 'Şifrenizi tekrar girin',
            'autocomplete': 'new-password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Bu e-posta adresi zaten kullanılıyor.')
        return email


class UserLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control login-input',
            'placeholder': 'E-posta adresinizi girin',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control login-input',
            'placeholder': 'Şifrenizi girin',
            'autocomplete': 'current-password'
        })
    )

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise forms.ValidationError('E-posta veya şifre hatalı.')
            if not user.is_active:
                raise forms.ValidationError('Hesabınız aktif değil.')
        return self.cleaned_data


class LostItemPostForm(forms.ModelForm):
    """Kayıp eşya ilanı formu"""
    
    # Türk şehirleri - 81 il
    TURKISH_CITIES = [
        ('', 'Şehir Seçiniz'),
        ('Adana', 'Adana'),
        ('Adıyaman', 'Adıyaman'),
        ('Afyonkarahisar', 'Afyonkarahisar'),
        ('Ağrı', 'Ağrı'),
        ('Amasya', 'Amasya'),
        ('Ankara', 'Ankara'),
        ('Antalya', 'Antalya'),
        ('Artvin', 'Artvin'),
        ('Aydın', 'Aydın'),
        ('Balıkesir', 'Balıkesir'),
        ('Bilecik', 'Bilecik'),
        ('Bingöl', 'Bingöl'),
        ('Bitlis', 'Bitlis'),
        ('Bolu', 'Bolu'),
        ('Burdur', 'Burdur'),
        ('Bursa', 'Bursa'),
        ('Çanakkale', 'Çanakkale'),
        ('Çankırı', 'Çankırı'),
        ('Çorum', 'Çorum'),
        ('Denizli', 'Denizli'),
        ('Diyarbakır', 'Diyarbakır'),
        ('Edirne', 'Edirne'),
        ('Elazığ', 'Elazığ'),
        ('Erzincan', 'Erzincan'),
        ('Erzurum', 'Erzurum'),
        ('Eskişehir', 'Eskişehir'),
        ('Gaziantep', 'Gaziantep'),
        ('Giresun', 'Giresun'),
        ('Gümüşhane', 'Gümüşhane'),
        ('Hakkari', 'Hakkari'),
        ('Hatay', 'Hatay'),
        ('Isparta', 'Isparta'),
        ('Mersin', 'Mersin'),
        ('İstanbul', 'İstanbul'),
        ('İzmir', 'İzmir'),
        ('Kars', 'Kars'),
        ('Kastamonu', 'Kastamonu'),
        ('Kayseri', 'Kayseri'),
        ('Kırklareli', 'Kırklareli'),
        ('Kırşehir', 'Kırşehir'),
        ('Kocaeli', 'Kocaeli'),
        ('Konya', 'Konya'),
        ('Kütahya', 'Kütahya'),
        ('Malatya', 'Malatya'),
        ('Manisa', 'Manisa'),
        ('Kahramanmaraş', 'Kahramanmaraş'),
        ('Mardin', 'Mardin'),
        ('Muğla', 'Muğla'),
        ('Muş', 'Muş'),
        ('Nevşehir', 'Nevşehir'),
        ('Niğde', 'Niğde'),
        ('Ordu', 'Ordu'),
        ('Rize', 'Rize'),
        ('Sakarya', 'Sakarya'),
        ('Samsun', 'Samsun'),
        ('Siirt', 'Siirt'),
        ('Sinop', 'Sinop'),
        ('Sivas', 'Sivas'),
        ('Tekirdağ', 'Tekirdağ'),
        ('Tokat', 'Tokat'),
        ('Trabzon', 'Trabzon'),
        ('Tunceli', 'Tunceli'),
        ('Şanlıurfa', 'Şanlıurfa'),
        ('Uşak', 'Uşak'),
        ('Van', 'Van'),
        ('Yozgat', 'Yozgat'),
        ('Zonguldak', 'Zonguldak'),
        ('Aksaray', 'Aksaray'),
        ('Bayburt', 'Bayburt'),
        ('Karaman', 'Karaman'),
        ('Kırıkkale', 'Kırıkkale'),
        ('Batman', 'Batman'),
        ('Şırnak', 'Şırnak'),
        ('Bartın', 'Bartın'),
        ('Ardahan', 'Ardahan'),
        ('Iğdır', 'Iğdır'),
        ('Yalova', 'Yalova'),
        ('Karabük', 'Karabük'),
        ('Kilis', 'Kilis'),
        ('Osmaniye', 'Osmaniye'),
        ('Düzce', 'Düzce'),
    ]
    
    city = forms.ChoiceField(
        choices=TURKISH_CITIES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'citySelect'
        }),
        label='Şehir'
    )

    neighborhood = forms.CharField(
        required=False,
        label='Mahalle',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mahalle adı (örn: Barbaros Mahallesi)'
        })
    )
    
    # İlan kategorileri (DB yerine açıklamaya işlenecek)
    MAIN_CATEGORIES = [
        ('', 'Kategori Seçiniz'),
        ('electronics', 'Elektronik'),
        ('accessories', 'Aksesuar'),
        ('documents', 'Belge/Kimlik'),
        ('clothing', 'Giyim'),
        ('animals', 'Hayvan'),
        ('others', 'Diğer')
    ]

    main_category = forms.ChoiceField(
        choices=MAIN_CATEGORIES,
        required=False,
        label='Kategori',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'mainCategory'})
    )

    sub_category = forms.CharField(
        required=False,
        label='Alt Kategori',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Telefon, Cüzdan, Gözlük'})
    )

    brand = forms.CharField(
        required=False,
        label='Marka',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Apple, Samsung, Ray-Ban'})
    )

    color = forms.CharField(
        required=False,
        label='Renk',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Siyah, Mavi'})
    )

    class Meta:
        model = ItemPost
        fields = ['title', 'description', 'city', 'district', 'location', 'contact_phone', 
                  'contact_email', 'image', 'is_urgent']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Örn: Kayıp Telefon - İzmir Konak'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Eşyanız hakkında detaylı bilgi veriniz...'
            }),
            'district': forms.Select(attrs={
                'class': 'form-select',
                'id': 'districtSelect',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Örn: Konak Meydanı, Kadıköy Sahil'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '05XX XXX XX XX'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'E-posta adresiniz (opsiyonel)'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_urgent': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'title': 'Başlık',
            'description': 'Açıklama',
            'district': 'İlçe',
            'location': 'Konum',
            'contact_phone': 'İletişim Telefonu',
            'contact_email': 'İletişim E-posta',
            'image': 'Eşya Fotoğrafı',
            'is_urgent': 'Acil İlan'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['district'].required = False
        self.fields['contact_email'].required = False
        self.fields['image'].required = False

    def clean(self):
        cleaned = super().clean()
        # Kategori bilgilerini açıklamanın sonuna ekleyelim (şimdilik DB alanı eklemeden)
        parts = []
        if cleaned.get('main_category'):
            parts.append(f"Kategori: {dict(self.MAIN_CATEGORIES).get(cleaned['main_category'], '')}")
        if cleaned.get('sub_category'):
            parts.append(f"Alt Kategori: {cleaned['sub_category']}")
        if cleaned.get('brand'):
            parts.append(f"Marka: {cleaned['brand']}")
        if cleaned.get('color'):
            parts.append(f"Renk: {cleaned['color']}")
        if cleaned.get('neighborhood'):
            parts.append(f"Mahalle: {cleaned['neighborhood']}")

        if parts:
            desc = cleaned.get('description') or ''
            # Eski formatta eklenmiş kategori bloğunu (tek satır, | ile ayrılmış) temizle
            marker = "\n\n[Kategori:"
            idx = desc.find(marker)
            if idx != -1:
                desc = desc[:idx].rstrip()

            # Yeni format: her özellik alt alta görünsün
            extra = "\n\n[" + "\n".join(parts) + "]"
            cleaned['description'] = (desc + extra).strip()
        return cleaned


class MissingChildPostForm(forms.ModelForm):
    """Kayıp çocuk ilanı formu"""
    
    # Türk şehirleri - LostItemPostForm'dan kopyala
    TURKISH_CITIES = LostItemPostForm.TURKISH_CITIES
    
    city = forms.ChoiceField(
        choices=TURKISH_CITIES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'citySelect'
        }),
        label='Şehir'
    )
    
    class Meta:
        model = ItemPost
        fields = [
            'title', 'description', 'city', 'district', 'location', 
            'contact_phone', 'contact_email', 'image', 'is_urgent',
            'child_name', 'child_age', 'child_gender', 'child_height', 
            'child_weight', 'child_hair_color', 'child_eye_color',
            'child_physical_features', 'missing_date', 'last_seen_location',
            'last_seen_clothing'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Örn: Kayıp Çocuk - İzmir Konak'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Çocuk hakkında detaylı bilgi veriniz...'
            }),
            'district': forms.Select(attrs={
                'class': 'form-select',
                'id': 'districtSelect',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Örn: Konak Meydanı, Kadıköy Sahil'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '05XX XXX XX XX'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'E-posta adresiniz (opsiyonel)'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_urgent': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'child_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Çocuğun adı'
            }),
            'child_age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Yaş',
                'min': 0,
                'max': 18
            }),
            'child_gender': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[('', 'Seçiniz'), ('erkek', 'Erkek'), ('kız', 'Kız')]),
            'child_height': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Boy (cm)',
                'min': 0,
                'max': 200
            }),
            'child_weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kilo (kg)',
                'min': 0,
                'max': 100
            }),
            'child_hair_color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Örn: Siyah, Sarı, Kahverengi'
            }),
            'child_eye_color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Örn: Mavi, Yeşil, Kahverengi'
            }),
            'child_physical_features': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Örn: Yüzünde yara izi var, sol kolu kırık, vb.'
            }),
            'missing_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'last_seen_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Son görüldüğü yer'
            }),
            'last_seen_clothing': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Son görüldüğünde üzerindeki kıyafetler'
            }),
        }
        labels = {
            'title': 'Başlık',
            'description': 'Açıklama',
            'district': 'İlçe',
            'location': 'Konum',
            'contact_phone': 'İletişim Telefonu',
            'contact_email': 'İletişim E-posta',
            'image': 'Çocuğun Fotoğrafı',
            'is_urgent': 'Acil İlan',
            'child_name': 'Çocuğun Adı',
            'child_age': 'Yaş',
            'child_gender': 'Cinsiyet',
            'child_height': 'Boy (cm)',
            'child_weight': 'Kilo (kg)',
            'child_hair_color': 'Saç Rengi',
            'child_eye_color': 'Göz Rengi',
            'child_physical_features': 'Fiziksel Özellikler',
            'missing_date': 'Kaybolma Tarihi',
            'last_seen_location': 'Son Görüldüğü Yer',
            'last_seen_clothing': 'Son Görüldüğünde Üzerindeki Kıyafetler',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['district'].required = False
        self.fields['contact_email'].required = False
        self.fields['image'].required = True  # Çocuk ilanları için fotoğraf zorunlu
        self.fields['child_name'].required = True
        self.fields['child_age'].required = True
        self.fields['child_gender'].required = True
        self.fields['missing_date'].required = True
        self.fields['child_physical_features'].required = False  # Fiziksel özellikler opsiyonel
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.is_missing_child = True
        instance.post_type = 'lost'  # Kayıp çocuk ilanları her zaman 'lost' tipinde
        if commit:
            instance.save()
        return instance


class FoundChildPostForm(forms.ModelForm):
    """Bulunan çocuk ilanı formu"""
    
    # Türk şehirleri - LostItemPostForm'dan kopyala
    TURKISH_CITIES = LostItemPostForm.TURKISH_CITIES
    
    city = forms.ChoiceField(
        choices=TURKISH_CITIES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'citySelect'
        }),
        label='Şehir'
    )
    
    class Meta:
        model = ItemPost
        fields = [
            'title', 'description', 'city', 'district', 'location', 
            'contact_phone', 'contact_email', 'image', 'is_urgent',
            'child_name', 'child_age', 'child_gender', 
            'child_hair_color', 'child_eye_color',
            'child_physical_features', 'missing_date', 'last_seen_location',
            'last_seen_clothing'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Örn: Bulunan Çocuk - İzmir Konak'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Çocuk hakkında detaylı bilgi veriniz...'
            }),
            'district': forms.Select(attrs={
                'class': 'form-select',
                'id': 'districtSelect',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Örn: Konak Meydanı, Kadıköy Sahil'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '05XX XXX XX XX'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'E-posta adresiniz (opsiyonel)'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_urgent': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'child_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Çocuğun adı (biliniyorsa)'
            }),
            'child_age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Yaş (tahmini)',
                'min': 0,
                'max': 18
            }),
            'child_gender': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[('', 'Seçiniz'), ('erkek', 'Erkek'), ('kız', 'Kız')]),
            'child_hair_color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Örn: Siyah, Sarı, Kahverengi'
            }),
            'child_eye_color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Örn: Mavi, Yeşil, Kahverengi'
            }),
            'child_physical_features': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Örn: Yüzünde yara izi var, sol kolu kırık, vb.'
            }),
            'missing_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'last_seen_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Çocuğun bulunduğu yer'
            }),
            'last_seen_clothing': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Çocuğun üzerindeki kıyafetler'
            }),
        }
        labels = {
            'title': 'Başlık',
            'description': 'Açıklama',
            'district': 'İlçe',
            'location': 'Konum',
            'contact_phone': 'İletişim Telefonu',
            'contact_email': 'İletişim E-posta',
            'image': 'Çocuğun Fotoğrafı',
            'is_urgent': 'Acil İlan',
            'child_name': 'Çocuğun Adı',
            'child_age': 'Yaş (Tahmini)',
            'child_gender': 'Cinsiyet',
            'child_hair_color': 'Saç Rengi',
            'child_eye_color': 'Göz Rengi',
            'child_physical_features': 'Fiziksel Özellikler',
            'missing_date': 'Bulunma Tarihi',
            'last_seen_location': 'Bulunduğu Yer',
            'last_seen_clothing': 'Üzerindeki Kıyafetler',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['district'].required = False
        self.fields['contact_email'].required = False
        self.fields['image'].required = True  # Çocuk ilanları için fotoğraf zorunlu
        self.fields['child_name'].required = False  # Bulunan çocuk için ad bilinmeyebilir
        self.fields['child_age'].required = False  # Tahmini olabilir
        self.fields['child_gender'].required = True
        self.fields['missing_date'].required = True  # Bulunma tarihi
        self.fields['child_physical_features'].required = False  # Fiziksel özellikler opsiyonel
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.is_missing_child = True
        instance.post_type = 'found'  # Bulunan çocuk ilanları 'found' tipinde
        if commit:
            instance.save()
        return instance