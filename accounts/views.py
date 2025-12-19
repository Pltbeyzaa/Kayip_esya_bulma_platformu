from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.conf import settings
from django.views.decorators.http import require_POST
from django.db import models
from django.db.models import Q
import os
from typing import List, Dict
from .forms import UserRegistrationForm, UserLoginForm, LostItemPostForm, MissingChildPostForm, FoundChildPostForm
from .models import ItemPost
from .services import upsert_item_post_to_mongo
from image_matching.models import ImageVector, ImageMatch
from .constants import MATCH_NOTIFY_THRESHOLD
from .matching_service import MatchingService


def add_notification(request, title: str, message: str, level: str = "info") -> None:
    """
    Basit bildirim yapısı (session tabanlı).
    level: info | success | warning | danger
    """
    notif: List[Dict] = request.session.get('notifications', [])
    notif.append({
        'title': title,
        'message': message,
        'level': level,
    })
    request.session['notifications'] = notif


def _get_post_by_vector_cached(vec: ImageVector, post_type: str, exclude_user_id=None):
    filename = os.path.basename(vec.image_path)
    qs = ItemPost.objects.filter(
        image__icontains=filename,
        post_type=post_type,
        status="active",
    )
    if exclude_user_id:
        qs = qs.exclude(user_id=exclude_user_id)
    return qs.first()

def landing(request):
    """Landing sayfası - Giriş yapmayan kullanıcılar için"""
    # Oturum açmamış kullanıcılar için bulanık ilanlar göster (merak uyandırmak için)
    # Tüm aktif ilanları göster (testuser dahil)
    posts = (
        ItemPost.objects
        .filter(status='active')
        .select_related('user')
        .order_by('?')[:15]  # Rastgele 15 ilan
    )
    
    return render(request, 'accounts/home.html', {
        'show_landing': True,
        'blurred_posts': posts
    })


@login_required
def home(request):
    """Ana sayfa - İlan akışı (Sadece giriş yapmış kullanıcılar)"""
    posts = ItemPost.objects.filter(status='active').select_related('user')

    # Filtreler
    selected_type = request.GET.get('post_type', 'all')
    selected_city = request.GET.get('city', '').strip()
    query = request.GET.get('q', '').strip()
    child_filter = request.GET.get('child_filter', 'all')  # 'children' | 'animals' | 'others' | 'all'

    if selected_type in ['lost', 'found']:
        posts = posts.filter(post_type=selected_type)
    if selected_city:
        posts = posts.filter(city__iexact=selected_city)
    if query:
        posts = posts.filter(title__icontains=query) | posts.filter(description__icontains=query)

    # Çocuk / hayvan / diğer ilanlar filtresi
    if child_filter == 'children':
        posts = posts.filter(is_missing_child=True)
    elif child_filter == 'animals':
        # Sadece hayvan ilanlarını göster
        # Açıklamada "Kategori: Hayvan" veya "[Kategori: Hayvan" geçen ilanlar
        posts = posts.filter(
            is_missing_child=False
        ).filter(
            Q(description__icontains='Kategori: Hayvan') |
            Q(description__icontains='[Kategori: Hayvan')
        ).distinct()
    elif child_filter == 'others':
        # Çocuk ve hayvan ilanları hariç diğer tüm ilanlar
        posts = posts.filter(is_missing_child=False).exclude(description__icontains='Kategori: Hayvan')

    cities = (
        ItemPost.objects.exclude(city__isnull=True)
        .exclude(city__exact='')
        .values_list('city', flat=True)
        .distinct()
        .order_by('city')
    )

    # Sayfalama
    paginator = Paginator(posts, 12)  # Sayfa başına 12 ilan
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Her ilan için en yüksek eşleşme oranını hesapla
    post_matches = {}
    if page_obj:
        from image_matching.models import ImageVector, ImageMatch
        import os
        
        for post in page_obj:
            if post.image:
                try:
                    # İlanın vektörünü bul
                    filename = os.path.basename(post.image.name)
                    source_vec = ImageVector.objects.filter(image_path__icontains=filename).first()
                    
                    if source_vec:
                        # En yüksek eşleşme oranını bul
                        max_match = ImageMatch.objects.filter(
                            source_vector=source_vec
                        ).order_by('-similarity_score').first()
                        
                        if max_match:
                            post_matches[post.id] = round(float(max_match.similarity_score) * 100, 1)
                        else:
                            # Veritabanında eşleşme yoksa dinamik hesapla
                            try:
                                ms = MatchingService()
                                results = ms.find_matches(post)
                                if results:
                                    max_similarity = max(r['similarity'] for r in results)
                                    post_matches[post.id] = round(max_similarity * 100, 1)
                            except:
                                pass
                except Exception as e:
                    print(f"Eşleşme oranı hesaplama hatası (post {post.id}): {e}")

    # İstatistikler
    total_posts = ItemPost.objects.filter(status='active').exclude(user__username='testuser').count()
    lost_posts = ItemPost.objects.filter(status='active', post_type='lost').exclude(user__username='testuser').count()
    found_posts = ItemPost.objects.filter(status='active', post_type='found').exclude(user__username='testuser').count()
    missing_children = ItemPost.objects.filter(status='active', is_missing_child=True).exclude(user__username='testuser').count()

    context = {
        'page_obj': page_obj,
        'total_posts': total_posts,
        'lost_posts': lost_posts,
        'found_posts': found_posts,
        'missing_children': missing_children,
        'cities': cities,
        'selected_type': selected_type,
        'selected_city': selected_city,
        'query': query,
        'child_filter': child_filter,
        'post_matches': post_matches,  # İlan ID -> en yüksek eşleşme oranı
    }

    return render(request, 'accounts/home.html', context)


