#!/usr/bin/env python
"""
Test script to verify Turkish character encoding
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')
django.setup()

from accounts.models import ItemPost

def test_turkish_characters():
    """Test that Turkish characters are properly stored and retrieved"""
    
    # Test strings with Turkish characters
    test_strings = [
        "Kayıp Gözlük - Antalya Muratpaşa",
        "Güneş gözlüğümü plajda kaybettim. Ray-Ban marka.",
        "Osmangazi metroda siyah çanta buldum. İçinde kitaplar var.",
        "Çankaya'da anahtar buldum. Sahibi arıyorsa iletişime geçsin.",
        "İstanbul Kadıköy'de cüzdan kaybettim.",
        "Ödül: 500₺"
    ]
    
    print("Testing Turkish character encoding...")
    print("=" * 50)
    
    for i, test_string in enumerate(test_strings, 1):
        print(f"{i}. Original: {test_string}")
        
        # Check if string contains Turkish characters
        turkish_chars = ['ç', 'ğ', 'ı', 'ö', 'ş', 'ü', 'Ç', 'Ğ', 'İ', 'Ö', 'Ş', 'Ü']
        has_turkish = any(char in test_string for char in turkish_chars)
        print(f"   Contains Turkish chars: {has_turkish}")
        
        # Test encoding/decoding
        try:
            encoded = test_string.encode('utf-8')
            decoded = encoded.decode('utf-8')
            print(f"   Encoding test: {'✓ PASS' if decoded == test_string else '✗ FAIL'}")
        except Exception as e:
            print(f"   Encoding test: ✗ FAIL - {e}")
        
        print()
    
    # Test database content
    print("Database content test:")
    print("=" * 50)
    
    posts = ItemPost.objects.all()[:3]
    for post in posts:
        print(f"Title: {post.title}")
        print(f"Description: {post.description[:50]}...")
        print(f"City: {post.city}")
        print(f"District: {post.district}")
        print("-" * 30)

if __name__ == '__main__':
    test_turkish_characters()
