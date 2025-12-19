"""
Basit CLIP vektörleme testi.

Kullanım:
    python test_clip_embedding.py [gorsel_yolu]

Varsayılan olarak `media/item_images/images.jpeg` dosyasını dener.
Ön koşullar: `pip install -r requirements.txt` (özellikle open-clip-torch).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from image_matching.utils import image_to_clip_vector


def run(image_path: Path) -> None:
    if not image_path.exists():
        raise FileNotFoundError(f"Görsel bulunamadı: {image_path}")

    print(f"📸 Görsel: {image_path}")
    vec = image_to_clip_vector(str(image_path))

    dim = len(vec)
    l2 = math.sqrt(sum(x * x for x in vec))
    preview = ", ".join(f"{v:.4f}" for v in vec[:8])

    print(f"🔢 Boyut: {dim} (beklenen: 512)")
    print(f"📐 L2 norm: {l2:.4f} (normalize ≈ 1.0)")
    print(f"👀 İlk 8 değer: [{preview}{', ...' if dim > 8 else ''}]")
    print("✅ CLIP vektörleme testi tamamlandı.")


def main(argv: list[str]) -> int:
    default_img = Path("media/item_images/images.jpeg")
    image_path = Path(argv[1]) if len(argv) > 1 else default_img
    try:
        run(image_path)
    except Exception as exc:  # pragma: no cover - sadece el ile test
        print(f"❌ Hata: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

