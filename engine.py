from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent

class ZakIdentityEngine:
    def __init__(self, config_path=ROOT / "identity.json"):
        self.config = json.loads(Path(config_path).read_text())

    def references_for(self, view="front", include_body=False):
        face = self.config["face"]["anchors"]
        mapping = {
            "front": [face[0], face[1], face[2]],
            "three_quarter_left": [face[1], face[0], face[3]],
            "three_quarter_right": [face[2], face[0]],
            "left_profile": [face[3], face[1]],
            "low_angle": [face[4], face[0], face[1]],
        }
        refs = mapping.get(view, [face[0], face[1], face[2]])
        if include_body:
            refs += self.config["body"]["anchors"][:2]
        return [str(ROOT / p) for p in refs]

    def identity_prompt(self):
        g = self.config["grooming"]
        return (
            "Preserve the subject's exact underlying facial identity from the supplied genuine references. "
            "Do not beautify or redesign facial structure. "
            f"Hair: {g['hair']} Facial hair: {g['facial_hair']} "
            "Maintain natural skin texture and asymmetry. Generated images must never become identity anchors."
        )

    def build_request(self, scene, view="front", include_body=True):
        return {
            "scene": scene,
            "identity_instruction": self.identity_prompt(),
            "references": self.references_for(view, include_body),
            "rules": self.config["generation_rules"],
        }

if __name__ == "__main__":
    engine = ZakIdentityEngine()
    print(json.dumps(engine.build_request("casual iPhone coffee photo", "three_quarter_left"), indent=2))
