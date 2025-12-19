import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')
django.setup()

from image_matching.models import ImageMatch
from accounts.constants import MATCH_NOTIFY_THRESHOLD

matches = ImageMatch.objects.filter(similarity_score__gte=MATCH_NOTIFY_THRESHOLD)
print(f"%75+ eşleşme sayısı: {matches.count()}\n")

for m in matches[:10]:
    print(f"{m.source_vector.user.username} <-> {m.target_vector.user.username}: %{m.similarity_score*100:.2f}")

