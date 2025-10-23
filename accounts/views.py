from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .forms import UserRegistrationForm, UserLoginForm


def home(request):
    """Ana sayfa"""
    return render(request, 'accounts/home.html')


def register_view(request):
    """Kullanıcı kayıt sayfası"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
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
    return redirect('home')


@login_required
def profile_view(request):
    """Kullanıcı profil sayfası"""
    return render(request, 'accounts/profile.html', {'user': request.user})
