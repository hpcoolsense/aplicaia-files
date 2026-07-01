#!/usr/bin/env python3
"""
make_reel.py — Compone los slides verticales 1080x1920 de un día AplicaIA en un
Reel (9:16) con transición "slideup" (cada slide sale hacia arriba y entra el
siguiente desde abajo) y música de fondo.

No re-renderiza ni toca los slides: los toma tal cual (cover a 1080x1920, sin
franjas) y arma el MP4 con ffmpeg. Si el slide no fuese 9:16, lo llena al centro.

Uso:
    python3 make_reel.py posts/2026-06-28 -o posts/2026-06-28/reel.mp4
    python3 make_reel.py posts/2026-06-28 --transition fade --slide-dur 3.2
    python3 make_reel.py posts/2026-06-28 --audio posts/assets/reel-bg.mp3
    python3 make_reel.py --images a.png b.png c.png -o reel.mp4

Requiere: ffmpeg en el PATH (con libx264). Nada de pip.
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

W, H = 1080, 1920          # lienzo vertical del Reel (9:16)
FPS = 30


def find_ffmpeg():
    """ffmpeg del sistema, o el binario estático de imageio-ffmpeg (pip).
    El entorno de la routine evita apt, así que imageio-ffmpeg es el fallback."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def find_slides(day_dir: str):
    pats = sorted(glob.glob(os.path.join(day_dir, "*-imagen.png")))
    return pats


def build_filter(n, durs, xfade_dur, transition):
    """Devuelve (filter_complex, label_final)."""
    parts = []
    # 1) Cada imagen -> 1080x1920, cuadrada centrada sobre negro, fps/format fijos.
    for i in range(n):
        # Fuente ya 9:16 (1080x1920): cover + crop = identidad. Para cualquier
        # otro aspecto, llena el frame vertical y recorta al centro (sin franjas).
        chain = (
            f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},"
            f"setsar=1,format=yuv420p,setpts=PTS-STARTPTS,fps={FPS},settb=AVTB[s{i}]"
        )
        parts.append(chain)

    # 2) Cadena de xfade encadenando s0..s(n-1).
    if n == 1:
        return ";".join(parts), "s0"

    prev = "s0"
    cum = durs[0]
    for j in range(1, n):
        offset = cum - xfade_dur
        out = f"x{j}" if j < n - 1 else "vout"
        parts.append(
            f"[{prev}][s{j}]xfade=transition={transition}:"
            f"duration={xfade_dur}:offset={offset:.3f}[{out}]"
        )
        cum += durs[j] - xfade_dur
        prev = out
    return ";".join(parts), "vout"


def main():
    ap = argparse.ArgumentParser(description="Carrusel de slides -> Reel vertical 9:16.")
    ap.add_argument("day_dir", nargs="?", help="Carpeta posts/AAAA-MM-DD con NN-imagen.png")
    ap.add_argument("--images", nargs="+", help="Lista explícita de PNGs (en orden)")
    ap.add_argument("-o", "--output", help="MP4 de salida (default: <day_dir>/reel.mp4)")
    ap.add_argument("--slide-dur", type=float, default=3.0, help="Segundos por slide (default 3.0)")
    ap.add_argument("--xfade-dur", type=float, default=0.6, help="Duración de la transición (default 0.6)")
    ap.add_argument("--hold-first", type=float, default=0.6, help="Extra en la portada (default +0.6)")
    ap.add_argument("--hold-last", type=float, default=1.4, help="Extra en el cierre/CTA (default +1.4)")
    ap.add_argument("--transition", default="slideup",
                    help="Transición xfade: slideup (sale arriba, entra desde abajo), slideleft, fade... (default slideup)")
    ap.add_argument("--audio", help="Pista de audio (mp3/m4a). Si falta, usa posts/assets/reel-bg.mp3; si tampoco está, silencio.")
    ap.add_argument("--fps", type=int, default=FPS)
    args = ap.parse_args()

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        sys.exit("FATAL: no encuentro ffmpeg (ni en PATH ni vía imageio-ffmpeg).\n"
                 "  Instalá: pip install imageio-ffmpeg   (o apt-get install ffmpeg)")

    if args.images:
        slides = args.images
    elif args.day_dir:
        slides = find_slides(args.day_dir)
    else:
        sys.exit("FATAL: pasá una carpeta día o --images")

    slides = [s for s in slides if Path(s).is_file()]
    n = len(slides)
    if n < 2:
        sys.exit(f"FATAL: necesito >=2 slides, encontré {n}")

    out = args.output or os.path.join(args.day_dir or ".", "reel.mp4")

    durs = [args.slide_dur] * n
    durs[0] += args.hold_first
    durs[-1] += args.hold_last

    fcomplex, final = build_filter(n, durs, args.xfade_dur, args.transition)
    total = sum(durs) - (n - 1) * args.xfade_dur

    # Audio: --audio explícito, o pista fija posts/assets/reel-bg.mp3, o silencio.
    default_bg = Path(__file__).resolve().parent / "assets" / "reel-bg.mp3"
    audio = args.audio if (args.audio and Path(args.audio).is_file()) else \
        (str(default_bg) if default_bg.is_file() else None)

    cmd = [ffmpeg, "-y"]
    for i, s in enumerate(slides):
        cmd += ["-loop", "1", "-framerate", str(args.fps), "-t", f"{durs[i]:.3f}", "-i", s]

    if audio:
        cmd += ["-stream_loop", "-1", "-i", audio]              # loopea si dura menos que el reel
        afilter = f"afade=t=in:d=0.5,afade=t=out:st={max(0.0, total - 1):.2f}:d=1"
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]  # silencio compatible
        afilter = None

    cmd += ["-filter_complex", fcomplex, "-map", f"[{final}]", "-map", f"{n}:a"]
    if afilter:
        cmd += ["-af", afilter]
    cmd += [
        "-c:v", "libx264", "-preset", "medium", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-r", str(args.fps),
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-shortest", "-movflags", "+faststart",
        out,
    ]

    print("→ slides:", *[os.path.basename(s) for s in slides])
    print("→ durs:", [round(d, 2) for d in durs], "| xfade:", args.xfade_dur, "| transition:", args.transition)
    r = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-2000:])
        sys.exit(f"FATAL: ffmpeg salió con código {r.returncode}")

    print(f"✓ Reel OK: {out}  (~{total:.1f}s, {n} slides, {W}x{H}, audio={'sí' if audio else 'mudo'})")


if __name__ == "__main__":
    main()
