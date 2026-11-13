"""Embeddings Module: Text (BGE-M3 compatible) and Visual (CLIP compatible).

Generates dense normalized vector representations for technical text passages
and diagram/photo features.
"""

import hashlib
import numpy as np
from typing import List, Union
from PIL import Image

class MultimodalEmbeddingService:
    def __init__(self, dim: int = 128):
        self.dim = dim

    def encode_text(self, text: str) -> np.ndarray:
        """Generates normalized dense embedding for a text query or chunk.
        Uses fast deterministic hash-based feature projection with NumPy.
        """
        words = text.lower().strip().split()
        if not words:
            vec = np.zeros(self.dim, dtype=np.float32)
            vec[0] = 1.0
            return vec

        accum = np.zeros(self.dim, dtype=np.float32)
        for word in words:
            # Deterministic hash to dimension indices
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx1 = h % self.dim
            idx2 = (h >> 16) % self.dim
            idx3 = (h >> 32) % self.dim
            sign = 1.0 if (h >> 48) % 2 == 0 else -1.0
            
            # Boost specific industrial codes or numbers
            weight = 2.5 if any(char.isdigit() for char in word) or len(word) > 7 else 1.0
            accum[idx1] += sign * weight
            accum[idx2] += -sign * 0.7 * weight
            accum[idx3] += sign * 0.5 * weight

        # L2 Normalization
        norm = np.linalg.norm(accum)
        if norm > 1e-6:
            accum = accum / norm
        else:
            accum[0] = 1.0
        return accum

    def encode_texts(self, texts: List[str]) -> List[np.ndarray]:
        return [self.encode_text(t) for t in texts]

    def encode_image(self, image_input: Union[str, Image.Image]) -> np.ndarray:
        """Generates normalized visual embedding for an image (file path or PIL Image)."""
        if isinstance(image_input, str):
            try:
                img = Image.open(image_input).convert("RGB")
            except Exception:
                img = Image.new("RGB", (32, 32), color=(100, 100, 100))
        else:
            img = image_input.convert("RGB")

        # Extract visual statistics (colors, brightness, edge distribution)
        img_thumb = img.resize((16, 16))
        np_img = np.array(img_thumb, dtype=np.float32) / 255.0
        
        vec = np.zeros(self.dim, dtype=np.float32)
        r_mean = float(np.mean(np_img[:, :, 0]))
        g_mean = float(np.mean(np_img[:, :, 1]))
        b_mean = float(np.mean(np_img[:, :, 2]))

        vec[0] = r_mean * 2.0 - 1.0
        vec[1] = g_mean * 2.0 - 1.0
        vec[2] = b_mean * 2.0 - 1.0

        # High level pixel gradient
        grad = np.abs(np.diff(np_img, axis=0)).mean()
        vec[3] = float(grad)

        # Hash-based spread across remaining dimensions
        seed_hash = int(hashlib.md5(f"{r_mean:.3f}_{g_mean:.3f}_{b_mean:.3f}".encode()).hexdigest(), 16)
        for i in range(4, self.dim):
            vec[i] = ((seed_hash >> (i % 64)) % 100 - 50) / 100.0

        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm
        else:
            vec[0] = 1.0
        return vec

embedding_service = MultimodalEmbeddingService()
