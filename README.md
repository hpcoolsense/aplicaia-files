# aplicaia-files — Reel diario de AplicaIA

Repositorio de la **Cloud Routine** que publica un Reel diario en Instagram
(@aplicai.ia.ar) sobre novedades del ecosistema Claude. Estética negro/amarillo
APLICA IA, formato 9:16.

> El sistema anterior de **publicaciones/carrusel (feed 1080×1080)** fue removido
> el 2026-07-07 — plantillas, renderer raíz y ejemplos duplicados viven solo en el
> historial de git. Todo lo vigente está en `posts/`.

## Estructura

```
posts/
├── bootstrap.sh                          # Paso 0 de la routine: clone/pull + playwright pineado + remote auth
├── render.py                             # JSON → PNG 1080×1920 (una pantalla del reel)
├── make_reel.py                          # PNGs del día → reel.mp4 (slideup + música)
├── templates/
│   └── instagram-templates-reel.html     # template vertical con los 6 tipos de pantalla
├── examples/                             # schema de referencia de cada tipo (NO inventar campos)
│   ├── announce-example.json             # portada / anuncio
│   ├── stat-example.json                 # número/benchmark
│   ├── review-example.json               # reseña/quote con autor
│   ├── quote-example.json                # cita destacada
│   ├── compare-example.json              # comparativa A vs B
│   └── tips-example.json                 # lista de tips / cierre
├── assets/
│   └── reel-bg.mp3                       # música de fondo (reemplazable, sin copyright)
└── AAAA-MM-DD/                           # una carpeta por reel publicado
    ├── NN-data.json                      # datos de cada pantalla
    ├── NN-imagen.png                     # render 1080×1920
    └── caption.txt                       # caption usado (opcional)

log/
└── temas-publicados.json                 # dedup: qué (feature, ángulo, tema) ya se publicó + post_id
```

## Flujo de un reel

```bash
# 1) renderizar cada pantalla (vertical 1080×1920)
python3 posts/render.py posts/AAAA-MM-DD/NN-data.json -o posts/AAAA-MM-DD/NN-imagen.png

# 2) componer el reel (toma los NN-imagen.png en orden, transición slideup + música)
python3 posts/make_reel.py posts/AAAA-MM-DD -o posts/AAAA-MM-DD/reel.mp4
```

Salida: H.264, 1080×1920, 30 fps, `+faststart`, AAC. ~3 s por pantalla
(portada +0.6 s, cierre +1.4 s), transición 0.6 s. El MP4 **no se commitea**
(solo JSONs y PNGs, para no inflar el repo).

## Reglas del contenido

- 4 a 6 pantallas por reel; la portada es siempre tipo `announce`.
- Los JSON respetan el schema de `posts/examples/` — no inventar campos.
- CTAs de reel ("Mirá el reel completo", "Guardalo"), nunca "pasá las slides".
- Dedup por `(feature_principal, angulo)` contra `log/temas-publicados.json`;
  la reserva se pushea a main ANTES de publicar.

## Requisitos del entorno

- Playwright con chromium (la imagen de la routine lo trae horneado;
  `posts/bootstrap.sh` pinea la versión de playwright que matchea).
- ffmpeg: del sistema o vía `pip install imageio-ffmpeg` (el entorno evita apt).
- `GH_TOKEN` en las variables del environment para el push del dedup.
