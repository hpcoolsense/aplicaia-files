# Setup de la Routine "Carrusel diario Claude" — qué dejar andando

Diagnóstico hecho el 2026-06-03 corriendo la routine en el environment remoto.
Separa lo **ya arreglado en el repo** de lo que **solo se cambia en la web**
(config del environment / texto de la routine), porque desde el sandbox no se
puede tocar la network policy ni las variables de entorno.

---

## 1. Ya arreglado en el repo (commiteado)

### `posts/bootstrap.sh`
Reemplaza al Paso 0 inline. Arregla dos fallas reales del environment:

- **Playwright vs chromium**: `pip install playwright` instala una versión (1.60)
  cuyo build de chromium (1223) **no está** en la imagen, que trae `chromium-1194`
  en `/opt/pw-browsers`. El script prueba lanzar chromium y, si falla, fija la
  versión de playwright que matchea (1.56.0 en esta imagen).
- **`--with-deps`**: se eliminó. Falla por repos de apt sin firmar y no hace falta:
  el chromium ya viene en la imagen.

**Cambio a hacer en el texto de la routine (Paso 0):** reemplazar todo el bloque
bash inline por:

```bash
cd /home/user && bash aplicaia-files/posts/bootstrap.sh || {
  echo "bootstrap failed"; exit 1; }
```

(Si el repo todavía no existe, primero
`git clone https://github.com/hpcoolsense/aplicaia-files.git` — el script igual
es idempotente y hace el clone si falta.)

---

## 2. Cambios en el TEXTO de la routine (web UI — los hago vos)

### 2.1 Paso 5 — Quality gate: dimensión equivocada (BUG)
`render.py` usa `device_scale_factor=2`, así que **todos** los PNG salen
**2160×2160** (verificado: los 5 carruseles ya publicados son 2160×2160). El gate
actual exige `1080 x 1080` → **nunca puede pasar**. `render.py` no se debe tocar.

Cambiar en Paso 5:
```bash
file "$f" | grep -q "PNG image data, 2160 x 2160" || { echo "FATAL: $f no es 2160x2160"; exit 1; }
```

### 2.2 Paso 1 — Descubrimiento del tema en X: NO es ejecutable hoy
X está **bloqueado a nivel de red** en este environment (no es un tema de login):

```
x.com / api.x.com / twitter.com / abs.twimg.com  ->  403 "Host not in allowlist"
github.com / pypi  ->  OK
WebFetch (cualquier host)  ->  403 (deshabilitado por la policy)
WebSearch  ->  único canal web que funciona
```

Para que el Paso 1 sea autónomo hacen falta DOS cosas que se setean en la web:

1. **Network policy del environment** → agregar a la allowlist:
   `api.x.com`, `x.com`, `abs.twimg.com`.
   (Doc: https://code.claude.com/docs/en/claude-code-on-the-web)
2. **Fuente de datos con auth** (elegir una):
   - **Recomendado:** `X_BEARER_TOKEN` como variable de entorno y reescribir el
     Paso 1 para usar la API v2: `GET /2/tweets/search/recent` con
     `tweet.fields=public_metrics,created_at` → da likes/RT/replies/fecha exactos,
     que es justo lo que pide el Abort Gate (Paso 2).
   - Alternativa frágil: cookies de sesión (`auth_token`, `ct0`) como env var,
     inyectadas con Playwright. Se vencen y hay que rotarlas. Usuario+contraseña
     NO sirve (captcha/2FA rompen el headless).

> Mientras la network policy no se abra, el Paso 1 solo puede hacerse pasando el
> tweet ancla a mano, o usando WebSearch como fuente aproximada (rompe la regla
> dura de métricas exactas).

---

## 3. Variables de entorno del environment (web UI)

### 3.1 `GH_TOKEN` — falta de verdad
La routine dice "viene de `GH_TOKEN`" pero **no está seteado**; el bootstrap aborta
sin él. Hay que agregarlo a la config del environment.

### 3.2 Token plano expuesto en el texto de la routine — REVOCAR
El bloque "info util" de la routine tiene un PAT de GitHub en texto plano
(`ghp_...`). Está expuesto: **revocalo en GitHub, emití uno nuevo y ponelo solo en
`GH_TOKEN`**. Sacá el token del texto de la routine.

### 3.3 Zernio — auth interactiva en cada corrida
Zernio usa OAuth interactivo (MCP). El container es efímero, así que cada sesión
nueva pide pegar la URL de callback a mano → **no es desatendido**. Si Zernio
permite un token de larga duración, guardalo como env var y usá ese; si no, este
paso siempre va a requerir intervención humana.

---

## Checklist para dejarlo 100% autónomo

- [ ] Routine Paso 0 → llamar a `posts/bootstrap.sh`.
- [ ] Routine Paso 5 → `2160 x 2160` en vez de `1080 x 1080`.
- [ ] Network policy → allowlist `api.x.com`, `x.com`, `abs.twimg.com`.
- [ ] Env var `X_BEARER_TOKEN` (+ reescribir Paso 1 con API v2).
- [ ] Env var `GH_TOKEN` seteada de verdad.
- [ ] Revocar el PAT plano del texto de la routine.
- [ ] Zernio: token persistente como env var (si Zernio lo permite).
