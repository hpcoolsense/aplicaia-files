// reel-player.jsx — runner headless de las plantillas de reel (sin editor).
// Requiere animations.jsx + reel-kinetics.jsx + reel-templates.jsx cargados antes.
//
// Contrato con render_reel.py:
//   window.DATA = { template: '<id>', accent: '#FACC15', content: {...} }  (inyectado antes de cargar)
//   window.__reel  → { total, fps, scenes: [{key,label,start,dur}] }       (disponible tras el mount)
//   window.__seek(t) → Promise; renderiza el frame en el tiempo t (flushSync + doble rAF = pintado)
//   body[data-player-ready="1"] cuando fuentes + mount están listos.
//
// Sin window.DATA (abierto a mano en un navegador) reproduce la plantilla 'anuncio'
// con sus textos default, en loop — sirve como preview.

const PLAYER_ACCENTS = ['#FACC15', '#A3E635', '#22D3EE', '#FB923C', '#A78BFA'];

function buildConfig() {
  const d = window.DATA || {};
  const tpl = REEL_TEMPLATES.find(t => t.id === d.template) || REEL_TEMPLATES.find(t => t.id === 'anuncio') || REEL_TEMPLATES[0];
  const content = { ...JSON.parse(JSON.stringify(tpl.defaults)), ...(d.content || {}) };
  const accent = PLAYER_ACCENTS.includes(d.accent) ? d.accent : (d.accent || PLAYER_ACCENTS[0]);
  return { tpl, content, accent };
}

function HeadlessReel() {
  const { tpl, content, accent } = React.useMemo(buildConfig, []);
  const [time, setTime] = React.useState(0);

  const scenes = tpl.scenes(content);
  const starts = []; let acc = 0;
  scenes.forEach(s => { starts.push(acc); acc += Math.max(0.5, +s.dur || 1); });
  const total = Math.round(acc * 100) / 100;

  React.useEffect(() => {
    window.__reel = {
      total,
      template: tpl.id,
      scenes: scenes.map((s, i) => ({ key: s.key, label: s.label, start: starts[i], dur: Math.max(0.5, +s.dur || 1) })),
    };
    window.__seek = (t) => new Promise(resolve => {
      ReactDOM.flushSync(() => setTime(Math.max(0, Math.min(total, +t || 0))));
      // doble rAF: garantiza que el frame quedó pintado antes del screenshot
      requestAnimationFrame(() => requestAnimationFrame(resolve));
    });

    const fonts = [
      '400 28px "JetBrains Mono"', '700 28px "JetBrains Mono"',
      '400 76px "Inter"', '600 46px "Inter"', '800 76px "Inter"', '900 150px "Inter"',
    ];
    Promise.all(fonts.map(f => document.fonts.load(f).catch(() => null)))
      .then(() => document.fonts.ready)
      .then(() => { document.body.dataset.playerReady = '1'; });

    // Preview interactivo si no vino DATA inyectado: loop con reloj real
    if (!window.DATA) {
      let raf, t0 = performance.now();
      const step = (ts) => { setTime(((ts - t0) / 1000) % total); raf = requestAnimationFrame(step); };
      raf = requestAnimationFrame(step);
      return () => cancelAnimationFrame(raf);
    }
  }, []);

  return (
    <div id="reel-canvas" style={{
      width: 1080, height: 1920, position: 'relative', overflow: 'hidden', background: '#000',
      fontFamily: '"Inter", system-ui, sans-serif',
    }}>
      <TimelineContext.Provider value={{ time, duration: total, playing: false, setTime, setPlaying: () => {} }}>
        <ReelCtx.Provider value={{ accent }}>
          <ReelBg />
          {scenes.map((s, i) => (
            <Sprite key={s.key} start={starts[i]} end={starts[i] + Math.max(0.5, +s.dur || 1) - 0.001}>
              <SceneShell label={`${tpl.name} · ${s.label}`} align={s.align}>
                {s.node}
              </SceneShell>
            </Sprite>
          ))}
          {starts.slice(1).map(b => (
            <Sprite key={'f' + b} start={Math.max(0, b - 0.02)} end={b + 0.16}><Flash /></Sprite>
          ))}
          <ReelWatermark />
        </ReelCtx.Provider>
      </TimelineContext.Provider>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<HeadlessReel />);