def register_view(request):
    """Kullanıcı kayıt sayfası"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        # KVKK ve Kullanım Şartları onay kontrolü
        agree_terms = request.POST.get('agree_terms')
        agree_privacy = request.POST.get('agree_privacy')
        
        if not agree_terms:
            messages.error(request, 'Kayıt olmak için kullanım şartlarını kabul etmelisiniz.')
            return render(request, 'accounts/register.html', {'form': form})
        
        if not agree_privacy:
            messages.error(request, 'Kayıt olmak için gizlilik politikasını kabul etmelisiniz.')
            return render(request, 'accounts/register.html', {'form': form})
        
        if form.is_valid():
            user = form.save()

            # Hoş geldiniz e-postası gönder
            try:
                if user.email:
                    send_mail(
                        subject='FindUs\'a Hoş Geldiniz',
                        message=(
                            f'Merhaba {user.first_name or user.username},\n\n'
                            'FindUs platformuna kayıt olduğunuz için teşekkür ederiz.\n'
                            'Artık kayıp ve bulunan eşyalar için ilan verebilir ve akıllı eşleştirme '
                            'sistemimizi kullanabilirsiniz.\n\n'
                            'Sevgiler,\n'
                            'FindUs Ekibi'
                        ),
                        from_email=getattr(settings, 'EMAIL_HOST_USER', None),
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
            except Exception as e:
                # Sunucu tarafında hata olsa bile kullanıcı akışı bozulmasın
                print(f'Hoş geldiniz e-postası gönderilemedi: {e}')

            login(request, user)
            messages.success(request, 'Kayıt başarılı! Hoş geldiniz.')
            return redirect('findus_info')
        else:
            messages.error(request, 'Kayıt sırasında bir hata oluştu.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Kullanıcı giriş sayfası"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            from django.contrib.auth import authenticate
            user = authenticate(username=email, password=password)
            if user:
                login(request, user)
                messages.success(request, 'Giriş başarılı!')
                return redirect('findus_info')
        else:
            messages.error(request, 'E-posta veya şifre hatalı.')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Kullanıcı çıkış"""
    logout(request)
    messages.info(request, 'Başarıyla çıkış yaptınız.')
    return redirect('landing')


