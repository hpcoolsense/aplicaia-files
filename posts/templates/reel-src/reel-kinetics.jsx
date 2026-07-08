// reel-kinetics.jsx — primitivas de tipografía cinética para Reels AplicaIA
// Requiere animations.jsx cargado antes (Easing, clamp, useTime, useSprite en window).
// Fuente de verdad de diseño: claude.ai/design proyecto "AplicaIA" (mismo nombre de archivo).

// animations.jsx no trae Quint — lo agregamos
Easing.easeOutQuint = (t) => 1 + (--t) * t * t * t * t;

const KIN_MONO = "'JetBrains Mono', ui-monospace, monospace";
const KIN_INK = '#F5F5F7';
const KIN_DIM = '#A1A1AA';

// Zona segura Reels (UI de Instagram: barra superior, caption, rail de acciones)
const SAFE = { top: 240, bottom: 460, left: 100, right: 150 };

const ReelCtx = React.createContext({ accent: '#FACC15' });
const useReel = () => React.useContext(ReelCtx);

// ── helpers ──────────────────────────────────────────────────────────────
function hexA(hex, a) {
  const h = hex.replace('#', '');
  const r = parseInt(h.slice(0, 2), 16), g = parseInt(h.slice(2, 4), 16), b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${a})`;
}

// *palabra* → span con color de acento
function rich(text, accent) {
  return String(text).split(/(\*[^*]+\*)/g).map((p, i) =>
    p.length > 2 && p.startsWith('*') && p.endsWith('*')
      ? <span key={i} style={{ color: accent }}>{p.slice(1, -1)}</span>
      : <React.Fragment key={i}>{p}</React.Fragment>
  );
}

// texto → [{w, acc}] palabra por palabra conservando marcas de acento
function tokens(text) {
  const out = [];
  String(text).split(/(\*[^*]+\*)/g).forEach(seg => {
    let acc = false, s = seg;
    if (/^\*[^*]+\*$/.test(seg)) { acc = true; s = seg.slice(1, -1); }
    s.split(/\s+/).filter(Boolean).forEach(w => out.push({ w, acc }));
  });
  return out;
}

function splitLines(text) {
  return String(text).split('\n').map(l => l.trim()).filter(Boolean);
}

// tamaño de fuente que entra en maxW (Inter 900 ≈ 0.58em por carácter)
function fitSize(str, base, maxW = 830, k = 0.58) {
  const len = Math.max(1, String(str).replace(/\*/g, '').length);
  return Math.min(base, Math.floor(maxW / (len * k)));
}

// ── fondo, marca, chrome ─────────────────────────────────────────────────
function ReelBg() {
  const t = useTime();
  const { accent } = useReel();
  const g1x = 50 + 9 * Math.sin(t * 0.22), g1y = -6 + 4 * Math.cos(t * 0.17);
  const g2y = 104 + 5 * Math.sin(t * 0.19 + 2);
  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
      <div style={{
        position: 'absolute', inset: 0,
        background: `radial-gradient(62% 42% at ${g1x}% ${g1y}%, ${hexA(accent, 0.13)}, transparent 62%), radial-gradient(85% 50% at 50% ${g2y}%, ${hexA(accent, 0.07)}, transparent 62%), #000`,
      }} />
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px)',
        backgroundSize: '3px 3px', mixBlendMode: 'overlay',
      }} />
      <div style={{ position: 'absolute', inset: 0, boxShadow: 'inset 0 0 340px rgba(0,0,0,0.75)' }} />
    </div>
  );
}

function ReelWatermark() {
  const { accent } = useReel();
  return (
    <div style={{ position: 'absolute', top: 118, left: 0, right: 0, display: 'flex', justifyContent: 'center', zIndex: 30 }}>
      <div style={{ fontWeight: 900, fontSize: 44, letterSpacing: '-0.045em', lineHeight: 1, opacity: 0.9 }}>
        <span style={{ color: accent }}>Aplica</span><span style={{ color: KIN_INK }}> IA</span>
      </div>
    </div>
  );
}

function SafeGuides() {
  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 60, pointerEvents: 'none' }}>
      <div style={{ position: 'absolute', top: SAFE.top, bottom: SAFE.bottom, left: SAFE.left, right: SAFE.right, border: '2px dashed rgba(255,90,90,0.7)' }} />
      <div style={{
        position: 'absolute', top: SAFE.top - 34, left: SAFE.left,
        fontFamily: KIN_MONO, fontSize: 20, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(255,90,90,0.85)',
      }}>zona segura</div>
    </div>
  );
}

