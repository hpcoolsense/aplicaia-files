# AplicaIA — Sistema de plantillas Instagram

Implementación del handoff de Claude Design `VmDOC3fwyUpmO8i24bzg5g`.
Reproduce las **6 plantillas 1080×1080** del archivo `Instagram Templates.html`
de forma parametrizada: la Routine pasa un JSON, sale un PNG listo para subir.

## Estructura

```
posts/
├── templates/
│   └── instagram-templates.html    ← renderer (HTML+CSS+JS, todo inline)
├── render.py                        ← script: JSON → PNG 1080×1080
├── examples/
│   ├── stat-example.json
│   ├── review-example.json
│   ├── tips-example.json
│   ├── quote-example.json
│   ├── compare-example.json
│   └── announce-example.json
├── renders/                         ← outputs (se crea solo)
└── README.md
```

## Las 6 plantillas

| Tipo | Para qué sirve | Campos clave |
|---|---|---|
| `stat` | Dato impactante con fuente | `number`, `unit`, `description`, `source` |
| `review` | Reseña de herramienta con score | `name`, `category`, `score` (0–5), `summary`, `tags[]` |
| `tips` | 3–4 tips numerados ("guardalo") | `titleLine1/2`, `items[]` (title + desc) |
| `quote` | Testimonio con atribución | `text`, `initials`, `name`, `role` |
| `compare` | Antes/después de un proceso | `before.metric/unit/...`, `after.metric/unit/...` |
| `announce` | Lanzamiento, evento, novedad | `pillLabel`, `date`, `titleLine1/2`, `lead` |

## Cómo se usa

### Requisitos
```bash
pip install playwright
playwright install chromium
```

### Renderizar
```bash
# desde un archivo
python render.py examples/stat-example.json -o renders/post.png

# desde stdin (útil en pipelines)
cat data.json | python render.py - -o out.png

# sin -o: usa renders/<type>-<timestamp>.png
python render.py data.json
```

### Output
PNG **2160×2160** (1080×1080 @2x para nitidez). Instagram lo acepta directo en el feed.

## Cómo escribir el JSON

### Convenciones globales

- **Mayúsculas en `headerLabel`, `footerTag`, `cta`** — la tipografía es mono uppercase y el CSS ya aplica `text-transform`, pero conviene escribirlo así igual para legibilidad del JSON.
- **`**texto**` para negrita amarilla en campos `rich`** — los campos marcados como "soportan rich" (ver schemas abajo) convierten `**palabra**` a `<strong>palabra</strong>` que el CSS pinta en amarillo o blanco según corresponda.
- **`titleLine1` + `titleLine2`/`titleLine2Accent`**: los títulos grandes están partidos en 2 líneas para controlar el salto. La segunda línea (o el "Accent") va en amarillo.
- **`headerLabel` opcional**: si no lo pasás, cada plantilla tiene un default razonable.

### Schema por tipo

#### 1. `stat` — dato grande
```json
{
  "type": "stat",
  "headerLabel": "DATO",                    // opcional
  "eyebrow": "Productividad · 2026",        // chip amarillo arriba del número
  "number": "73",                            // número grande (string)
  "unit": "%",                               // unidad blanca al lado del número
  "description": "de las empresas que **agentes IA** ...",  // rich (negrita = amarillo)
  "source": "McKinsey, Estado IA 2026",     // sin "Fuente ·" (se agrega solo)
  "cta": "VER MÁS"                           // opcional
}
```

#### 2. `review` — reseña de herramienta
```json
{
  "type": "review",
  "verdict": "RECOMENDADA",                 // o "EVITAR" / "INTERESANTE" / etc
  "verdictWarn": false,                      // true = pill grisado en vez de amarillo
  "category": "Automatización · No-code",
  "name": "Cursor 2.0",                      // título grande
  "score": 4,                                // 0-5, entero, llena N estrellas
  "scoreLabel": "4.2",                       // lo que se muestra al lado de "/5"
  "summary": "Editor con **agentes IA** ...", // rich
  "tags": ["IDE", "$20/mes", "Mac"],         // pills inferiores
  "footerTag": "#ToolReview",
  "cta": "MÁS REVIEWS"
}
```

#### 3. `tips` — lista numerada
```json
{
  "type": "tips",
  "eyebrow": "Antes de implementar",
  "titleLine1": "4 cosas que",               // blanco
  "titleLine2": "nunca falta hacer",         // amarillo
  "items": [                                  // 3 o 4 items (probado hasta 4)
    {"title": "Medir el proceso a mano", "desc": "Si no podés contar..."},
    {"title": "Empezar por una tarea", "desc": "Un solo cuello..."},
    {"title": "...", "desc": "..."},
    {"title": "...", "desc": "..."}
  ],
  "cta": "GUARDÁ ESTE POST"
}
```

