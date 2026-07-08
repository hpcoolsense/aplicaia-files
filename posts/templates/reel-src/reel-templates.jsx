// reel-templates.jsx — 6 plantillas de reel AplicaIA (tipografía cinética)
// Cada plantilla: defaults (contenido editable), sections (config del editor),
// scenes(c) → [{key, label, dur, align, node}]
// Fuente de verdad de diseño: claude.ai/design proyecto "AplicaIA" (mismo nombre de archivo).

const pad2 = (n) => String(n).padStart(2, '0');

const REEL_TEMPLATES = [

  // ── 1 · ANUNCIO — Lanzamiento ──────────────────────────────────────────
  {
    id: 'lanzamiento', name: 'Lanzamiento', tag: 'Anuncio',
    desc: 'Palabras que golpean una a una + puntos + cierre',
    defaults: {
      hookWords: 'Ya\nestá\n*online.*', durHook: 2.8,
      kicker: 'Lanzamiento', titulo: 'La nueva landing de *AplicaIA* ya está en producción.', durTitulo: 3.2,
      puntos: 'IA aplicada a problemas reales\nCasos medibles en producción\nAgenda abierta esta semana', durPuntos: 3.6,
      cta: 'Link en la bio', handle: '@aplicaia', durCta: 2.8,
    },
    sections: [
      { title: 'Hook', durKey: 'durHook', fields: [{ key: 'hookWords', type: 'multi', label: 'Palabras — una por línea', rows: 3 }] },
      { title: 'Titular', durKey: 'durTitulo', fields: [{ key: 'kicker', type: 'text', label: 'Etiqueta' }, { key: 'titulo', type: 'multi', label: 'Frase', rows: 3 }] },
      { title: 'Puntos', durKey: 'durPuntos', fields: [{ key: 'puntos', type: 'multi', label: 'Uno por línea', rows: 3 }] },
      { title: 'Cierre', durKey: 'durCta', fields: [{ key: 'cta', type: 'text', label: 'Botón' }, { key: 'handle', type: 'text', label: 'Subtexto' }] },
    ],
    scenes: (c) => [
      { key: 'hook', label: 'Hook', dur: +c.durHook, align: 'center', node: <WordSlam words={splitLines(c.hookWords)} /> },
      { key: 'titulo', label: 'Titular', dur: +c.durTitulo, align: 'center', node: <><Kicker text={c.kicker} /><Cascade text={c.titulo} size={96} align="center" weight={900} /></> },
      { key: 'puntos', label: 'Puntos', dur: +c.durPuntos, align: 'left', node: <ListReveal items={splitLines(c.puntos)} size={66} /> },
      { key: 'cta', label: 'Cierre', dur: +c.durCta, align: 'center', node: <CTAPill text={c.cta} sub={c.handle} /> },
    ],
  },

  // ── 2 · ANUNCIO — Novedad ──────────────────────────────────────────────
  {
    id: 'anuncio', name: 'Novedad', tag: 'Anuncio',
    desc: 'Titular por máscaras + palabra gigante de fondo',
    defaults: {
      kicker: 'Nuevo en AplicaIA', titulo: 'Dejá de\nimaginar la IA.\n*Aplicala.*', durTitulo: 3.2,
      fraseWord: 'REAL', frase: 'Automatización con impacto *real* en tu operación.', durFrase: 3.0,
      detalle: 'Diagnóstico, implementación y medición. Sin humo.', durDetalle: 2.8,
      cta: 'Conocé cómo', handle: '@aplicaia', durCta: 2.8,
    },
    sections: [
      { title: 'Titular', durKey: 'durTitulo', fields: [{ key: 'kicker', type: 'text', label: 'Etiqueta' }, { key: 'titulo', type: 'multi', label: 'Líneas — una por línea', rows: 3 }] },
      { title: 'Frase', durKey: 'durFrase', fields: [{ key: 'fraseWord', type: 'text', label: 'Palabra de fondo' }, { key: 'frase', type: 'multi', label: 'Frase', rows: 2 }] },
      { title: 'Detalle', durKey: 'durDetalle', fields: [{ key: 'detalle', type: 'multi', label: 'Texto', rows: 2 }] },
      { title: 'Cierre', durKey: 'durCta', fields: [{ key: 'cta', type: 'text', label: 'Botón' }, { key: 'handle', type: 'text', label: 'Subtexto' }] },
    ],
    scenes: (c) => [
      { key: 'titulo', label: 'Titular', dur: +c.durTitulo, align: 'center', node: <><Kicker text={c.kicker} /><StackReveal lines={splitLines(c.titulo)} base={150} /></> },
      { key: 'frase', label: 'Frase', dur: +c.durFrase, align: 'center', node: <><GhostWord word={c.fraseWord} /><Cascade text={c.frase} size={88} align="center" weight={900} /></> },
      { key: 'detalle', label: 'Detalle', dur: +c.durDetalle, align: 'center', node: <Cascade text={c.detalle} size={72} align="center" /> },
      { key: 'cta', label: 'Cierre', dur: +c.durCta, align: 'center', node: <CTAPill text={c.cta} sub={c.handle} /> },
    ],
  },

  // ── 3 · TIPS — Lista ───────────────────────────────────────────────────
  {
    id: 'tips', name: 'Tips · Lista', tag: 'Tips',
    desc: 'Hook + 3-5 tips con dígito gigante + cierre',
    listKey: 'tips',
    defaults: {
      hookTop: 'Guardá esto', hook: '5 usos de IA que podés *copiar hoy*', durHook: 2.8,
      tips: [
        { text: 'Respuestas automáticas que suenan humanas', dur: 2.8 },
        { text: 'Reportes que se escriben solos', dur: 2.8 },
        { text: 'Errores detectados antes que el cliente', dur: 2.8 },
        { text: 'Onboarding guiado por IA', dur: 2.8 },
        { text: 'Seguimiento de leads 24/7', dur: 2.8 },
      ],
      cierre: 'Guardalo para después', handle: '@aplicaia', durCierre: 2.8,
    },
    sections: [
      { title: 'Hook', durKey: 'durHook', fields: [{ key: 'hookTop', type: 'text', label: 'Etiqueta' }, { key: 'hook', type: 'multi', label: 'Frase', rows: 2 }] },
      { title: 'Tips', type: 'list', listKey: 'tips', min: 3, max: 5, itemLabel: 'Tip' },
      { title: 'Cierre', durKey: 'durCierre', fields: [{ key: 'cierre', type: 'text', label: 'Botón' }, { key: 'handle', type: 'text', label: 'Subtexto' }] },
    ],
    scenes: (c) => {
      const n = c.tips.length;
      return [
        { key: 'hook', label: 'Hook', dur: +c.durHook, align: 'center', node: <><Kicker text={c.hookTop} /><Cascade text={c.hook} size={94} align="center" weight={900} /></> },
        ...c.tips.map((t, i) => ({
          key: 'tip' + i, label: `Tip ${i + 1}`, dur: +t.dur, align: 'left',
          node: <><BigDigit text={pad2(i + 1)} /><Kicker text={`Tip ${i + 1} de ${n}`} /><Cascade text={t.text} size={82} align="left" weight={900} maxW={720} /></>,
        })),
        { key: 'cierre', label: 'Cierre', dur: +c.durCierre, align: 'center', node: <CTAPill text={c.cierre} sub={c.handle} /> },
      ];
    },
  },

  // ── 4 · TIPS — Countdown ───────────────────────────────────────────────
  {
    id: 'countdown', name: 'Countdown', tag: 'Tips',
    desc: 'Cuenta regresiva con número gigante — el #1 al final',
    listKey: 'items',
    defaults: {
      hookTop: 'Ojo con esto', hook: '*3 errores* que frenan tu IA', durHook: 2.8,
      items: [
        { text: 'Pilotos eternos que nunca llegan a producción', dur: 3.0 },
        { text: 'No medir nada antes de automatizar', dur: 3.0 },
        { text: 'Empezar por la herramienta y no por el problema', dur: 3.0 },
      ],
      cierre: 'El #1 es el más caro', handle: '@aplicaia', durCierre: 2.8,
    },
    sections: [
      { title: 'Hook', durKey: 'durHook', fields: [{ key: 'hookTop', type: 'text', label: 'Etiqueta' }, { key: 'hook', type: 'multi', label: 'Frase', rows: 2 }] },
      { title: 'Items — del último al primero', type: 'list', listKey: 'items', min: 3, max: 5, itemLabel: 'Item' },
      { title: 'Cierre', durKey: 'durCierre', fields: [{ key: 'cierre', type: 'text', label: 'Botón' }, { key: 'handle', type: 'text', label: 'Subtexto' }] },
    ],
    scenes: (c) => {
      const n = c.items.length;
      return [
        { key: 'hook', label: 'Hook', dur: +c.durHook, align: 'center', node: <><Kicker text={c.hookTop} /><Cascade text={c.hook} size={94} align="center" weight={900} /></> },
        ...c.items.map((t, i) => ({
          key: 'item' + i, label: `#${n - i}`, dur: +t.dur, align: 'center',
          node: <><BigNumber n={n - i} /><Cascade text={t.text} size={70} align="center" weight={800} maxW={760} /></>,
        })),
        { key: 'cierre', label: 'Cierre', dur: +c.durCierre, align: 'center', node: <CTAPill text={c.cierre} sub={c.handle} /> },
      ];
    },
  },

  // ── 5 · CASO — Caso de éxito ───────────────────────────────────────────
  {
    id: 'caso', name: 'Caso de éxito', tag: 'Caso',
    desc: 'Cliente + problema + métrica count-up + resultado',
    defaults: {
      kicker: 'Caso real · Logística', cliente: 'Operador con 900 pedidos semanales cargados a mano.', durIntro: 3.0,
      problema: '6 horas por día\nse iban en\n*copiar y pegar.*', durProblema: 3.2,
      metric: { prefix: '-', value: 87, suffix: '%', label: 'de tiempo en carga manual', dur: 3.4 },
      resultado: 'El equipo pasó de cargar datos a *vender*.', durResultado: 3.0,
      cta: 'Tu caso puede ser el próximo', handle: '@aplicaia', durCta: 2.8,
    },
    sections: [
      { title: 'Intro', durKey: 'durIntro', fields: [{ key: 'kicker', type: 'text', label: 'Etiqueta' }, { key: 'cliente', type: 'multi', label: 'Cliente / contexto', rows: 2 }] },
      { title: 'Problema', durKey: 'durProblema', fields: [{ key: 'problema', type: 'multi', label: 'Líneas — una por línea', rows: 3 }] },
      { title: 'Métrica', type: 'metric', key: 'metric' },
      { title: 'Resultado', durKey: 'durResultado', fields: [{ key: 'resultado', type: 'multi', label: 'Frase', rows: 2 }] },
      { title: 'Cierre', durKey: 'durCta', fields: [{ key: 'cta', type: 'text', label: 'Botón' }, { key: 'handle', type: 'text', label: 'Subtexto' }] },
    ],
    scenes: (c) => [
      { key: 'intro', label: 'Intro', dur: +c.durIntro, align: 'center', node: <><Kicker text={c.kicker} /><Cascade text={c.cliente} size={76} align="center" /></> },
      { key: 'problema', label: 'Problema', dur: +c.durProblema, align: 'center', node: <StackReveal lines={splitLines(c.problema)} base={140} /> },
      { key: 'metric', label: 'Métrica', dur: +c.metric.dur, align: 'center', node: <CountUpBig {...c.metric} /> },
      { key: 'resultado', label: 'Resultado', dur: +c.durResultado, align: 'center', node: <Cascade text={c.resultado} size={90} align="center" weight={900} /> },
      { key: 'cta', label: 'Cierre', dur: +c.durCta, align: 'center', node: <CTAPill text={c.cta} sub={c.handle} /> },
    ],
  },

  // ── 6 · CASO — Métricas ────────────────────────────────────────────────
  {
    id: 'metricas', name: 'Métricas', tag: 'Caso',
    desc: 'Serie de números count-up + cierre',
    listKey: 'metrics',
    defaults: {
      kicker: 'Resultados', titulo: '90 días\ncon *AplicaIA*', durTitulo: 2.8,
      metrics: [
        { prefix: '', value: 14, suffix: ' hs', label: 'ahorradas por semana', dur: 3.0 },
        { prefix: '', value: 3, suffix: '×', label: 'más rápido en responder', dur: 3.0 },
        { prefix: '', value: 0, suffix: '', label: 'errores de carga', dur: 3.0 },
      ],
      cierre: 'Medimos *todo*.', cta: 'Pedí tu diagnóstico', handle: '@aplicaia', durCierre: 3.2,
    },
    sections: [
      { title: 'Título', durKey: 'durTitulo', fields: [{ key: 'kicker', type: 'text', label: 'Etiqueta' }, { key: 'titulo', type: 'multi', label: 'Líneas — una por línea', rows: 2 }] },
      { title: 'Métricas', type: 'metrics', listKey: 'metrics', min: 2, max: 4 },
      { title: 'Cierre', durKey: 'durCierre', fields: [{ key: 'cierre', type: 'text', label: 'Frase' }, { key: 'cta', type: 'text', label: 'Botón' }, { key: 'handle', type: 'text', label: 'Subtexto' }] },
    ],
    scenes: (c) => [
      { key: 'titulo', label: 'Título', dur: +c.durTitulo, align: 'center', node: <><Kicker text={c.kicker} /><StackReveal lines={splitLines(c.titulo)} base={150} /></> },
      ...c.metrics.map((m, i) => ({
        key: 'm' + i, label: `Métrica ${i + 1}`, dur: +m.dur, align: 'center',
        node: <><Kicker text={pad2(i + 1)} /><CountUpBig {...m} /></>,
      })),
      { key: 'cierre', label: 'Cierre', dur: +c.durCierre, align: 'center', node: <><Cascade text={c.cierre} size={100} align="center" weight={900} /><CTAPill text={c.cta} sub={c.handle} /></> },
    ],
  },
];

Object.assign(window, { REEL_TEMPLATES, pad2 });
