#!/usr/bin/env python3
"""
render_reel.py — Reel animado AplicaIA: JSON → MP4 1080×1920.

Carga posts/templates/reel-player.html (autocontenido) en chromium headless,
avanza el playhead frame a frame (window.__seek es determinístico: mismo JSON
→ mismo video) y compone el MP4 con ffmpeg + música de fondo.

Además genera la PORTADA (<output>-cover.jpg, 1080×1920): el frame del hook ya
entrado del todo. Va a Instagram como `instagramThumbnail` — sin ella IG usa el
frame 0, que con tipografía cinética es negro. Y aplica un piso de duración de
10s: si el guión queda corto, sostiene el cierre (CTA) hasta llegar al mínimo.

Uso:
    python3 posts/render_reel.py posts/AAAA-MM-DD/reel-data.json -o posts/AAAA-MM-DD/reel.mp4
    # deja también posts/AAAA-MM-DD/reel-cover.jpg (portada para instagramThumbnail)

JSON de entrada (ver posts/examples/reels/ y posts/templates/reels-manifest.json):
    {
      "template": "anuncio" | "lanzamiento" | "tips" | "countdown" | "caso" | "metricas",
      "music":    "<id>",             // opcional: pista de posts/assets/music/<id>.mp3
                                      //   (catálogo: posts/assets/music/music-manifest.json)
      "content":  { ... }             // campos de la plantilla; lo no seteado usa defaults
    }

El acento es SIEMPRE #FACC15 (amarillo APLICA IA): identidad de marca. Cualquier
"accent" que venga en el JSON se ignora y se fuerza el amarillo.

Requiere: playwright con chromium; ffmpeg en PATH o `pip install imageio-ffmpeg`.
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
PLAYER = ROOT / "templates" / "reel-player.html"
MUSIC_DIR = ROOT / "assets" / "music"
DEFAULT_AUDIO = ROOT / "assets" / "reel-bg.mp3"

TEMPLATE_IDS = {"lanzamiento", "anuncio", "tips", "countdown", "caso", "metricas"}
W, H = 1080, 1920
# Piso duro de duración: menos de esto no alcanza para explicar la idea.
# Si el guión queda corto, se sostiene el último frame (el cierre con CTA)
# hasta llegar al mínimo — pero lo correcto es escribir escenas con sustancia.
MIN_TOTAL = 10.0


def find_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def cover_time(info: dict) -> float:
    """Momento de la portada: la escena 1 (hook) ya entró del todo, antes del
    flash de transición. Las animaciones son solo de entrada (ease-out), así
    que cerca del final de la escena el frame está completo."""
    sc = info["scenes"][0]
    start, dur = float(sc["start"]), float(sc["dur"])
    return start + max(0.6 * dur, dur - 0.35)


def render_frames(data: dict, frames_dir: Path, fps: int, cover: Path | None) -> dict:
    """Renderiza todos los frames PNG (+ la portada). Devuelve window.__reel."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("ERROR: falta playwright. Instalá con:\n  pip install playwright && playwright install chromium")

    if not PLAYER.exists():
        sys.exit(f"ERROR: no encuentro el player en {PLAYER} (¿corriste posts/build_player.py?)")

    frames_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        # REEL_CHROMIUM: usar un chromium de sistema (p.ej. en la Raspberry) en
        # vez del bundle de playwright. En el sandbox de la routine queda vacío.
        exe = os.environ.get("REEL_CHROMIUM", "").strip() or None
        browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
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

        # Portada para Instagram (instagramThumbnail): el hook completo.
        # Sin esto IG usa el frame 0, que con tipografía cinética es negro.
        if cover:
            t_cov = cover_time(info)
            page.evaluate("t => window.__seek(t)", t_cov)
            page.screenshot(path=str(cover), type="jpeg", quality=92)
            print(f"→ portada: {cover} (frame en t={t_cov:.2f}s)")

        # Piso de duración: sostener el cierre (último frame) hasta MIN_TOTAL.
        n_min = int(math.ceil(MIN_TOTAL * fps))
        if n < n_min:
            print(f"⚠ el guión dura {total:.1f}s < {MIN_TOTAL:.0f}s — se sostiene el cierre hasta {MIN_TOTAL:.0f}s")
            last = frames_dir / f"f_{n - 1:05d}.png"
            for i in range(n, n_min):
                shutil.copyfile(last, frames_dir / f"f_{i:05d}.png")
            info["padded_total"] = MIN_TOTAL

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
    ap.add_argument("--cover", help="Path de la portada JPEG (default: <output>-cover.jpg)")
    ap.add_argument("--no-cover", action="store_true", help="No generar portada")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    data = json.loads(raw)

    # Identidad de marca: el acento es siempre el amarillo APLICA IA.
    if data.get("accent") not in (None, "#FACC15"):
        print(f"⚠ accent '{data.get('accent')}' ignorado — la marca usa solo #FACC15")
    data["accent"] = "#FACC15"

    tpl = data.get("template")
    if tpl not in TEMPLATE_IDS:
        sys.exit(f"ERROR: template '{tpl}' inválido. Opciones: {sorted(TEMPLATE_IDS)}")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.audio == "none":
        audio = None
    elif args.audio:
        audio = Path(args.audio)
    elif data.get("music"):
        audio = MUSIC_DIR / f"{data['music']}.mp3"
        if not audio.is_file():
            print(f"⚠ música '{data['music']}' no está en {MUSIC_DIR} — uso la default")
            audio = DEFAULT_AUDIO
    else:
        audio = DEFAULT_AUDIO

    if args.no_cover:
        cover = None
    else:
        cover = Path(args.cover) if args.cover else out.parent / (out.stem + "-cover.jpg")

    tmp = None
    if args.keep_frames:
        frames_dir = out.parent / (out.stem + "-frames")
    else:
        tmp = tempfile.TemporaryDirectory(prefix="reel-frames-")
        frames_dir = Path(tmp.name)

    info = render_frames(data, frames_dir, args.fps, cover)
    total = float(info.get("padded_total") or info["total"])
    if total > 90:
        print(f"⚠ dura {total:.0f}s (>90s recomendado por Reels)")

    encode(frames_dir, out, args.fps, total, audio)
    if tmp:
        tmp.cleanup()

    sz = out.stat().st_size
    print(f"✓ Reel OK: {out}  ({sz // 1024} KB, {total:.1f}s, {W}x{H}@{args.fps}fps, "
          f"audio={'sí' if audio else 'mudo'}"
          f"{', portada=' + cover.name if cover else ''})")


if __name__ == "__main__":
    main()
