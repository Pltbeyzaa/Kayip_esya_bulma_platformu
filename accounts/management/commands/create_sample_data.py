from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import ItemPost

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data with proper Turkish characters'

    def handle(self, *args, **options):
        # Create test user if not exists
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'phone_number': '05551234567'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Test user created'))
        else:
            self.stdout.write(self.style.WARNING('Test user already exists'))

        # Clear existing sample posts
        ItemPost.objects.filter(user=user).delete()

        # Create sample posts with proper Turkish characters
        sample_posts = [
            {
                'title': 'Bulunan Saat - Adana Seyhan',
                'description': 'Merkez parkta saat buldum. Sahibi gelip alabilir.',
                'post_type': 'found',
                'location': 'Adana Merkez Park',
                'city': 'Adana',
                'district': 'Seyhan',
                'contact_phone': '05551234567',
                'contact_email': 'test@example.com',
                'image': 'item_images/watch_found.svg',
                'is_urgent': False,
            },
            {
                'title': 'Kayıp Gözlük - Antalya Muratpaşa',
                'description': 'Güneş gözlüğümü plajda kaybettim. Ray-Ban marka.',
                'post_type': 'lost',
                'location': 'Antalya Plajı',
                'city': 'Antalya',
                'district': 'Muratpaşa',
                'contact_phone': '05551234567',
                'contact_email': 'test@example.com',
                'image': 'item_images/glasses_lost.svg',
                'is_urgent': False,
            },
            {
                'title': 'Bulunan Çanta - Bursa Osmangazi',
                'description': 'Osmangazi metroda siyah çanta buldum. İçinde kitaplar var.',
                'post_type': 'found',
                'location': 'Osmangazi Metro İstasyonu',
                'city': 'Bursa',
                'district': 'Osmangazi',
                'contact_phone': '05551234567',
                'contact_email': 'test@example.com',
                'image': 'item_images/bag_found.svg',
                'is_urgent': False,
            },
            {
                'title': 'Kayıp Cüzdan - İstanbul Kadıköy',
                'description': 'Kahverengi deri cüzdanımı kaybettim. İçinde kimlik ve kartlar var.',
                'post_type': 'lost',
                'location': 'Kadıköy Çarşı',
                'city': 'İstanbul',
                'district': 'Kadıköy',
                'contact_phone': '05551234567',
                'contact_email': 'test@example.com',
                'image': 'item_images/wallet_lost.svg',
                'is_urgent': True,
            },
            {
                'title': 'Bulunan Anahtar - Ankara Çankaya',
                'description': 'Çankaya\'da anahtar buldum. Sahibi arıyorsa iletişime geçsin.',
                'post_type': 'found',
                'location': 'Çankaya Metro',
                'city': 'Ankara',
                'district': 'Çankaya',
                'contact_phone': '05551234567',
                'contact_email': 'test@example.com',
                'image': 'item_images/key_found.svg',
                'is_urgent': False,
            },
            {
                'title': 'Kayıp Telefon - İzmir Konak',
                'description': 'iPhone telefonumu kaybettim. Son konum Konak Meydanı.',
                'post_type': 'lost',
                'location': 'Konak Meydanı',
                'city': 'İzmir',
                'district': 'Konak',
                'contact_phone': '05551234567',
                'contact_email': 'test@example.com',
                'image': 'item_images/phone_lost.svg',
                'is_urgent': True,
            },
            {
                'title': 'Bulunan Kulaklık - Eskişehir Odunpazarı',
                'description': 'Tramvayda kablosuz kulaklık buldum, marka Xiaomi.',
                'post_type': 'found',
                'location': 'Odunpazarı Tramvay Durağı',
                'city': 'Eskişehir',
                'district': 'Odunpazarı',
                'contact_phone': '05551234567',
                'contact_email': 'test@example.com',
                'image': 'item_images/earbuds_found.svg',
                'is_urgent': False,
            },
            {
                'title': 'Kayıp Laptop - Ankara Bilkent',
                'description': 'Gri renkli laptop çantası içinde Dell bilgisayar kayıp.',
                'post_type': 'lost',
                'location': 'Bilkent Kütüphane',
                'city': 'Ankara',
                'district': 'Çankaya',
                'contact_phone': '05551234567',
                'contact_email': 'test@example.com',
                'image': 'item_images/laptop_lost.svg',
                'is_urgent': True,
            },
            {
                'title': 'Bulunan Yüzük - İstanbul Beşiktaş',
                'description': 'Sahil yolunda altın renk yüzük buldum.',
                'post_type': 'found',
                'location': 'Beşiktaş Sahil',
                'city': 'İstanbul',
                'district': 'Beşiktaş',
                'contact_phone': '05551234567',
                'contact_email': 'test@example.com',
                'image': 'item_images/ring_found.svg',
                'is_urgent': False,
            },
            {
                'title': 'Kayıp Pasaport - Trabzon Ortahisar',
                'description': 'Mavi kapaklı pasaportumu kaybettim, bulan lütfen iletişime geçsin.',
                'post_type': 'lost',
                'location': 'Ortahisar Meydan',
                'city': 'Trabzon',
                'district': 'Ortahisar',
                'contact_phone': '05551234567',
                'contact_email': 'test@example.com',
                'image': 'item_images/passport_lost.svg',
                'is_urgent': True,
            }
        ]

        for post_data in sample_posts:
            ItemPost.objects.create(
                user=user,
                **post_data
            )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(sample_posts)} sample posts')
        )
