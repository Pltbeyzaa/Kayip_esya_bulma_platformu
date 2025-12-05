"""
CLIP tabanlı görüntü vektörleme yardımcı fonksiyonları.

Bu dosya, bir görüntü dosya yolunu alıp CLIP modelinden
normalize edilmiş embedding (vektör) üreten fonksiyon içerir.

Kullanım örneği:

    from image_matching.utils import image_to_clip_vector

    vec = image_to_clip_vector("media/example.jpg")

Gereken paketler:
    pip install open-clip-torch torch torchvision pillow
"""

from functools import lru_cache
from typing import List, Tuple

from PIL import Image
import torch


@lru_cache(maxsize=1)
def _load_clip_model(
    model_name: str = "ViT-B-32",
    pretrained: str = "openai",
    device: str | None = None,
) -> Tuple[torch.nn.Module, callable, torch.device]:
    """
    CLIP modelini tek sefer yükle ve cache et.

    - model_name: CLIP mimarisi (örn: ViT-B-32, ViT-L-14 vb.)
    - pretrained: open-clip için ön-eğitim seti adı (örn: openai, laion2b_s34b_b79k)
    """
    try:
        import open_clip  # type: ignore
    except ImportError as exc:  # pragma: no cover - sadece runtime uyarısı
        raise ImportError(
            "open_clip bulunamadı. Lütfen önce `pip install open-clip-torch` çalıştırın."
        ) from exc

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    dev = torch.device(device)
    model, _, preprocess = open_clip.create_model_and_transforms(
        model_name, pretrained=pretrained
    )
    model.eval()
    model.to(dev)

    return model, preprocess, dev


def image_to_clip_vector(
    image_path: str,
    model_name: str = "ViT-B-32",
    pretrained: str = "openai",
    device: str | None = None,
) -> List[float]:
    """
    Verilen görüntü dosyasını CLIP embedding vektörüne çevir.

    Dönen değer:
        - normalize edilmiş (L2 normu 1 olan) vektör (list[float])
    """
    model, preprocess, dev = _load_clip_model(
        model_name=model_name, pretrained=pretrained, device=device
    )

    # Görüntüyü yükle ve CLIP preprocess'inden geçir
    img = Image.open(image_path).convert("RGB")
    img_tensor = preprocess(img).unsqueeze(0).to(dev)

    with torch.no_grad():
        features = model.encode_image(img_tensor)
        # Normalize et (Milvus / benzerlik aramalarında genelde iyi pratik)
        features = features / features.norm(dim=-1, keepdim=True)

    # Tek boyutlu Python listesine çevir
    return features.squeeze(0).cpu().tolist()


def vectorize_object_clip(image_path: str) -> List[float] | None:
    """
    Dış API'ler tarafından kullanılmak üzere, CLIP tabanlı
    nesne vektörleme için basit bir sarmalayıcı.
    """
    try:
        return image_to_clip_vector(image_path)
    except Exception as exc:  # pragma: no cover - sadece runtime
        print(f"CLIP vektörleme hatası: {exc}")
        return None

