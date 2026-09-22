from pathlib import Path
import json
from PIL import Image, ImageOps, ImageStat
import numpy as np
ROOT = Path(__file__).resolve().parent

class FaceChecker:
    """ZAK Face Checker v0.6.

    If InsightFace/ArcFace is available, compares a candidate against genuine
    enrolled references with cosine similarity. Thresholds are calibrated from
    Zak's own genuine reference set; they are not universal biometric claims.
    """
    def __init__(self, config_path=ROOT/'identity.json', backend=None):
        self.config=json.loads(Path(config_path).read_text())
        self.backend=backend
        if self.backend is None:
            try:
                from face_embedding_backend import InsightFaceBackend
                self.backend=InsightFaceBackend()
            except Exception:
                self.backend=None

    def _quality(self,path):
        im=Image.open(path).convert('L'); im=ImageOps.fit(im,(256,256))
        stat=ImageStat.Stat(im); mean=stat.mean[0]
        arr=np.asarray(im,dtype=np.float32)
        dx=np.abs(arr[:,:-1]-arr[:,1:]).mean(); dy=np.abs(arr[:-1,:]-arr[1:,:]).mean()
        sharp=(dx+dy)
        return {'exposure':round(max(0,1-abs(mean-128)/128),3),'sharpness':round(float(min(1,sharp/24)),3)}

    def identity_score(self,candidate_path,reference_paths):
        if self.backend is None: return None, []
        c=self.backend.embed(candidate_path)
        scores=[]
        for r in reference_paths:
            rp=ROOT/r if not Path(r).is_absolute() else Path(r)
            scores.append(self.backend.cosine(c,self.backend.embed(rp)))
        # robust aggregate: mean of top 3, useful across pose differences
        top=sorted(scores,reverse=True)[:min(3,len(scores))]
        return float(np.mean(top)), scores

    def calibrate(self):
        """Estimate a conservative same-person floor from genuine refs only."""
        if self.backend is None: return None
        refs=[ROOT/p for p in self.config['face']['anchors']]
        embs=[self.backend.embed(p) for p in refs]
        pair=[]
        for i in range(len(embs)):
            for j in range(i+1,len(embs)):
                pair.append(self.backend.cosine(embs[i],embs[j]))
        # Do not pretend this is a universal threshold. Use low genuine-pair percentile,
        # with a small margin, and clamp to sane cosine range.
        threshold=float(np.clip(np.percentile(pair,10)-0.03,0.20,0.85))
        return {'threshold':round(threshold,4),'genuine_pair_scores':[round(x,4) for x in pair]}

    def check(self,candidate_path,view='front'):
        from engine import ZakIdentityEngine
        refs=ZakIdentityEngine().references_for(view=view,include_body=False)
        quality=self._quality(candidate_path)
        score,per_ref=self.identity_score(candidate_path,refs)
        cal=self.calibrate() if self.backend is not None else None
        threshold=cal['threshold'] if cal else None
        # Three-way decision around the genuine-reference floor. Scores close to
        # the calibrated floor stay in REVIEW rather than forcing a binary claim.
        if score is None:
            status='REVIEW'
        else:
            review_margin=0.04
            status='PASS' if score>=threshold else ('REVIEW' if score>=threshold-review_margin else 'REJECT')
        notes=[]
        if quality['exposure']<0.55: notes.append('Exposure may reduce comparison reliability.')
        if quality['sharpness']<0.35: notes.append('Candidate is soft/blurred; use a clearer face crop.')
        if score is None: notes.append('Embedding backend unavailable; no identity claim made.')
        return {'candidate':str(candidate_path),'view':view,'references_used':refs,
                'quality':quality,'identity_score':None if score is None else round(score,4),
                'per_reference_scores':[round(x,4) for x in per_ref],
                'calibration':cal,'status':status,'notes':notes}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('image'); p.add_argument('--view',default='front'); p.add_argument('--calibrate',action='store_true'); a=p.parse_args()
    fc=FaceChecker()
    print(json.dumps(fc.calibrate() if a.calibrate else fc.check(a.image,a.view),indent=2))
