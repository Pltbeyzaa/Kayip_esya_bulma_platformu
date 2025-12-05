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
            extra = "\n\n[" + " | ".join(parts) + "]"
            cleaned['description'] = (desc + extra).strip()
        return cleaned
