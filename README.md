# aplicaia-files — Reel animado diario de AplicaIA

Repositorio de la **Cloud Routine** que publica un Reel diario en Instagram
(@aplicai.ia.ar) sobre novedades del ecosistema Claude. Reels 9:16 de
**tipografía cinética** (plantillas animadas diseñadas en Claude Design) con la
estética APLICA IA y música de fondo.

> Historial: el sistema de publicaciones/carrusel (feed 1080×1080) se removió el
> 2026-07-07, y el slideshow de PNGs con transiciones (v5) fue reemplazado ese
> mismo día por este pipeline de animación real (v6). Todo vive en el historial de git.

## Estructura

```
posts/
├── bootstrap.sh                 # Paso 0 de la routine: clone/pull + playwright pineado + ffmpeg + checks
├── render_reel.py               # reel-data.json → frames (chromium headless) → reel.mp4 (H.264 + música)
├── build_player.py              # re-ensambla reel-player.html tras editar reel-src/ (correrlo a mano)
├── templates/
│   ├── reel-player.html         # player AUTOCONTENIDO (React+Babel+fuentes inline, cero red) — generado
│   ├── reels-manifest.json      # catálogo: cuándo usar cada plantilla, límites, acentos, mapeo ángulo→plantilla
│   └── reel-src/                # fuentes del sistema de diseño (espejo del proyecto Claude Design "AplicaIA")
│       ├── animations.jsx       #   motor de timeline (Sprite, easings, TimelineContext)
│       ├── reel-kinetics.jsx    #   primitivas cinéticas (WordSlam, Cascade, CountUpBig, CTAPill…)
│       ├── reel-templates.jsx   #   las 6 plantillas (lanzamiento, anuncio, tips, countdown, caso, metricas)
│       ├── reel-player.jsx      #   runner headless (window.DATA + window.__seek determinístico)
│       └── vendor/              #   React, Babel standalone y fuentes woff2 (offline)
├── examples/reels/              # schema de referencia del reel-data.json de cada plantilla
├── assets/
│   └── reel-bg.mp3              # música de fondo (reemplazable, sin copyright)
└── AAAA-MM-DD/                  # una carpeta por reel publicado
    ├── reel-data.json           # plantilla + acento + contenido del día (la "fuente" del reel)
    └── caption.txt              # caption usado

log/
└── temas-publicados.json        # dedup: (feature, ángulo, tema) publicados + plantilla + post_id
```

## Flujo de un reel

```bash
# 1) escribir posts/AAAA-MM-DD/reel-data.json
#    (elegir plantilla con posts/templates/reels-manifest.json;
#     copiar el schema de posts/examples/reels/<plantilla>.json)

# 2) renderizar la animación completa
python3 posts/render_reel.py posts/AAAA-MM-DD/reel-data.json -o posts/AAAA-MM-DD/reel.mp4
```

Salida: H.264, 1080×1920, 30 fps, `+faststart`, AAC, con fade de audio. El render
es **determinístico**: mismo JSON → mismo video, frame a frame. El MP4 **no se
commitea** (`.gitignore`); al repo van `reel-data.json` + `caption.txt`.

## Las 6 plantillas

| id | tag | estructura |
|---|---|---|
| `lanzamiento` | Anuncio | palabras que golpean una a una → titular → puntos → CTA |
| `anuncio` | Anuncio | titular por máscaras → palabra gigante de fondo → detalle → CTA |
| `tips` | Tips | hook → 3-5 tips con dígito gigante → CTA de guardado |
| `countdown` | Tips | hook → cuenta regresiva N…1 con número gigante → CTA |
| `caso` | Caso | contexto → problema → métrica count-up → resultado → CTA |
| `metricas` | Caso | título → serie de count-ups → cierre + CTA |

Detalles, límites de texto y guía de acentos: `posts/templates/reels-manifest.json`.

## Editar las plantillas

La fuente de verdad de diseño es el proyecto **"AplicaIA" en claude.ai/design**
(archivos con el mismo nombre). Para actualizar:

1. Bajar el/los `.jsx` modificados a `posts/templates/reel-src/`.
2. `python3 posts/build_player.py` (regenera `reel-player.html`).
3. Probar: `python3 posts/render_reel.py posts/examples/reels/anuncio.json -o /tmp/test.mp4`.
4. Commit de `reel-src/` + `reel-player.html` juntos.

## Requisitos del entorno

- Playwright con chromium (la imagen de la routine lo trae horneado;
  `posts/bootstrap.sh` pinea la versión de playwright que matchea).
- ffmpeg: `bootstrap.sh` lo resuelve vía `pip install imageio-ffmpeg` (sin apt).
- `GH_TOKEN` en las variables del environment para el push del dedup.
