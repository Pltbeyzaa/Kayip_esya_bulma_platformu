import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')
django.setup()

from accounts.models import ItemPost
from accounts.matching_service import MatchingService
from image_matching.models import ImageVector
import os

post = ItemPost.objects.get(id=21)
print(f"Post ID: {post.id}")
print(f"Post image name: {post.image.name}")
filename = os.path.basename(post.image.name)
print(f"Filename: {filename}")

vecs = ImageVector.objects.all()
print(f"\nToplam ImageVector: {vecs.count()}")
for v in vecs[:5]:
    print(f"  Vector image_path: {v.image_path}")
    print(f"  Contains filename? {filename in v.image_path}")

ms = MatchingService()
source_vec = ms._get_vector_for_post(post)
print(f"\nSource vector bulundu: {source_vec is not None}")
if source_vec:
    print(f"  Vector ID: {source_vec.vector_id}")

matches = ms.find_matches(post)
print(f"\nBulunan eşleşme sayısı: {len(matches)}")

if matches:
    target_post = matches[0]['post']
    print(f"Target post ID: {target_post.id}")
    target_vec = ms._get_vector_for_post(target_post)
    print(f"Target vector bulundu: {target_vec is not None}")
    if target_vec:
        print(f"  Vector ID: {target_vec.vector_id}")

saved = ms.save_matches(post)
print(f"\nKaydedilen eşleşme sayısı: {saved}")

