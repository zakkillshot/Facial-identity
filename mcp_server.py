"""ZAK Identity Engine v0.5 — MCP bridge.

Exposes the local identity engine as MCP tools when the optional `mcp` Python
package is installed. The biometric backend remains optional and never invents
an identity score when unavailable.
"""
from pathlib import Path
from typing import Literal

from engine import ZakIdentityEngine
from face_checker import FaceChecker

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    raise SystemExit(
        "MCP package is not installed. Install the official Python MCP SDK, then run this file."
    ) from e

ROOT = Path(__file__).resolve().parent
mcp = FastMCP("ZAK Identity Engine")
engine = ZakIdentityEngine()
checker = FaceChecker()

View = Literal["front", "three_quarter_left", "three_quarter_right", "left_profile", "low_angle"]

@mcp.tool()
def get_zak_identity_rules() -> dict:
    """Return ZAK ID's genuine-reference policy, grooming, body, and generation rules."""
    return {"engine_version": "0.5", "identity": engine.config}

@mcp.tool()
def build_zak_image_request(scene: str, view: View = "front", include_body: bool = True) -> dict:
    """Build an identity-preserving image request and select genuine references for the requested view."""
    result = engine.build_request(scene=scene, view=view, include_body=include_body)
    result["engine_version"] = "0.5"
    return result

@mcp.tool()
def check_zak_identity(image_path: str, view: View = "front") -> dict:
    """Compare a candidate image to genuine ZAK ID references and return PASS/REVIEW/REJECT.

    If the embedding backend is unavailable, returns REVIEW rather than fabricating a score.
    """
    p = Path(image_path).expanduser().resolve()
    if not p.exists():
        return {"engine_version": "0.5", "status": "ERROR", "error": "image_not_found", "image_path": str(p)}
    result = checker.check(p, view=view)
    result["engine_version"] = "0.5"
    return result

@mcp.tool()
def calibrate_zak_identity_checker() -> dict:
    """Calibrate the matcher using only genuine enrolled ZAK ID face references."""
    result = checker.calibrate()
    if result is None:
        return {"engine_version": "0.5", "status": "REVIEW", "note": "Embedding backend unavailable; no threshold fabricated."}
    return {"engine_version": "0.5", "status": "OK", "calibration": result}

if __name__ == "__main__":
    mcp.run()
