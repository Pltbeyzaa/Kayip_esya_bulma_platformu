from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import User, ItemPost


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'E-posta adresinizi girin'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Adınız'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Soyadınız'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Telefon numaranız (opsiyonel)'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Kullanıcı adınız'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Şifreniz'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Şifrenizi tekrar girin'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Bu e-posta adresi zaten kullanılıyor.')
        return email


class UserLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'E-posta adresinizi girin'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Şifrenizi girin'
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
    
    # Türk şehirleri
    TURKISH_CITIES = [
        ('', 'Şehir Seçiniz'),
        ('İstanbul', 'İstanbul'),
        ('Ankara', 'Ankara'),
        ('İzmir', 'İzmir'),
        ('Bursa', 'Bursa'),
        ('Antalya', 'Antalya'),
        ('Adana', 'Adana'),
        ('Konya', 'Konya'),
        ('Gaziantep', 'Gaziantep'),
        ('Şanlıurfa', 'Şanlıurfa'),
        ('Kocaeli', 'Kocaeli'),
        ('Mersin', 'Mersin'),
        ('Diyarbakır', 'Diyarbakır'),
        ('Hatay', 'Hatay'),
        ('Manisa', 'Manisa'),
        ('Kayseri', 'Kayseri'),
        ('Samsun', 'Samsun'),
        ('Balıkesir', 'Balıkesir'),
        ('Kahramanmaraş', 'Kahramanmaraş'),
        ('Van', 'Van'),
        ('Aydın', 'Aydın'),
        ('Tekirdağ', 'Tekirdağ'),
        ('Denizli', 'Denizli'),
        ('Malatya', 'Malatya'),
        ('Erzurum', 'Erzurum'),
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
            'district': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'İlçe (opsiyonel)'
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

        if parts:
            desc = cleaned.get('description') or ''
            extra = "\n\n[" + " | ".join(parts) + "]"
            cleaned['description'] = (desc + extra).strip()
        return cleaned
