#!/usr/bin/env bash
# Bootstrap idempotente para la Routine "Reel diario Claude".
# Reemplaza al Paso 0 inline: el environment remoto arranca vacío en cada corrida.
#
# Uso desde la routine:
#   cd /home/user && bash aplicaia-files/posts/bootstrap.sh || exit 1
#
# Arregla dos problemas conocidos del environment:
#   1) `pip install playwright` agarra una versión cuyo build de chromium NO está
#      en la imagen (/opt/pw-browsers trae chromium-1194). Acá fijamos la versión
#      de playwright que matchea el chromium ya instalado, probando candidatos.
#   2) `playwright install --with-deps` falla por repos de apt sin firmar; no hace
#      falta: el chromium ya viene horneado en la imagen.

set -euo pipefail

REPO_DIR="${REPO_DIR:-/home/user/aplicaia-files}"
REPO_URL="https://github.com/hpcoolsense/aplicaia-files.git"

echo "== [bootstrap] repo =="
cd /home/user
if [ ! -d "$REPO_DIR" ]; then
  git clone "$REPO_URL" "$REPO_DIR"
fi
cd "$REPO_DIR"
git pull origin main

echo "== [bootstrap] archivos base (pipeline reel animado) =="
test -f posts/render_reel.py || { echo "FATAL: falta render_reel.py"; exit 1; }
test -f posts/templates/reel-player.html || { echo "FATAL: falta reel-player.html (correr posts/build_player.py)"; exit 1; }
test -f posts/templates/reels-manifest.json || { echo "FATAL: falta reels-manifest.json"; exit 1; }
test -d posts/examples/reels || { echo "FATAL: faltan examples/reels"; exit 1; }
test -f posts/assets/reel-bg.mp3 || { echo "FATAL: falta la música reel-bg.mp3"; exit 1; }
MCOUNT=$(ls posts/assets/music/*.mp3 2>/dev/null | wc -l)
[ "$MCOUNT" -ge 6 ] || { echo "FATAL: catálogo de música incompleto ($MCOUNT pistas)"; exit 1; }
test -f posts/assets/music/music-manifest.json || { echo "FATAL: falta music-manifest.json"; exit 1; }

echo "== [bootstrap] playwright (pin que matchea el chromium de la imagen) =="
# Probamos lanzar chromium; si falla, vamos bajando a versiones que matcheen el
# chromium preinstalado. La lista cubre los builds más comunes de la imagen.
launch_ok() {
  python3 - <<'PY' 2>/dev/null
from playwright.sync_api import sync_playwright
p = sync_playwright().start(); b = p.chromium.launch(); b.close(); p.stop()
PY
}

if ! python3 -c "import playwright" 2>/dev/null || ! launch_ok; then
  for v in 1.56.0 1.55.0 1.57.0 1.58.0 1.54.0; do
    pip3 install --quiet "playwright==$v" 2>/dev/null || continue
    if launch_ok; then echo "  -> playwright==$v OK"; PW_OK=1; break; fi
    echo "  -> $v no matchea, sigo"
  done
  [ "${PW_OK:-}" = "1" ] || { echo "FATAL: ningún playwright matchea el chromium de la imagen"; exit 1; }
else
  echo "  -> playwright actual ya lanza chromium OK"
fi

echo "== [bootstrap] ffmpeg (estático vía pip; el entorno evita apt) =="
python3 -c "import imageio_ffmpeg" 2>/dev/null || pip3 install --quiet imageio-ffmpeg
python3 -c "import imageio_ffmpeg; print('  -> ffmpeg:', imageio_ffmpeg.get_ffmpeg_exe())" \
  || { echo "FATAL: no ffmpeg"; exit 1; }

echo "== [bootstrap] git config =="
git config user.email "tomyrengi@gmail.com"
git config user.name "aplicaia-routine"
git config commit.gpgsign false

echo "== [bootstrap] remote auth =="
if [ -n "${GH_TOKEN:-}" ]; then
  git remote set-url origin "https://${GH_TOKEN}@github.com/hpcoolsense/aplicaia-files.git"
  echo "  -> remote via GH_TOKEN"
else
  echo "FATAL: GH_TOKEN no está configurado en el environment"; exit 1
fi

echo "== [bootstrap] OK =="
