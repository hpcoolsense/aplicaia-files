#!/usr/bin/env python3
"""
AplicaIA Instagram Template Renderer
====================================

Toma un JSON con datos de un post, lo renderiza usando templates/instagram-templates.html
y guarda un PNG 1080x1080 listo para subir a Instagram.

Uso:
    python render.py examples/stat-example.json -o renders/post.png
    cat data.json | python render.py - -o out.png   # stdin
    python render.py data.json                       # default: renders/<type>-<timestamp>.png

Requiere:
    pip install playwright
    playwright install chromium
"""

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
TEMPLATE = ROOT / "templates" / "instagram-templates.html"


def render(data: dict, out_path: Path, template: Path = TEMPLATE, height: int = 1080, scale: int = 2) -> Path:
    """Renderiza el dict `data` al PNG `out_path`. Retorna el path final.

    template/height/scale permiten el modo reel (1080x1920 @1x) sin romper
    el modo feed por defecto (1080x1080 @2x).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("ERROR: falta playwright. Instalá con:\n  pip install playwright && playwright install chromium")

    if not template.exists():
        sys.exit(f"ERROR: no encuentro la plantilla en {template}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": 1080, "height": height},
            device_scale_factor=scale,   # PNG @scale para nitidez
        )
        page = ctx.new_page()

        # Inyectamos window.DATA antes de que corra el script de la plantilla
        page.add_init_script(f"window.DATA = {json.dumps(data, ensure_ascii=False)};")

        # file:// para que cargue sin servidor local
        page.goto(template.resolve().as_uri(), wait_until="networkidle")

        # Esperamos a que el script marque que fuentes y layout están listos
        page.wait_for_selector('body[data-render-ready="1"]', timeout=15_000)
        page.wait_for_selector('.canvas', timeout=5_000)
        # Margen extra para gradientes/shadows
        page.wait_for_timeout(300)

        canvas = page.locator(".canvas").first
        canvas.screenshot(path=str(out_path), omit_background=False, type="png")

        browser.close()

    print(f"✓ Render OK: {out_path}  ({out_path.stat().st_size // 1024} KB)")
    return out_path


def load_data(src: str) -> dict:
    if src == "-":
        return json.loads(sys.stdin.read())
    return json.loads(Path(src).read_text(encoding="utf-8"))


def default_outpath(data: dict) -> Path:
    t = data.get("type", "post")
    ts = time.strftime("%Y%m%d-%H%M%S")
    return ROOT / "renders" / f"{t}-{ts}.png"


def main():
    ap = argparse.ArgumentParser(description="Renderiza un post de Instagram AplicaIA desde JSON.")
    ap.add_argument("input", help="Path a JSON, o '-' para stdin")
    ap.add_argument("-o", "--output", help="PNG de salida (default: renders/<type>-<timestamp>.png)")
    ap.add_argument("--template", help="HTML de plantilla (default: templates/instagram-templates.html)")
    ap.add_argument("--height", type=int, default=1080, help="Alto del canvas en px (1080 feed / 1920 reel)")
    ap.add_argument("--scale", type=int, default=2, help="device_scale_factor (2 = @2x)")
    ap.add_argument("--reel", action="store_true",
                    help="Atajo: template reel + alto 1920 + scale 1 (salida 1080x1920)")
    args = ap.parse_args()

    data = load_data(args.input)
    out = Path(args.output) if args.output else default_outpath(data)
    if args.reel:
        template = ROOT / "templates" / "instagram-templates-reel.html"
        height, scale = 1920, 1
    else:
        template = Path(args.template) if args.template else TEMPLATE
        height, scale = args.height, args.scale
    render(data, out, template=template, height=height, scale=scale)


if __name__ == "__main__":
    main()
