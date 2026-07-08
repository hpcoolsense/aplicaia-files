#!/usr/bin/env python3
"""
build_player.py — ensambla posts/templates/reel-player.html (autocontenido).

Inlinea React + ReactDOM + Babel standalone + fuentes (base64) + los 4 JSX de
reel-src/ en un único HTML sin dependencias de red — el sandbox de la routine
lo carga por file:// y renderiza offline.

Correr después de editar cualquier archivo de posts/templates/reel-src/:
    python3 posts/build_player.py
"""

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "templates" / "reel-src"
VENDOR = SRC / "vendor"
OUT = ROOT / "templates" / "reel-player.html"

# Orden de carga: motor → primitivas → plantillas → runner
JSX_FILES = ["animations.jsx", "reel-kinetics.jsx", "reel-templates.jsx", "reel-player.jsx"]


def js_escape(code: str) -> str:
    """Evita que un '</script' dentro del código cierre el tag inline."""
    return code.replace("</script", "<\\/script")


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def main():
    for req in [VENDOR / "react.js", VENDOR / "react-dom.js", VENDOR / "babel.js",
                VENDOR / "inter.woff2", VENDOR / "jbmono.woff2"]:
        if not req.exists():
            sys.exit(f"ERROR: falta {req}")

    jsx_blocks = []
    for name in JSX_FILES:
        p = SRC / name
        if not p.exists():
            sys.exit(f"ERROR: falta {p}")
        jsx_blocks.append(
            f'<script type="text/babel" data-presets="react">\n// ── {name} ──\n'
            + js_escape(p.read_text(encoding="utf-8"))
            + "\n</script>"
        )

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<title>AplicaIA · Reel Player</title>
<style>
@font-face {{
  font-family: 'Inter';
  font-style: normal;
  font-weight: 100 900;
  font-display: block;
  src: url(data:font/woff2;base64,{b64(VENDOR / 'inter.woff2')}) format('woff2');
}}
@font-face {{
  font-family: 'JetBrains Mono';
  font-style: normal;
  font-weight: 100 800;
  font-display: block;
  src: url(data:font/woff2;base64,{b64(VENDOR / 'jbmono.woff2')}) format('woff2');
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #000; }}
</style>
</head>
<body>
<div id="root"></div>
<script>{js_escape((VENDOR / 'react.js').read_text(encoding='utf-8'))}</script>
<script>{js_escape((VENDOR / 'react-dom.js').read_text(encoding='utf-8'))}</script>
<script>{js_escape((VENDOR / 'babel.js').read_text(encoding='utf-8'))}</script>
{chr(10).join(jsx_blocks)}
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"✓ Player OK: {OUT}  ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
