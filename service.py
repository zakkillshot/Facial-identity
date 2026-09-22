"""ZAK Identity Engine v0.7 HTTP service.

The biometric model is lazy-loaded on the first identity-check request so the
service can boot with a much smaller idle memory footprint.
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import json

from face_checker import FaceChecker
from engine import ZakIdentityEngine


ROOT = Path(__file__).resolve().parent
checker = FaceChecker()
engine = ZakIdentityEngine()


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, payload):
        data = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self._send(
                200,
                {
                    "service": "ZAK Identity Engine",
                    "version": "0.7",
                    "status": "ok",
                    "embedding_backend": "lazy",
                },
            )

        elif self.path == "/self_test":
            try:
                images = [
                    p
                    for p in (ROOT / "references").rglob("*")
                    if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
                ]

                if not images:
                    return self._send(
                        500,
                        {"error": "no_reference_images_found"},
                    )

                test_image = images[0]
                result = checker.check(test_image, "front")

                self._send(
                    200,
                    {
                        "status": "ok",
                        "version": "0.7",
                        "model_loaded": True,
                        "test_image": test_image.name,
                        "result": result,
                    },
                )

            except Exception as e:
                self._send(
                    500,
                    {
                        "status": "error",
                        "error": type(e).__name__,
                        "detail": str(e),
                    },
                )

        elif self.path == "/identity":
            self._send(
                200,
                {
                    "version": "0.7",
                    "identity": engine.config,
                },
            )

        else:
            self._send(
                404,
                {"error": "not_found"},
            )

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))

        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send(
                400,
                {"error": "invalid_json"},
            )

        try:
            if self.path == "/check_identity":
                image = body.get("image_path")

                if not image:
                    return self._send(
                        400,
                        {"error": "image_path_required"},
                    )

                p = Path(image)

                if not p.exists():
                    return self._send(
                        400,
                        {
                            "error": "image_not_found",
                            "image_path": image,
                        },
                    )

                self._send(
                    200,
                    checker.check(
                        p,
                        body.get("view", "front"),
                    ),
                )

            elif self.path == "/build_request":
                self._send(
                    200,
                    engine.build_request(
                        body.get("scene", ""),
                        body.get("view", "front"),
                        body.get("include_body", True),
                    ),
                )

            else:
                self._send(
                    404,
                    {"error": "not_found"},
                )

        except Exception as e:
            self._send(
                500,
                {
                    "error": type(e).__name__,
                    "detail": str(e),
                },
            )

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)

    a = p.parse_args()

    print(
        f"ZAK Identity Engine v0.7 listening on "
        f"http://{a.host}:{a.port}"
    )

    ThreadingHTTPServer(
        (a.host, a.port),
        Handler,
    ).serve_forever()
