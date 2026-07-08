#!/usr/bin/env python3
"""
render_reel.py — Reel animado AplicaIA: JSON → MP4 1080×1920.

Carga posts/templates/reel-player.html (autocontenido) en chromium headless,
avanza el playhead frame a frame (window.__seek es determinístico: mismo JSON
→ mismo video) y compone el MP4 con ffmpeg + música de fondo.

Uso:
    python3 posts/render_reel.py posts/AAAA-MM-DD/reel-data.json -o posts/AAAA-MM-DD/reel.mp4

JSON de entrada (ver posts/examples/reels/ y posts/templates/reels-manifest.json):
    {
      "template": "anuncio" | "lanzamiento" | "tips" | "countdown" | "caso" | "metricas",
      "accent":   "#FACC15",          // opcional (default amarillo APLICA IA)
      "content":  { ... }             // campos de la plantilla; lo no seteado usa defaults
    }

Requiere: playwright con chromium; ffmpeg en PATH o `pip install imageio-ffmpeg`.
"""

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
PLAYER = ROOT / "templates" / "reel-player.html"
DEFAULT_AUDIO = ROOT / "assets" / "reel-bg.mp3"

TEMPLATE_IDS = {"lanzamiento", "anuncio", "tips", "countdown", "caso", "metricas"}
W, H = 1080, 1920


def find_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def render_frames(data: dict, frames_dir: Path, fps: int) -> dict:
    """Renderiza todos los frames PNG. Devuelve window.__reel (total, scenes)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("ERROR: falta playwright. Instalá con:\n  pip install playwright && playwright install chromium")

    if not PLAYER.exists():
        sys.exit(f"ERROR: no encuentro el player en {PLAYER} (¿corriste posts/build_player.py?)")

    frames_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=1)
        page = ctx.new_page()
        page.add_init_script(f"window.DATA = {json.dumps(data, ensure_ascii=False)};")
        page.goto(PLAYER.resolve().as_uri(), wait_until="load")
        # babel compila los JSX en la carga: dar margen
        page.wait_for_selector('body[data-player-ready="1"]', timeout=60_000)

        info = page.evaluate("window.__reel")
        total = float(info["total"])
        n = int(math.ceil(total * fps))
        print(f"→ template={info['template']}  total={total:.2f}s  escenas={len(info['scenes'])}  frames={n}@{fps}fps")

        for i in range(n):
            t = min(total - 1e-4, i / fps)
            page.evaluate("t => window.__seek(t)", t)
            page.screenshot(path=str(frames_dir / f"f_{i:05d}.png"))
            if i % (fps * 3) == 0:
                print(f"  frame {i}/{n} ({t:.1f}s)")

        browser.close()
    return info


def encode(frames_dir: Path, out: Path, fps: int, total: float, audio: Path | None):
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        sys.exit("FATAL: no encuentro ffmpeg (ni en PATH ni vía imageio-ffmpeg).\n"
                 "  Instalá: pip install imageio-ffmpeg   (o apt-get install ffmpeg)")

    cmd = [ffmpeg, "-y", "-framerate", str(fps), "-i", str(frames_dir / "f_%05d.png")]
    if audio and audio.is_file():
        cmd += ["-stream_loop", "-1", "-i", str(audio)]
        afade = f"afade=t=in:d=0.5,afade=t=out:st={max(0.0, total - 1):.2f}:d=1"
        cmd += ["-af", afade, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "128k", "-ar", "44100"]
    else:
        print("  (sin audio: no se encontró la pista)")
    cmd += [
        "-c:v", "libx264", "-preset", "medium", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-r", str(fps),
        "-shortest", "-movflags", "+faststart",
        str(out),
    ]
    r = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-2000:])
        sys.exit(f"FATAL: ffmpeg salió con código {r.returncode}")


def main():
    ap = argparse.ArgumentParser(description="Reel animado AplicaIA desde JSON (plantillas reel-src).")
    ap.add_argument("input", help="Path al JSON del reel, o '-' para stdin")
    ap.add_argument("-o", "--output", required=True, help="MP4 de salida")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--audio", help=f"Pista de audio (default: {DEFAULT_AUDIO.name}; 'none' = mudo)")
    ap.add_argument("--keep-frames", action="store_true", help="No borrar los PNG intermedios")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    data = json.loads(raw)

    tpl = data.get("template")
    if tpl not in TEMPLATE_IDS:
        sys.exit(f"ERROR: template '{tpl}' inválido. Opciones: {sorted(TEMPLATE_IDS)}")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.audio == "none":
        audio = None
    elif args.audio:
        audio = Path(args.audio)
    else:
        audio = DEFAULT_AUDIO

    tmp = None
    if args.keep_frames:
        frames_dir = out.parent / (out.stem + "-frames")
    else:
        tmp = tempfile.TemporaryDirectory(prefix="reel-frames-")
        frames_dir = Path(tmp.name)

    info = render_frames(data, frames_dir, args.fps)
    total = float(info["total"])
    if total > 90:
        print(f"⚠ dura {total:.0f}s (>90s recomendado por Reels)")

    encode(frames_dir, out, args.fps, total, audio)
    if tmp:
        tmp.cleanup()

    sz = out.stat().st_size
    print(f"✓ Reel OK: {out}  ({sz // 1024} KB, {total:.1f}s, {W}x{H}@{args.fps}fps, "
          f"audio={'sí' if audio else 'mudo'})")


if __name__ == "__main__":
    main()
