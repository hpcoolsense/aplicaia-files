#!/usr/bin/env python3
"""
discover.py — descubre de qué se está hablando HOY sobre Claude/Anthropic,
con métricas de engagement REALES y verificables.

Por qué existe: el Paso 1 de la routine pedía "leer tendencias de X". x.com no
sirve contenido sin JavaScript ni sesión iniciada, así que ese camino nunca dio
datos reales — y el agente terminaba escribiendo métricas plausibles pero
inventadas. Este script trae números que existen de verdad, o no trae nada.

Fuentes (todas públicas, sin auth, sin costo):
  · Hacker News (Algolia)  → puntos y comentarios reales
  · x.com                  → se sondea y se REPORTA si es legible (spoiler: no)

Uso:
    python3 posts/discover.py                 # últimas 96h, salida legible
    python3 posts/discover.py --json          # JSON para el resto del pipeline
    python3 posts/discover.py --horas 48

Nunca inventa métricas: lo que no se pudo leer sale como null.
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request

HN_API = "https://hn.algolia.com/api/v1/search_by_date"
UA = "Mozilla/5.0 (compatible; AplicaIA-routine/1.0)"

CONSULTAS = [
    "claude anthropic",
    "claude code",
    "anthropic",
    "claude ai",
]


def _get(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def buscar_hn(horas: int) -> list[dict]:
    """Historias de HN sobre Claude/Anthropic con puntos y comentarios reales."""
    corte = int(time.time()) - horas * 3600
    vistos, salida = set(), []

    for q in CONSULTAS:
        params = urllib.parse.urlencode({
            "query": q,
            "tags": "story",
            "numericFilters": f"created_at_i>{corte}",
            "hitsPerPage": 30,
        })
        try:
            data = json.loads(_get(f"{HN_API}?{params}"))
        except Exception as e:
            print(f"  ⚠ HN falló para '{q}': {e}", file=sys.stderr)
            continue

        for h in data.get("hits", []):
            oid = h.get("objectID")
            if not oid or oid in vistos:
                continue
            vistos.add(oid)
            titulo = h.get("title") or ""
            if not titulo:
                continue
            # filtro de tema: que hable de Claude/Anthropic, no de cualquier IA
            low = titulo.lower()
            if not any(k in low for k in ("claude", "anthropic", "sonnet", "opus", "haiku")):
                continue
            edad_h = round((time.time() - h["created_at_i"]) / 3600, 1)
            salida.append({
                "fuente": "hackernews",
                "titulo": titulo,
                "url": h.get("url") or f"https://news.ycombinator.com/item?id={oid}",
                "url_discusion": f"https://news.ycombinator.com/item?id={oid}",
                "puntos": h.get("points"),
                "comentarios": h.get("num_comments"),
                "horas_antiguedad": edad_h,
                "autor": h.get("author"),
            })

    # los más discutidos primero: puntos + comentarios (el debate vale tanto como el voto)
    salida.sort(key=lambda x: (x["puntos"] or 0) + (x["comentarios"] or 0), reverse=True)
    return salida


def sondear_x() -> dict:
    """¿x.com es legible sin sesión? Devuelve el diagnóstico, no una excusa."""
    try:
        html = _get("https://x.com/search?q=claude&f=trend", timeout=15).decode("utf-8", "ignore")
    except Exception as e:
        return {"legible": False, "motivo": f"sin acceso de red: {type(e).__name__}"}
    if "JavaScript is not available" in html or "enable JavaScript" in html:
        return {"legible": False, "motivo": "x.com exige JavaScript y sesión iniciada"}
    if 'data-testid="tweet"' in html:
        return {"legible": True, "motivo": "hay tweets en el HTML"}
    return {"legible": False, "motivo": "responde, pero sin tweets en el HTML"}


def main():
    ap = argparse.ArgumentParser(description="Descubre temas calientes sobre Claude con métricas reales.")
    ap.add_argument("--horas", type=int, default=96, help="Ventana de frescura (default 96)")
    ap.add_argument("--json", action="store_true", help="Salida JSON para el pipeline")
    ap.add_argument("--skip-x", action="store_true", help="No sondear x.com")
    args = ap.parse_args()

    x = {"legible": False, "motivo": "no sondeado"} if args.skip_x else sondear_x()
    hits = buscar_hn(args.horas)

    if args.json:
        json.dump({"x": x, "candidatos": hits}, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return

    print(f"x.com legible: {'sí' if x['legible'] else 'NO'} ({x['motivo']})")
    print(f"\nHacker News — {len(hits)} discusiones sobre Claude/Anthropic en las últimas {args.horas}h:\n")
    if not hits:
        print("  (ninguna) → no hay conversación caliente; el Paso 1 debe caer a WebSearch")
        return
    for h in hits[:12]:
        print(f"  ▲{h['puntos']:<5} 💬{h['comentarios']:<4} ({h['horas_antiguedad']:>5.1f}h)  {h['titulo'][:64]}")
        print(f"      {h['url'][:78]}")


if __name__ == "__main__":
    main()
