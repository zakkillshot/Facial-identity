# ZAK Identity Engine v0.5

v0.5 adds an **MCP bridge** around the existing ZAK ID reference and checking engine.

## What is real in this build

- Five genuine face anchors and five genuine body/posture anchors remain the only identity references.
- The 1 mm facial-hair target and current natural hair rules remain separate from facial geometry.
- `mcp_server.py` exposes four MCP tools:
  - `get_zak_identity_rules`
  - `build_zak_image_request`
  - `check_zak_identity`
  - `calibrate_zak_identity_checker`
- The checker returns `REVIEW` instead of inventing an identity score if the optional embedding backend is unavailable.

## Important limitation

This package is now **bridge-ready**, but it is not automatically connected to ChatGPT merely because the ZIP exists. It must run on a machine/server with the MCP SDK installed and then be connected through a supported ChatGPT custom-app/MCP workflow. The current package also does not train or modify ChatGPT's built-in image model.

## Run locally

From this folder:

```bash
python mcp_server.py
```

The MCP SDK must be installed. For real embedding-based PASS/REJECT checks, InsightFace/ArcFace plus its local model/runtime must also be provisioned.

## Privacy

The reference photos are bundled locally in this prototype. Do not publish the ZIP or expose an unauthenticated public server containing these photos. For a deployed version, keep references in private storage and add authentication.