// contenedor de escena: padding seguro + deriva de cámara constante
function SceneShell({ label, align = 'center', children }) {
  const { progress } = useSprite();
  const s = 1 + 0.045 * Easing.easeOutSine(progress);
  return (
    <div data-screen-label={label} style={{
      position: 'absolute', inset: 0, zIndex: 2,
      padding: `${SAFE.top}px ${SAFE.right}px ${SAFE.bottom}px ${SAFE.left}px`,
    }}>
      <div style={{
        position: 'relative', width: '100%', height: '100%',
        display: 'flex', flexDirection: 'column',
        alignItems: align === 'center' ? 'center' : 'flex-start',
        justifyContent: 'center', gap: 52,
        transform: `scale(${s})`, transformOrigin: '50% 45%',
      }}>
        {children}
      </div>
    </div>
  );
}

// flash de acento en cortes de escena
function Flash() {
  const { progress } = useSprite();
  const { accent } = useReel();
  return <div style={{ position: 'absolute', inset: 0, background: accent, opacity: (1 - Easing.easeOutQuad(progress)) * 0.5, zIndex: 40, pointerEvents: 'none' }} />;
}

// ── piezas cinéticas ─────────────────────────────────────────────────────

// Palabras a pantalla completa una por una, luego apiladas
function WordSlam({ words, base = 210, stackBase = 172 }) {
  const { localTime, duration } = useSprite();
  const { accent } = useReel();
  const clean = (words || []).map(w => String(w).trim()).filter(Boolean);
  const n = Math.max(1, clean.length);
  const solo = Math.min(duration * 0.55, 0.5 * n + 0.15);
  const per = solo / n;

  if (localTime < solo && n > 1) {
    const i = Math.min(n - 1, Math.floor(localTime / per));
    const wt = clamp((localTime - i * per) / per, 0, 1);
    const e = Easing.easeOutExpo(clamp(wt / 0.42, 0, 1));
    const word = clean[i];
    return (
      <div style={{ display: 'grid', placeItems: 'center', width: '100%' }}>
        <div style={{
          fontSize: fitSize(word, base), fontWeight: 900, letterSpacing: '-0.05em', lineHeight: 0.95,
          transform: `scale(${1.9 - 0.9 * e}) rotate(${(i % 2 ? 1 : -1) * (1 - e) * 3}deg)`,
          opacity: e, color: KIN_INK, whiteSpace: 'nowrap',
        }}>{rich(word, accent)}</div>
      </div>
    );
  }

  const st = Math.max(0, localTime - (n > 1 ? solo : 0));
  const size = Math.min(stackBase, ...clean.map(w => fitSize(w, stackBase)));
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      {clean.map((w, i) => {
        const p = Easing.easeOutQuint(clamp((st - i * 0.09) / 0.45, 0, 1));
        return (
          <div key={i} style={{ overflow: 'hidden', padding: '0.04em 0.1em' }}>
            <div style={{
              fontSize: size, fontWeight: 900, letterSpacing: '-0.05em', lineHeight: 0.95,
              transform: `translateY(${(1 - p) * 108}%)`, color: KIN_INK, whiteSpace: 'nowrap', textAlign: 'center',
            }}>{rich(w, accent)}</div>
          </div>
        );
      })}
    </div>
  );
}

// líneas que se revelan desde máscara, en secuencia
function StackReveal({ lines, base = 148, align = 'center' }) {
  const { localTime } = useSprite();
  const { accent } = useReel();
  const ls = (lines || []).filter(Boolean);
  const size = Math.min(base, ...ls.map(l => fitSize(l, base)));
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: align === 'center' ? 'center' : 'flex-start' }}>
      {ls.map((l, i) => {
        const p = Easing.easeOutQuint(clamp((localTime - 0.1 - i * 0.16) / 0.55, 0, 1));
        return (
          <div key={i} style={{ overflow: 'hidden', padding: '0.04em 0.1em' }}>
            <div style={{
              fontSize: size, fontWeight: 900, letterSpacing: '-0.045em', lineHeight: 0.98,
              transform: `translateY(${(1 - p) * 108}%)`, color: KIN_INK, whiteSpace: 'nowrap',
              textAlign: align,
            }}>{rich(l, accent)}</div>
          </div>
        );
      })}
    </div>
  );
}

