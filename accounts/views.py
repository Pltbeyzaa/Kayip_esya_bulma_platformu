from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from .forms import UserRegistrationForm, UserLoginForm, LostItemPostForm
from .models import ItemPost
from .services import upsert_item_post_to_mongo


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
    # Tüm aktif ilanları getir (örnek verileri hariç tut)
    # Not: Örnek veriler management command ile 'testuser' kullanıcısı altında oluşturuluyor
    posts = (
        ItemPost.objects
        .filter(status='active')
        .exclude(user__username='testuser')
        .select_related('user')
    )

    # Sayfalama
    paginator = Paginator(posts, 12)  # Sayfa başına 12 ilan
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # İstatistikler
    total_posts = ItemPost.objects.filter(status='active').exclude(user__username='testuser').count()
    lost_posts = ItemPost.objects.filter(status='active', post_type='lost').exclude(user__username='testuser').count()
    found_posts = ItemPost.objects.filter(status='active', post_type='found').exclude(user__username='testuser').count()

    context = {
        'page_obj': page_obj,
        'total_posts': total_posts,
        'lost_posts': lost_posts,
        'found_posts': found_posts,
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
            login(request, user)
            messages.success(request, 'Kayıt başarılı! Hoş geldiniz.')
            return redirect('home')
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
                return redirect('home')
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
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def create_lost_item_post(request):
    """Kayıp eşya ilanı oluşturma sayfası"""
    if request.method == 'POST':
        form = LostItemPostForm(request.POST, request.FILES)
        if form.is_valid():
            item_post = form.save(commit=False)
            item_post.user = request.user
            item_post.post_type = 'lost'  # Kayıp eşya ilanı
            item_post.status = 'active'
            item_post.save()
            upsert_item_post_to_mongo(item_post)
            messages.success(request, 'Kayıp eşya ilanınız başarıyla oluşturuldu!')
            return redirect('home')
        else:
            messages.error(request, 'Lütfen formu kontrol ediniz.')
    else:
        form = LostItemPostForm()
    
    return render(request, 'accounts/create_lost_item.html', {'form': form})


@login_required
def create_found_item_post(request):
    """Bulunan eşya ilanı oluşturma sayfası"""
    if request.method == 'POST':
        form = LostItemPostForm(request.POST, request.FILES)
        if form.is_valid():
            item_post = form.save(commit=False)
            item_post.user = request.user
            item_post.post_type = 'found'  # Bulunan eşya ilanı
            item_post.status = 'active'
            item_post.save()
            upsert_item_post_to_mongo(item_post)
            messages.success(request, 'Bulunan eşya ilanınız başarıyla oluşturuldu!')
            return redirect('home')
        else:
            messages.error(request, 'Lütfen formu kontrol ediniz.')
    else:
        form = LostItemPostForm()

    return render(request, 'accounts/create_found_item.html', {'form': form})


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
        .exclude(user__username='testuser')
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
        .exclude(user__username='testuser')
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
    return render(request, 'accounts/post_detail.html', { 'post': post })


def terms_of_service(request):
    """Kullanım Şartları sayfası"""
    return render(request, 'accounts/terms_of_service.html')


def privacy_policy(request):
    """KVKK Gizlilik Politikası sayfası"""
    return render(request, 'accounts/privacy_policy.html')


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
