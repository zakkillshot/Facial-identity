"""Face-embedding backend for ZAK Identity Engine v0.6.

Uses InsightFace/ArcFace when installed. No generated image is ever enrolled as a
reference. This module does not download models automatically.
"""
from pathlib import Path
import numpy as np

class BackendUnavailable(RuntimeError): pass

class InsightFaceBackend:
    def __init__(self, model_name='buffalo_l', providers=None):
        try:
            from insightface.app import FaceAnalysis
        except ImportError as e:
            raise BackendUnavailable(
                'InsightFace is not installed. Install insightface + onnxruntime, '
                'then provision the buffalo_l model locally.'
            ) from e
        providers = providers or ['CPUExecutionProvider']
        self.app = FaceAnalysis(name=model_name, providers=providers)
        self.app.prepare(ctx_id=-1, det_size=(640,640))

    def embed(self, image_path):
        import cv2
        img = cv2.imread(str(image_path))
        if img is None: raise ValueError(f'Cannot read image: {image_path}')
        faces = self.app.get(img)
        if not faces: raise ValueError(f'No face detected: {image_path}')
        # Prefer largest detected face.
        f = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]))
        v = np.asarray(f.normed_embedding, dtype=np.float32)
        return v / (np.linalg.norm(v) + 1e-12)

    @staticmethod
    def cosine(a,b):
        return float(np.dot(a,b) / ((np.linalg.norm(a)+1e-12)*(np.linalg.norm(b)+1e-12)))