// párrafo cuyas palabras aparecen al ritmo de lectura
function Cascade({ text, size = 76, align = 'left', weight = 800, color = KIN_INK, maxW = 830 }) {
  const { localTime, duration } = useSprite();
  const { accent } = useReel();
  const tk = tokens(text);
  const chars = String(text).length;
  const eff = Math.round(size * Math.min(1, Math.sqrt(170 / Math.max(1, chars))));
  const per = Math.min(0.11, (duration * 0.45) / Math.max(1, tk.length));
  return (
    <div style={{
      display: 'flex', flexWrap: 'wrap', gap: '0.06em 0.26em',
      justifyContent: align === 'center' ? 'center' : 'flex-start',
      maxWidth: maxW, width: '100%',
      fontSize: eff, fontWeight: weight, letterSpacing: '-0.03em', lineHeight: 1.06,
      textAlign: align, color,
    }}>
      {tk.map((t, i) => {
        const p = Easing.easeOutQuint(clamp((localTime - 0.08 - i * per) / 0.32, 0, 1));
        return (
          <span key={i} style={{
            display: 'inline-block', opacity: p, transform: `translateY(${(1 - p) * 26}px)`,
            color: t.acc ? accent : undefined,
          }}>{t.w}</span>
        );
      })}
    </div>
  );
}

