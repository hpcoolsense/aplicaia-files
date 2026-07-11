#!/usr/bin/env python3
"""
discover.py — descubre de qué se está hablando HOY sobre Claude/Anthropic,
con métricas de engagement REALES y verificables.

Por qué existe: el Paso 1 pedía "leer tendencias de X". x.com no sirve contenido
sin JavaScript ni sesión, así que ese camino nunca dio datos reales — y el agente
terminaba escribiendo métricas plausibles pero inventadas. Este script trae
números que existen de verdad, o no trae nada.

Fuentes (todas públicas, sin auth, sin costo). Cada una aporta un ángulo distinto:

  · bluesky    → conversación social real (likes, reposts, replies). El reemplazo de X.
  · hackernews → debate técnico profundo (puntos, comentarios).
  · github     → QUÉ ESTÁ CONSTRUYENDO la gente con Claude (estrellas). Oro para
                 el ángulo `caso-de-uso`: no es una opinión, es algo que alguien armó.
  · devto      → tutoriales y guías paso a paso (reacciones). Ángulo `tutorial`.
  · googlenews → cobertura de medios. Sirve para el gate de "2 fuentes independientes".

Si una fuente falla (403, timeout, rate limit), se reporta y se sigue con las demás.
Nunca inventa métricas: lo que no se pudo leer sale como null.

Uso:
    python3 posts/discover.py                    # resumen legible
    python3 posts/discover.py --json             # JSON para el pipeline
    python3 posts/discover.py --horas 48
    python3 posts/discover.py --cobertura "Claude Cowork"   # ¿cuántos medios lo cubren?
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

UA = "Mozilla/5.0 (compatible; AplicaIA-routine/1.0)"
TIMEOUT = 20
# La API de búsqueda de GitHub sin token limita a ~10 req/min POR IP, y el sandbox
# comparte IP saliente → 403 casi seguro. Con token sube a 30 req/min por-token.
GH_TOKEN = os.environ.get("GH_TOKEN", "").strip()

# El tema tiene que ser del ecosistema Claude, no de "IA" en general.
CLAVES = ("claude", "anthropic", "sonnet", "opus", "haiku", "fable", "cowork")

HN_API = "https://hn.algolia.com/api/v1/search_by_date"
BSKY_API = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"
GH_API = "https://api.github.com/search/repositories"
DEVTO_API = "https://dev.to/api/articles"
GNEWS_RSS = "https://news.google.com/rss/search"


def _get(url: str, timeout: int = TIMEOUT, headers: dict | None = None) -> bytes:
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _json(url: str, headers: dict | None = None) -> dict:
    return json.loads(_get(url, headers=headers))


def _sobre_claude(texto: str) -> bool:
    low = texto.lower()
    return any(k in low for k in CLAVES)


def _edad_horas(ts_epoch: float) -> float:
    return round((time.time() - ts_epoch) / 3600, 1)


# ── fuentes ───────────────────────────────────────────────────────────────

def fuente_hackernews(horas: int) -> list[dict]:
    """Debate técnico. Métrica: puntos y comentarios."""
    corte = int(time.time()) - horas * 3600
    vistos, out = set(), []
    for q in ("claude anthropic", "claude code", "anthropic"):
        params = urllib.parse.urlencode({
            "query": q, "tags": "story",
            "numericFilters": f"created_at_i>{corte}", "hitsPerPage": 30,
        })
        for h in _json(f"{HN_API}?{params}").get("hits", []):
            oid, titulo = h.get("objectID"), h.get("title") or ""
            if not oid or oid in vistos or not _sobre_claude(titulo):
                continue
            vistos.add(oid)
            out.append({
                "fuente": "hackernews",
                "titulo": titulo,
                "url": h.get("url") or f"https://news.ycombinator.com/item?id={oid}",
                "url_discusion": f"https://news.ycombinator.com/item?id={oid}",
                "autor": h.get("author"),
                "horas_antiguedad": _edad_horas(h["created_at_i"]),
                "puntos": h.get("points"),
                "comentarios": h.get("num_comments"),
                "engagement": (h.get("points") or 0) + (h.get("num_comments") or 0),
            })
    return out


def fuente_bluesky(horas: int) -> list[dict]:
    """Conversación social real (el reemplazo de X). Métrica: likes, reposts, replies."""
    limite = datetime.now(timezone.utc) - timedelta(hours=horas)
    vistos, out = set(), []
    for q in ("claude anthropic", "claude code", "claude ai"):
        params = urllib.parse.urlencode({"q": q, "limit": 40, "sort": "top"})
        for p in _json(f"{BSKY_API}?{params}").get("posts", []):
            uri = p.get("uri")
            texto = (p.get("record") or {}).get("text", "")
            if not uri or uri in vistos or not _sobre_claude(texto):
                continue
            try:
                creado = datetime.fromisoformat(p["record"]["createdAt"].replace("Z", "+00:00"))
            except Exception:
                continue
            if creado < limite:
                continue
            vistos.add(uri)
            handle = p["author"]["handle"]
            likes, reposts, replies = p.get("likeCount", 0), p.get("repostCount", 0), p.get("replyCount", 0)
            out.append({
                "fuente": "bluesky",
                "titulo": texto.replace("\n", " ")[:180],
                "url": f"https://bsky.app/profile/{handle}/post/{uri.rsplit('/', 1)[-1]}",
                "url_discusion": None,
                "autor": f"@{handle}",
                "horas_antiguedad": round((datetime.now(timezone.utc) - creado).total_seconds() / 3600, 1),
                "likes": likes, "reposts": reposts, "comentarios": replies,
                # las respuestas valen más que un like: indican debate, no scroll
                "engagement": likes + 3 * reposts + 5 * replies,
            })
    return out


def fuente_github(horas: int) -> list[dict]:
    """Qué está CONSTRUYENDO la gente con Claude. Métrica: estrellas.
    Un repo nuevo con tracción es un caso-de-uso real, no una opinión."""
    limite = datetime.now(timezone.utc) - timedelta(hours=horas)
    # buscamos con un margen y filtramos por frescura después: la API indexa por día
    desde = (limite - timedelta(days=1)).strftime("%Y-%m-%d")
    params = urllib.parse.urlencode({
        "q": f"claude created:>{desde}", "sort": "stars", "order": "desc", "per_page": 30,
    })
    # con el token del repo, la búsqueda deja de dar 403 por rate-limit compartido
    gh_headers = {"Authorization": f"Bearer {GH_TOKEN}"} if GH_TOKEN else None
    out = []
    for r in _json(f"{GH_API}?{params}", headers=gh_headers).get("items", []):
        texto = f"{r['name']} {r.get('description') or ''}"
        estrellas = r.get("stargazers_count", 0)
        # ruido: repos sin tracción o forks de juguete
        if estrellas < 15 or not _sobre_claude(texto):
            continue
        creado = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        if creado < limite:
            continue
        out.append({
            "fuente": "github",
            "titulo": f"{r['full_name']}: {(r.get('description') or '')[:110]}",
            "url": r["html_url"],
            "url_discusion": None,
            "autor": r["owner"]["login"],
            "horas_antiguedad": round((datetime.now(timezone.utc) - creado).total_seconds() / 3600, 1),
            "estrellas": estrellas,
            "engagement": estrellas,
        })
    return out


def fuente_devto(horas: int) -> list[dict]:
    """Tutoriales y guías. Métrica: reacciones."""
    limite = datetime.now(timezone.utc) - timedelta(hours=horas)
    out = []
    for tag in ("claude", "anthropic"):
        params = urllib.parse.urlencode({"tag": tag, "per_page": 20, "top": 7})
        arts = _json(f"{DEVTO_API}?{params}")
        if not isinstance(arts, list):
            continue
        for a in arts:
            titulo = a.get("title", "")
            if not _sobre_claude(f"{titulo} {a.get('description','')}"):
                continue
            try:
                pub = datetime.fromisoformat(a["published_at"].replace("Z", "+00:00"))
            except Exception:
                continue
            if pub < limite:
                continue
            reacciones = a.get("positive_reactions_count", 0)
            out.append({
                "fuente": "devto",
                "titulo": titulo,
                "url": a.get("url"),
                "url_discusion": None,
                "autor": (a.get("user") or {}).get("username"),
                "horas_antiguedad": round((datetime.now(timezone.utc) - pub).total_seconds() / 3600, 1),
                "reacciones": reacciones,
                "comentarios": a.get("comments_count"),
                "engagement": reacciones + 2 * (a.get("comments_count") or 0),
            })
    return out


def cobertura_medios(tema: str, horas: int) -> dict:
    """Cuántos MEDIOS INDEPENDIENTES cubren el tema (gate de 2+ fuentes)."""
    dias = max(1, round(horas / 24))
    params = urllib.parse.urlencode({
        "q": f"{tema} when:{dias}d", "hl": "es-419", "gl": "AR", "ceid": "AR:es-419",
    })
    xml = _get(f"{GNEWS_RSS}?{params}").decode("utf-8", "ignore")
    items = re.findall(r"<item>(.*?)</item>", xml, re.S)
    notas = []
    for it in items[:30]:
        t = re.search(r"<title>(.*?)</title>", it, re.S)
        l = re.search(r"<link>(.*?)</link>", it, re.S)
        s = re.search(r"<source[^>]*>(.*?)</source>", it, re.S)
        if t and l:
            notas.append({"titulo": t.group(1)[:110], "url": l.group(1), "medio": s.group(1) if s else "?"})
    medios = sorted({n["medio"] for n in notas})
    return {"tema": tema, "medios_independientes": len(medios), "medios": medios[:12], "notas": notas[:10]}


def sondear_x() -> dict:
    """¿x.com es legible sin sesión? Devuelve el diagnóstico, no una excusa."""
    try:
        html = _get("https://x.com/search?q=claude&f=trend", timeout=15).decode("utf-8", "ignore")
    except Exception as e:
        return {"legible": False, "motivo": f"sin acceso: {type(e).__name__}"}
    if "JavaScript is not available" in html or "enable JavaScript" in html:
        return {"legible": False, "motivo": "x.com exige JavaScript y sesión iniciada"}
    if 'data-testid="tweet"' in html:
        return {"legible": True, "motivo": "hay tweets en el HTML"}
    return {"legible": False, "motivo": "responde, pero sin tweets en el HTML"}


# ── orquestación ──────────────────────────────────────────────────────────

FUENTES = {
    "bluesky": fuente_bluesky,
    "hackernews": fuente_hackernews,
    "github": fuente_github,
    "devto": fuente_devto,
}


def recolectar(horas: int) -> tuple[list[dict], dict]:
    candidatos, estado = [], {}
    for nombre, fn in FUENTES.items():
        try:
            hits = fn(horas)
            candidatos.extend(hits)
            estado[nombre] = {"ok": True, "resultados": len(hits)}
        except urllib.error.HTTPError as e:
            estado[nombre] = {"ok": False, "error": f"HTTP {e.code}"}
        except Exception as e:
            estado[nombre] = {"ok": False, "error": type(e).__name__}
    # frescura pareja: nada más viejo que la ventana pedida (el abort gate exige <96h)
    candidatos = [c for c in candidatos if c["horas_antiguedad"] <= horas]
    candidatos.sort(key=lambda c: c["engagement"], reverse=True)
    return candidatos, estado


def _metricas(c: dict) -> str:
    partes = []
    for k, sig in (("puntos", "▲"), ("likes", "❤️"), ("estrellas", "⭐"),
                   ("reposts", "🔁"), ("reacciones", "👍"), ("comentarios", "💬")):
        if c.get(k):
            partes.append(f"{sig}{c[k]}")
    return " ".join(partes)


def main():
    ap = argparse.ArgumentParser(description="Descubre temas calientes sobre Claude con métricas reales.")
    ap.add_argument("--horas", type=int, default=96, help="Ventana de frescura (default 96)")
    ap.add_argument("--json", action="store_true", help="Salida JSON para el pipeline")
    ap.add_argument("--cobertura", metavar="TEMA", help="Cuántos medios independientes cubren TEMA")
    ap.add_argument("--skip-x", action="store_true", help="No sondear x.com")
    args = ap.parse_args()

    if args.cobertura:
        c = cobertura_medios(args.cobertura, args.horas)
        if args.json:
            json.dump(c, sys.stdout, ensure_ascii=False, indent=2); print(); return
        print(f"\"{c['tema']}\" → {c['medios_independientes']} medios independientes")
        for m in c["medios"]:
            print(f"  · {m}")
        return

    x = {"legible": False, "motivo": "no sondeado"} if args.skip_x else sondear_x()
    candidatos, estado = recolectar(args.horas)

    if args.json:
        json.dump({"x": x, "fuentes": estado, "candidatos": candidatos}, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return

    print(f"x.com legible: {'sí' if x['legible'] else 'NO'} ({x['motivo']})\n")
    print("Fuentes:")
    for n, s in estado.items():
        print(f"  {n:<12} {'✅ ' + str(s['resultados']) + ' resultados' if s['ok'] else '❌ ' + s['error']}")

    print(f"\n{len(candidatos)} candidatos en las últimas {args.horas}h.")
    if not candidatos:
        print("  (ninguno) → el Paso 1 debe apoyarse en WebSearch")
        return
    print("⚠️  Ordenados por engagement, NO por calidad: el filtro SHOWCASE del Paso 1.3")
    print("    descarta quejas, polémicas y opiniones aunque tengan muchos likes.\n")

    # lo mejor de cada fuente: cada una aporta un ángulo distinto
    for nombre in FUENTES:
        del_fuente = [c for c in candidatos if c["fuente"] == nombre][:4]
        if not del_fuente:
            continue
        print(f"── {nombre} ──")
        for c in del_fuente:
            print(f"  {_metricas(c):<26} ({c['horas_antiguedad']:>5.1f}h)  {c['titulo'][:62]}")
            print(f"      {(c['url'] or '')[:78]}")
        print()


if __name__ == "__main__":
    main()