@login_required
def profile_view(request):
    """Kullanıcı profil sayfası"""
    # Aktif ilanlar
    user_lost_posts = ItemPost.objects.filter(user=request.user, post_type='lost', status='active').order_by('-created_at')
    user_found_posts = ItemPost.objects.filter(user=request.user, post_type='found', status='active').order_by('-created_at')
    
    # Geçmiş ilanlar (resolved durumundaki)
    user_resolved_posts = ItemPost.objects.filter(user=request.user, status='resolved').order_by('-updated_at')

    # Başarılı eşleşmeleri hesapla (%70 ve üzeri)
    # Kullanıcının ilanlarının başka kullanıcıların ilanlarıyla yaptığı benzersiz eşleşmelerin toplam sayısı
    # Her benzersiz (kullanıcı ilanı, başka kullanıcı ilanı) çifti sadece 1 kez sayılır
    successful_matches_count = 0
    try:
        # Kullanıcının ImageVector'larını bul
        user_vectors = ImageVector.objects.filter(user=request.user)
        user_vector_ids = list(user_vectors.values_list('id', flat=True))
        
        if user_vector_ids:
            # Kullanıcının vector'larının kaynak veya hedef olduğu eşleşmeleri bul (%70 ve üzeri)
            matches = ImageMatch.objects.filter(
                models.Q(source_vector_id__in=user_vector_ids) | models.Q(target_vector_id__in=user_vector_ids),
                similarity_score__gte=MATCH_NOTIFY_THRESHOLD
            ).select_related('source_vector__user', 'target_vector__user')
            
            # Benzersiz eşleşmeleri say (kullanıcının ilanı - başka kullanıcının ilanı çiftleri)
            # Her benzersiz çift sadece 1 kez sayılır (A->B ve B->A aynı çift sayılır)
            unique_match_pairs = set()
            for match in matches:
                source_vec = match.source_vector
                target_vec = match.target_vector
                
                # Kullanıcının vector'ü hangisi?
                user_vec_id = None
                other_vec_id = None
                
                if source_vec.user_id == request.user.id and target_vec.user_id != request.user.id:
                    user_vec_id = source_vec.id
                    other_vec_id = target_vec.id
                elif target_vec.user_id == request.user.id and source_vec.user_id != request.user.id:
                    user_vec_id = target_vec.id
                    other_vec_id = source_vec.id
                
                # Eğer geçerli bir eşleşme varsa (kullanıcının ilanı ve başka kullanıcının ilanı)
                if user_vec_id and other_vec_id:
                    # Eşleşmeyi benzersiz olarak işaretle (sıralı tuple ile - A->B ve B->A aynı çift sayılır)
                    # Kullanıcının ilanını önce yazıyoruz ki tutarlı olsun
                    match_key = (str(user_vec_id), str(other_vec_id))
                    unique_match_pairs.add(match_key)
            
            successful_matches_count = len(unique_match_pairs)
    except Exception as e:
        print(f"Başarılı eşleşme hesaplama hatası: {e}")
        import traceback
        traceback.print_exc()

    context = {
        'user': request.user,
        'user_lost_posts': user_lost_posts,
        'user_found_posts': user_found_posts,
        'user_resolved_posts': user_resolved_posts,
        'lost_count': user_lost_posts.count(),
        'found_count': user_found_posts.count(),
        'successful_matches_count': successful_matches_count,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def create_lost_item_post(request):
    """Kayıp eşya ilanı oluşturma sayfası"""
    # DEBUG: API key kontrolü
    api_key = settings.GOOGLE_MAPS_API_KEY
    print(f"DEBUG: GOOGLE_MAPS_API_KEY değeri: {api_key}")
    print(f"DEBUG: GOOGLE_MAPS_API_KEY uzunluğu: {len(api_key) if api_key else 0}")
    
    if request.method == 'POST':
        form = LostItemPostForm(request.POST, request.FILES)
        if form.is_valid():
            item_post = form.save(commit=False)
            item_post.user = request.user
            item_post.post_type = 'lost'  # Kayıp eşya ilanı
            item_post.status = 'active'
            item_post.save()
            upsert_item_post_to_mongo(item_post)
            
            # Signal otomatik olarak eşleştirme yapacak (accounts/signals.py)
            # Eşleşmeler ImageMatch tablosuna kaydedilecek ve bildirimler otomatik görünecek
            messages.success(request, 'Kayıp eşya ilanınız başarıyla oluşturuldu! Eşleşmeler arka planda işleniyor...')
            
            return redirect('post_detail', post_id=item_post.id)
        else:
            messages.error(request, 'Lütfen formu kontrol ediniz.')
    else:
        form = LostItemPostForm()
    
    return render(request, 'accounts/create_lost_item.html', {
        'form': form,
        'google_maps_api_key': api_key
    })


@login_required
def create_found_item_post(request):
    """Bulunan eşya ilanı oluşturma sayfası"""
    api_key = settings.GOOGLE_MAPS_API_KEY
    if request.method == 'POST':
        form = LostItemPostForm(request.POST, request.FILES)
        if form.is_valid():
            item_post = form.save(commit=False)
            item_post.user = request.user
            item_post.post_type = 'found'  # Bulunan eşya ilanı
            item_post.status = 'active'
            item_post.save()
            upsert_item_post_to_mongo(item_post)
            
            # Signal otomatik olarak eşleştirme yapacak (accounts/signals.py)
            # Eşleşmeler ImageMatch tablosuna kaydedilecek ve bildirimler otomatik görünecek
            messages.success(request, 'Bulunan eşya ilanınız başarıyla oluşturuldu! Eşleşmeler arka planda işleniyor...')
            
            return redirect('post_detail', post_id=item_post.id)
        else:
            messages.error(request, 'Lütfen formu kontrol ediniz.')
    else:
        form = LostItemPostForm()

    return render(request, 'accounts/create_found_item.html', {
        'form': form,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    })


@login_required
def create_missing_child_post(request):
    """Kayıp çocuk ilanı oluşturma sayfası"""
    api_key = settings.GOOGLE_MAPS_API_KEY
    
    if request.method == 'POST':
        form = MissingChildPostForm(request.POST, request.FILES)
        if form.is_valid():
            item_post = form.save(commit=False)
            item_post.user = request.user
            item_post.post_type = 'lost'  # Kayıp çocuk ilanları her zaman 'lost'
            item_post.status = 'active'
            item_post.is_missing_child = True
            item_post.save()
            upsert_item_post_to_mongo(item_post)
            
            # Signal otomatik olarak eşleştirme yapacak (accounts/signals.py)
            # Eşleşmeler ImageMatch tablosuna kaydedilecek ve bildirimler otomatik görünecek
            messages.success(request, 'Kayıp çocuk ilanınız başarıyla oluşturuldu! Eşleşmeler arka planda işleniyor...')
            
            return redirect('post_detail', post_id=item_post.id)
        else:
            messages.error(request, 'Lütfen formu kontrol ediniz.')
    else:
        form = MissingChildPostForm()
    
    return render(request, 'accounts/create_missing_child.html', {
        'form': form,
        'google_maps_api_key': api_key
    })


@login_required
def create_found_child_post(request):
    """Bulunan çocuk ilanı oluşturma sayfası"""
    api_key = settings.GOOGLE_MAPS_API_KEY
    
    if request.method == 'POST':
        form = FoundChildPostForm(request.POST, request.FILES)
        if form.is_valid():
            item_post = form.save(commit=False)
            item_post.user = request.user
            item_post.post_type = 'found'  # Bulunan çocuk ilanları 'found' tipinde
            item_post.status = 'active'
            item_post.is_missing_child = True
            item_post.save()
            upsert_item_post_to_mongo(item_post)
            
            # Signal otomatik olarak eşleştirme yapacak (accounts/signals.py)
            # Eşleşmeler ImageMatch tablosuna kaydedilecek ve bildirimler otomatik görünecek
            messages.success(request, 'Bulunan çocuk ilanınız başarıyla oluşturuldu! Eşleşmeler arka planda işleniyor...')
            
            return redirect('post_detail', post_id=item_post.id)
        else:
            messages.error(request, 'Lütfen formu kontrol ediniz.')
    else:
        form = FoundChildPostForm()
    
    return render(request, 'accounts/create_found_child.html', {
        'form': form,
        'google_maps_api_key': api_key
    })


@login_required
def create_lost_animal_post(request):
    """Kayıp hayvan ilanı oluşturma sayfası"""
    api_key = settings.GOOGLE_MAPS_API_KEY
    if request.method == 'POST':
        form = LostItemPostForm(request.POST, request.FILES)
        if form.is_valid():
            item_post = form.save(commit=False)
            item_post.user = request.user
            item_post.post_type = 'lost'  # Kayıp hayvan ilanı
            item_post.status = 'active'
            item_post.save()
            upsert_item_post_to_mongo(item_post)
            
            # Signal otomatik olarak eşleştirme yapacak (accounts/signals.py)
            # Eşleşmeler ImageMatch tablosuna kaydedilecek ve bildirimler otomatik görünecek
            messages.success(request, 'Kayıp hayvan ilanınız başarıyla oluşturuldu! Eşleşmeler arka planda işleniyor...')
            
            return redirect('post_detail', post_id=item_post.id)
        else:
            messages.error(request, 'Lütfen formu kontrol ediniz.')
    else:
        form = LostItemPostForm(initial={'main_category': 'animals'})
    
    return render(request, 'accounts/create_lost_item.html', {
        'form': form,
        'google_maps_api_key': api_key,
        'is_animal': True  # Hayvan ilanı için flag
    })


@login_required
def create_found_animal_post(request):
    """Bulunan hayvan ilanı oluşturma sayfası"""
    api_key = settings.GOOGLE_MAPS_API_KEY
    if request.method == 'POST':
        form = LostItemPostForm(request.POST, request.FILES)
        if form.is_valid():
            item_post = form.save(commit=False)
            item_post.user = request.user
            item_post.post_type = 'found'  # Bulunan hayvan ilanı
            item_post.status = 'active'
            item_post.save()
            upsert_item_post_to_mongo(item_post)
            
            # Signal otomatik olarak eşleştirme yapacak (accounts/signals.py)
            # Eşleşmeler ImageMatch tablosuna kaydedilecek ve bildirimler otomatik görünecek
            messages.success(request, 'Bulunan hayvan ilanınız başarıyla oluşturuldu! Eşleşmeler arka planda işleniyor...')
            
            return redirect('post_detail', post_id=item_post.id)
        else:
            messages.error(request, 'Lütfen formu kontrol ediniz.')
    else:
        form = LostItemPostForm(initial={'main_category': 'animals'})
    
    return render(request, 'accounts/create_found_item.html', {
        'form': form,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        'is_animal': True  # Hayvan ilanı için flag
    })


@login_required
def create_post(request):
    """İlan ekleme merkezi - Kayıp/Bulunan seçenekleri"""
    return render(request, 'accounts/create_post.html')


@login_required
def list_lost_posts(request):
    """Sadece kayıp ilanları listele (Sadece giriş yapmış kullanıcılar)"""
    posts = (
        ItemPost.objects
        .filter(status='active', post_type='lost')
        .select_related('user')
    )
    paginator = Paginator(posts, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'accounts/home.html', {
        'page_obj': page_obj,
        'total_posts': posts.count(),
        'lost_posts': posts.count(),
        'found_posts': 0,
    })


@login_required
def list_found_posts(request):
    """Sadece bulunan ilanları listele (Sadece giriş yapmış kullanıcılar)"""
    posts = (
        ItemPost.objects
        .filter(status='active', post_type='found')
        .select_related('user')
    )
    paginator = Paginator(posts, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'accounts/home.html', {
        'page_obj': page_obj,
        'total_posts': posts.count(),
        'lost_posts': 0,
        'found_posts': posts.count(),
    })


def post_detail(request, post_id: int):
    """İlan detay sayfası"""
    post = get_object_or_404(ItemPost.objects.select_related('user'), id=post_id)
    
    # Eşleşen ilanları bul (her zaman dinamik hesapla ve arka planda kaydet)
    matched_posts = []
    if request.user.is_authenticated and request.user.id == post.user_id and post.image:
        try:
            print(f"\n[EŞLEŞME] İlan {post.id} için eşleşme aranıyor...")
            print(f"[EŞLEŞME] İlan tipi: {post.post_type}, Şehir: {post.city}, Çocuk ilanı: {getattr(post, 'is_missing_child', False)}")
            
            ms = MatchingService()
            results = ms.find_matches(post)
            
            print(f"[EŞLEŞME] find_matches sonucu: {len(results)} eşleşme bulundu")
            
            # Sonuçları ekle
            for r in results:
                matched_posts.append({
                    "post": r["post"],
                    "similarity": r["similarity"],
                    "similarity_percent": round(r["similarity"] * 100, 2),
                    "distance": 1 - r["similarity"],
                })
                print(f"[EŞLEŞME] Eşleşme: {r['post'].id} - {r['post'].title} (Benzerlik: {r['similarity']:.2%})")
            
            print(f"[EŞLEŞME] Toplam {len(matched_posts)} eşleşme döndürülüyor\n")
            
            # Arka planda eşleşmeleri kaydet (async olarak)
            if results:
                try:
                    saved_count = ms.save_matches(post)
                    if saved_count > 0:
                        print(f"[EŞLEŞME] İlan {post.id} için {saved_count} eşleşme kaydedildi")
                except Exception as save_error:
                    print(f"[EŞLEŞME HATA] Kaydetme hatası: {save_error}")
                    import traceback
                    traceback.print_exc()
        except Exception as e:
            print(f"[EŞLEŞME HATA] Eşleşme getirme hatası: {e}")
            import traceback
            traceback.print_exc()
    else:
        if not request.user.is_authenticated:
            print(f"[EŞLEŞME] Kullanıcı giriş yapmamış")
        elif request.user.id != post.user_id:
            print(f"[EŞLEŞME] Kullanıcı ilanın sahibi değil (user_id: {request.user.id}, post.user_id: {post.user_id})")
        elif not post.image:
            print(f"[EŞLEŞME] İlanın görseli yok")
    
    # Benzerlik skoruna göre sırala (zaten sıralı ama emin olmak için)
    matched_posts.sort(key=lambda x: x["similarity"], reverse=True)
    
    return render(request, 'accounts/post_detail.html', { 
        'post': post,
        'matched_posts': matched_posts[:5],  # En fazla 5 eşleşme göster
        'matches_count': len(matched_posts),
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    })


@login_required
@require_POST
def mark_match_as_found(request, lost_post_id: int, found_post_id: int):
    """
    Kayıp ilan sahibi, bulunan ilanı "kaybettiğimi buldum" olarak işaretler.
    Bu işlem her iki ilanı da 'resolved' durumuna getirir ve eşleşmeyi sonlandırır.
    """
    lost_post = get_object_or_404(ItemPost, id=lost_post_id, post_type='lost', status='active')
    found_post = get_object_or_404(ItemPost, id=found_post_id, post_type='found', status='active')
    
    # Sadece kayıp ilan sahibi bu işlemi yapabilir
    if request.user.id != lost_post.user_id:
        messages.error(request, 'Bu işlemi sadece kayıp ilan sahibi yapabilir.')
        return redirect('post_detail', post_id=lost_post_id)
    
    # Her iki ilanı da 'resolved' durumuna getir
    lost_post.status = 'resolved'
    lost_post.save()
    
    found_post.status = 'resolved'
    found_post.save()
    
    # İlgili ImageMatch kayıtlarını doğrulanmış olarak işaretle
    try:
        from image_matching.models import ImageVector, ImageMatch
        
        # Kayıp ilanın vector'ünü bul
        lost_vector = ImageVector.objects.filter(
            image_path__icontains=str(lost_post.id)
        ).first()
        
        # Bulunan ilanın vector'ünü bul
        found_vector = ImageVector.objects.filter(
            image_path__icontains=str(found_post.id)
        ).first()
        
        if lost_vector and found_vector:
            # Her iki yöndeki eşleşmeleri bul ve doğrula
            ImageMatch.objects.filter(
                source_vector=lost_vector,
                target_vector=found_vector
            ).update(is_verified=True, verified_by=request.user)
            
            ImageMatch.objects.filter(
                source_vector=found_vector,
                target_vector=lost_vector
            ).update(is_verified=True, verified_by=request.user)
    except Exception as e:
        print(f"[MARK_MATCH] ImageMatch güncelleme hatası: {e}")
    
    # Bulunan ilan sahibine bildirim gönder
    try:
        from django.contrib import messages as django_messages
        django_messages.success(
            request,
            f'"{found_post.title}" ilanını kaybettiğinizi bulduğunuzu işaretlediniz. '
            f'İlan sahibi ({found_post.user.first_name or found_post.user.username}) bilgilendirildi.'
        )
    except Exception as e:
        print(f"[MARK_MATCH] Bildirim hatası: {e}")
    
    return redirect('post_detail', post_id=lost_post_id)


def terms_of_service(request):
    """Kullanım Şartları sayfası"""
    return render(request, 'accounts/terms_of_service.html')


def privacy_policy(request):
    """KVKK Gizlilik Politikası sayfası"""
    return render(request, 'accounts/privacy_policy.html')


def findus_info(request):
    """FindUs tanıtım sayfası"""
    return render(request, 'accounts/findus_info.html')

@login_required
def edit_post(request, post_id: int):
    """Kullanıcının kendi ilanını düzenlemesi"""
    post = get_object_or_404(ItemPost, id=post_id, user=request.user)
    if request.method == 'POST':
        form = LostItemPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            edited = form.save(commit=False)
            # post_type ve status mevcut değerleri korunsun
            edited.post_type = post.post_type
            edited.status = post.status
            edited.user = request.user
            edited.save()
            upsert_item_post_to_mongo(edited)
            messages.success(request, 'İlan başarıyla güncellendi!')
            return redirect('post_detail', post_id=post.id)
        else:
            messages.error(request, 'Lütfen formu kontrol edin.')
    else:
        form = LostItemPostForm(instance=post)
    return render(request, 'accounts/edit_post.html', { 'form': form, 'post': post })


@login_required
@require_POST
def delete_post(request, post_id: int):
    """Kullanıcının kendi ilanını silmesi"""
    post = get_object_or_404(ItemPost, id=post_id, user=request.user)
    post.delete()
    messages.success(request, 'İlan silindi.')
    return redirect('profile')


@login_required
def notifications_view(request):
    """
    Bildirimleri listele.
    Bildirimler ImageMatch üzerinden dinamik hesaplanıyor (template tag ile).
    Bildirimler görüntülendiğinde, görüntülenen post_id'leri session'a kaydedilir.
    """
    # Bildirimler görüntülendiğinde, görüntülenen post_id'leri session'a kaydet
    from accounts.templatetags.notification_tags import _get_notification_post_ids
    
    # Kullanıcının bildirimlerini al
    notification_post_ids = _get_notification_post_ids(request.user)
    
    # Session'a kaydet (görüntülenen bildirimler)
    viewed_notifications = request.session.get('viewed_notifications', set())
    if isinstance(viewed_notifications, list):
        viewed_notifications = set(viewed_notifications)
    
    # Tüm görüntülenen bildirimleri ekle
    viewed_notifications.update(notification_post_ids)
    request.session['viewed_notifications'] = list(viewed_notifications)
    request.session.modified = True
    
    return render(request, 'accounts/notifications.html', {})


@login_required
def show_matches(request, post_id: int):
    """Eşleşen ilanları göster"""
    post = get_object_or_404(ItemPost, id=post_id, user=request.user)
    
    # Session'dan eşleşmeleri al
    matches_data = request.session.get(f'matches_{post_id}', [])
    
    # Eşleşen ilanları getir
    matched_posts = []
    for match_data in matches_data:
        try:
            matched_post = ItemPost.objects.get(id=match_data['post_id'])
            matched_posts.append({
                'post': matched_post,
                'similarity': match_data.get('similarity', 0.0),
                'similarity_percent': round(match_data.get('similarity', 0.0) * 100, 2),
                'distance': match_data.get('distance', 0.0)
            })
        except ItemPost.DoesNotExist:
            continue
    
    # Benzerlik skoruna göre sırala (yüksekten düşüğe)
    matched_posts.sort(key=lambda x: x['similarity'], reverse=True)
    
    # Session'dan eşleşmeleri temizle
    if f'matches_{post_id}' in request.session:
        del request.session[f'matches_{post_id}']
    
    context = {
        'post': post,
        'matched_posts': matched_posts,
        'matches_count': len(matched_posts),
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    }
    
    return render(request, 'accounts/show_matches.html', context)