// lista numerada que entra en secuencia y queda
function ListReveal({ items, size = 64, gap = 46 }) {
  const { localTime, duration } = useSprite();
  const { accent } = useReel();
  const ls = (items || []).filter(Boolean);
  const stag = Math.min(0.5, (duration * 0.5) / Math.max(1, ls.length));
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap, width: '100%' }}>
      {ls.map((it, i) => {
        const p = Easing.easeOutQuint(clamp((localTime - 0.15 - i * stag) / 0.45, 0, 1));
        const chars = it.length;
        const eff = Math.round(size * Math.min(1, Math.sqrt(46 / Math.max(1, chars))));
        return (
          <div key={i} style={{
            display: 'flex', gap: 30, alignItems: 'baseline',
            opacity: p, transform: `translateY(${(1 - p) * 34}px)`,
          }}>
            <span style={{ fontFamily: KIN_MONO, color: accent, fontSize: Math.round(size * 0.52), fontWeight: 700 }}>
              {String(i + 1).padStart(2, '0')}
            </span>
            <span style={{ fontSize: eff, fontWeight: 800, letterSpacing: '-0.03em', lineHeight: 1.05, color: KIN_INK }}>
              {rich(it, accent)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// etiqueta mono tipeada con cursor
function Kicker({ text }) {
  const { localTime } = useSprite();
  const { accent } = useReel();
  const clean = String(text).replace(/\*/g, '');
  const chars = Math.min(clean.length, Math.floor(Math.max(0, localTime - 0.05) / 0.038));
  const on = Math.floor(localTime * 3) % 2 === 0;
  return (
    <div style={{
      fontFamily: KIN_MONO, fontSize: 28, letterSpacing: '0.3em', textTransform: 'uppercase',
      color: accent, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8, whiteSpace: 'nowrap',
    }}>
      <span>{clean.slice(0, chars)}</span>
      <span style={{ width: 15, height: 30, background: accent, opacity: on ? 1 : 0.15 }} />
    </div>
  );
}

// palabra gigante fantasma detrás del contenido
function GhostWord({ word, size = 400 }) {
  const { progress } = useSprite();
  const { accent } = useReel();
  const s = 0.92 + 0.3 * Easing.easeOutSine(progress);
  return (
    <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', zIndex: 0, pointerEvents: 'none' }}>
      <div style={{
        fontSize: fitSize(word, size, 1300), fontWeight: 900, letterSpacing: '-0.04em',
        color: 'transparent', WebkitTextStroke: `3px ${hexA(accent, 0.35)}`,
        transform: `scale(${s}) rotate(-5deg)`, whiteSpace: 'nowrap',
      }}>{String(word).replace(/\*/g, '')}</div>
    </div>
  );
}

// dígito gigante contorneado (fondo de tips)
function BigDigit({ text, size = 600 }) {
  const { localTime, progress } = useSprite();
  const { accent } = useReel();
  const e = Easing.easeOutExpo(clamp(localTime / 0.6, 0, 1));
  return (
    <div style={{
      position: 'absolute', right: -70, top: '50%',
      transform: `translateY(-50%) scale(${0.8 + 0.2 * e + 0.06 * Easing.easeOutSine(progress)})`,
      fontSize: size, fontWeight: 900, letterSpacing: '-0.06em', lineHeight: 1,
      color: 'transparent', WebkitTextStroke: `4px ${hexA(accent, 0.3)}`,
      opacity: e, zIndex: 0, pointerEvents: 'none',
    }}>{text}</div>
  );
}

// número gigante lleno (countdown)
function BigNumber({ n, size = 430 }) {
  const { localTime } = useSprite();
  const { accent } = useReel();
  const e = Easing.easeOutBack(clamp(localTime / 0.5, 0, 1));
  const drift = 1 + 0.03 * Math.sin(localTime * 1.4);
  return (
    <div style={{
      fontSize: size, fontWeight: 900, color: accent, letterSpacing: '-0.06em', lineHeight: 0.9,
      transform: `scale(${e * drift})`, textShadow: `0 0 120px ${hexA(accent, 0.4)}`,
      fontVariantNumeric: 'tabular-nums',
    }}>{n}</div>
  );
}

// métrica con count-up
function CountUpBig({ value = 0, prefix = '', suffix = '', label = '', size = 290 }) {
  const { localTime, duration } = useSprite();
  const { accent } = useReel();
  const cd = Math.min(1.6, duration * 0.55);
  const p = Easing.easeOutExpo(clamp(localTime / cd, 0, 1));
  const v = Math.round((+value || 0) * p);
  const settle = localTime > cd ? 1 + 0.03 * Math.exp(-(localTime - cd) * 5) * Math.sin((localTime - cd) * 14) : 1;
  const lp = Easing.easeOutQuint(clamp((localTime - cd * 0.6) / 0.5, 0, 1));
  const str = `${prefix}${v}${suffix}`;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 36 }}>
      <div style={{
        fontSize: fitSize(str, size, 830, 0.62), fontWeight: 900, letterSpacing: '-0.05em', lineHeight: 1,
        color: accent, fontVariantNumeric: 'tabular-nums',
        transform: `scale(${settle})`, textShadow: `0 0 90px ${hexA(accent, 0.35)}`, whiteSpace: 'nowrap',
      }}>{str}</div>
      <div style={{
        opacity: lp, transform: `translateY(${(1 - lp) * 20}px)`,
        fontSize: 46, color: KIN_DIM, fontWeight: 600, textAlign: 'center', maxWidth: 720, lineHeight: 1.25,
      }}>{label}</div>
    </div>
  );
}

// píldora CTA con brillo + subtexto
function CTAPill({ text, sub }) {
  const { localTime } = useSprite();
  const { accent } = useReel();
  const e = Easing.easeOutBack(clamp(localTime / 0.55, 0, 1));
  const pulse = 1 + 0.014 * Math.sin(localTime * 2.4);
  const subP = Easing.easeOutQuint(clamp((localTime - 0.5) / 0.5, 0, 1));
  const shine = (localTime * 0.42) % 1;
  const fs = Math.min(32, Math.floor(700 / (Math.max(1, String(text).length) * 0.82)));
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 46 }}>
      <div style={{
        transform: `scale(${e * pulse})`, background: accent, color: '#000',
        borderRadius: 999, padding: '36px 64px',
        fontFamily: KIN_MONO, fontSize: fs, fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase',
        position: 'relative', overflow: 'hidden', whiteSpace: 'nowrap',
        boxShadow: `0 0 90px ${hexA(accent, 0.3)}`,
      }}>
        {String(text).replace(/\*/g, '')}
        <div style={{
          position: 'absolute', inset: '-10% auto -10% 0', width: '34%',
          transform: `translateX(${-140 + shine * 420}%) skewX(-18deg)`,
          background: 'rgba(255,255,255,0.35)',
        }} />
      </div>
      {sub ? (
        <div style={{
          opacity: subP, fontFamily: KIN_MONO, fontSize: 27, letterSpacing: '0.3em',
          textTransform: 'uppercase', color: 'rgba(245,245,247,0.65)',
        }}>{String(sub).replace(/\*/g, '')}</div>
      ) : null}
    </div>
  );
}

Object.assign(window, {
  ReelCtx, useReel, SAFE, hexA, rich, tokens, splitLines, fitSize,
  ReelBg, ReelWatermark, SafeGuides, SceneShell, Flash,
  WordSlam, StackReveal, Cascade, ListReveal, Kicker,
  GhostWord, BigDigit, BigNumber, CountUpBig, CTAPill,
});