#### 4. `quote` — testimonio
```json
{
  "type": "quote",
  "text": "Implementamos un agente de IA y nuestro equipo de soporte ...",
  "initials": "MR",                          // 2 letras para el avatar
  "name": "Martín Rodríguez",
  "role": "CTO · BioArq"
}
```

#### 5. `compare` — antes/después
```json
{
  "type": "compare",
  "eyebrow": "Caso · onboarding cliente",
  "titleLine1": "De días",                   // blanco
  "titleLine2Pre": "a",                       // blanco
  "titleLine2Accent": "minutos.",             // amarillo
  "before": {
    "label": "Antes",
    "metric": "4",
    "unit": "días",
    "headline": "Onboarding manual con 5 mails y 2 calls.",
    "desc": "Validación humana en cada paso..."
  },
  "after": {
    "label": "Después",
    "metric": "12",
    "unit": "min",
    "headline": "Agente IA que valida, escala excepciones y firma.",
    "desc": "95% de los casos resueltos sin intervención humana."
  },
  "footerTag": "BIOARQ AGENT",
  "cta": "VER CASO"
}
```

#### 6. `announce` — anuncio
```json
{
  "type": "announce",
  "pillIcon": "✨",                          // emoji del pill (opcional)
  "pillLabel": "Novedad",
  "date": "25 · MAY · 2026",
  "kicker": "Lanzamiento",
  "titleLine1": "Agentes",                   // blanco
  "titleLine2Pre": "IA",                      // blanco
  "titleLine2Accent": "para todos.",          // amarillo
  "lead": "Lanzamos un **nuevo programa** ...", // rich
  "cta": "Link en la bio"
}
```

## Reglas de diseño (no romper)

Sacadas directo del handoff de Claude Design. Si querés cambiar algo, hacelo
en `templates/instagram-templates.html`, **no en el JSON**:

- **Paleta**: fondo `#000`, ink `#F5F5F7`, dim `#A1A1AA`, mute `#71717A`, **amarillo `#FACC15`**.
- **Tipografía**: Inter 900 para titulares (tracking `-0.04em` a `-0.06em`), Inter 500-700 para body, JetBrains Mono para todo lo uppercase con tracking ≥ `0.2em`.
- **Wordmark**: "Aplica" en amarillo, " IA" en blanco. Siempre Inter 900 con tracking `-0.05em`.
- **Header**: dot amarillo pulsante a la izquierda, wordmark a la derecha (en algunas no hay wordmark — respetar).
- **Grain overlay**: pattern radial sutil sobre todo. No tocar.
- **Glow amarillo**: gradientes radiales en `rgba(250,204,21, 0.06-0.12)` en cada plantilla. Cada una tiene su composición específica.

## Integración con la Routine

La Routine de Claude Code:

1. Investiga el tema de la semana.
2. **Elige el tipo de plantilla** según el contenido:
   - Hay un dato fuerte → `stat`
   - Estoy hablando de una herramienta concreta → `review`
   - 3-4 puntos accionables → `tips`
   - Tengo un cliente que dijo algo bueno → `quote`
   - Caso real con métrica de mejora → `compare`
   - Algo nuevo de AplicaIA → `announce`
3. Genera el JSON con los campos del schema correspondiente.
4. Corre `python render.py data.json -o post.png`.
5. Sube `post.png` + caption a Instagram vía MCP, en modo DRAFT.

## Verificación

Las 6 plantillas fueron renderizadas y verificadas pixel-perfect contra el
diseño original del handoff. Ver `renders/test-*.png` (incluidos en este bundle).

Si el render falla o sale corrido, lo más probable es:
- **Texto muy largo** → desborda. La Routine debe respetar los límites:
  - `stat.description`: máx 2-3 líneas (~110 chars)
  - `review.summary`: máx 4 líneas (~180 chars)
  - `tips.items[].desc`: máx 2 líneas (~90 chars cada uno)
  - `quote.text`: máx 5 líneas (~150 chars)
  - `announce.lead`: máx 4 líneas (~180 chars)
- **Fuentes no cargadas** → red bloqueando Google Fonts. En la Routine, asegurate
  de que el environment tiene acceso a `fonts.googleapis.com` y `fonts.gstatic.com`.

## Origen

Implementación derivada del handoff de **Claude Design** (claude.ai/design),
proyecto AplicaIA, archivo `Instagram Templates.html`. Los tokens visuales,
tipografía, gradientes y composición son del diseño original — esta capa
sólo agrega parametrización y rendering automatizado.
