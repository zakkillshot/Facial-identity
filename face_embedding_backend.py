"""Memory-conscious face-embedding backend for ZAK Identity Engine v0.7.

Optimized for small free-tier instances:
- defaults to InsightFace ``buffalo_s`` instead of ``buffalo_l``
- uses CPU execution only
- uses a 320x320 detector input
- model initialization is deferred until the first embedding request

Generated images are never enrolled as identity references.
"""
import gc
import os
import threading
import numpy as np


class BackendUnavailable(RuntimeError):
    pass


class InsightFaceBackend:
    def __init__(self, model_name=None, providers=None, det_size=None):
        self.model_name = model_name or os.getenv("ZAK_FACE_MODEL", "buffalo_s")
        self.providers = providers or ["CPUExecutionProvider"]
        det = det_size or os.getenv("ZAK_DET_SIZE", "320")
        try:
            side = max(160, min(640, int(det)))
        except (TypeError, ValueError):
            side = 320
        self.det_size = (side, side)
        self._app = None
        self._lock = threading.Lock()

    def _ensure_app(self):
        if self._app is not None:
            return self._app
        with self._lock:
            if self._app is not None:
                return self._app
            try:
                from insightface.app import FaceAnalysis
            except ImportError as e:
                raise BackendUnavailable(
                    "InsightFace is not installed. Install insightface + onnxruntime."
                ) from e
            app = FaceAnalysis(name=self.model_name, providers=self.providers)
            app.prepare(ctx_id=-1, det_size=self.det_size)
            self._app = app
            return app

    def embed(self, image_path):
        import cv2

        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")

        app = self._ensure_app()
        faces = app.get(img)
        del img
        if not faces:
            gc.collect()
            raise ValueError(f"No face detected: {image_path}")

        face = max(
            faces,
            key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]),
        )
        vector = np.asarray(face.normed_embedding, dtype=np.float32).copy()
        del faces, face
        gc.collect()
        return vector / (np.linalg.norm(vector) + 1e-12)

    @staticmethod
    def cosine(a, b):
        return float(
            np.dot(a, b)
            / ((np.linalg.norm(a) + 1e-12) * (np.linalg.norm(b) + 1e-12))
        )
