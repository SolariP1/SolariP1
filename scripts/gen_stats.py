"""Gera assets/stats.svg e assets/langs.svg a partir da API publica do GitHub.

Existe porque o github-readme-stats.vercel.app vive fora do ar (503) e o
github-profile-trophy devolve 402 — apontar o perfil pra um servico de
terceiro significa imagem quebrada sem aviso. Aqui os SVGs sao commitados
no proprio repo e o workflow stats.yml regenera todo dia.

Uso:
    python scripts/gen_stats.py            # sem token: 60 req/h, suficiente
    GITHUB_TOKEN=... python scripts/gen_stats.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

USER = "SolariP1"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# Paleta do banner, pra tudo ler como uma coisa so.
BG_FROM, BG_TO = "#050713", "#0d0820"
ACCENT = "#a78bfa"
ACCENT_2 = "#06b6d4"
TEXT = "#e6e8f0"
MUTED = "#8b93b0"

# Cores oficiais do linguist; o resto cai no roxo do tema.
LANG_COLORS = {
    "Python": "#3572A5",
    "TypeScript": "#3178C6",
    "JavaScript": "#F1E05A",
    "HTML": "#E34C26",
    "CSS": "#663399",
    "PHP": "#4F5D95",
    "Java": "#B07219",
    "Shell": "#89E051",
    "Dockerfile": "#384D54",
    "SQL": "#E38C00",
    "PLpgSQL": "#336790",
    "Hack": "#878787",
    "C#": "#178600",
    "Vue": "#41B883",
    "Makefile": "#427819",
}

# Linguagens que so poluem o grafico: nao dizem nada sobre o que eu escrevo.
LANG_IGNORE = {"Hack", "Batchfile", "Roff"}


def api(path: str):
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-profile-stats",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        if exc.code == 403:
            sys.exit("Rate limit da API do GitHub. Defina GITHUB_TOKEN e rode de novo.")
        raise


def collect():
    user = api(f"/users/{USER}")

    repos, page = [], 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&page={page}")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    own = [r for r in repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in own)

    # Bytes por linguagem somando todos os repos proprios: reflete o que eu
    # escrevo de verdade, nao so a linguagem "principal" que o GitHub chuta.
    totals: dict[str, int] = {}
    for repo in own:
        if repo["size"] == 0:
            continue
        for lang, count in api(f"/repos/{USER}/{repo['name']}/languages").items():
            if lang in LANG_IGNORE:
                continue
            totals[lang] = totals.get(lang, 0) + count

    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    return {
        "repos": len(own),
        "stars": stars,
        "followers": user["followers"],
        "langs": ranked,
        "lang_count": len(ranked),
    }


def shell(width: int, height: int, title: str, body: str) -> str:
    """Moldura comum: fundo espacial, estrelas piscando e borda em gradiente."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="{title}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{BG_FROM}"/>
      <stop offset="100%" stop-color="{BG_TO}"/>
    </linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{ACCENT}" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="{ACCENT_2}" stop-opacity="0.35"/>
    </linearGradient>
    <radialGradient id="haze" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{ACCENT}" stop-opacity="0.30"/>
      <stop offset="100%" stop-color="{ACCENT}" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="{width}" height="{height}" rx="14" fill="url(#bg)"/>
  <ellipse cx="{width - 40}" cy="24" rx="150" ry="90" fill="url(#haze)">
    <animate attributeName="opacity" values="0.5;1;0.5" dur="8s" repeatCount="indefinite"/>
  </ellipse>

  <g fill="#ffffff">
    <circle cx="26" cy="{height - 22}" r="1"><animate attributeName="opacity" values="0.2;1;0.2" dur="3.1s" repeatCount="indefinite"/></circle>
    <circle cx="{width - 30}" cy="{height - 34}" r="1.3"><animate attributeName="opacity" values="1;0.25;1" dur="4.3s" repeatCount="indefinite"/></circle>
    <circle cx="{width - 74}" cy="18" r="1"><animate attributeName="opacity" values="0.3;0.95;0.3" dur="2.7s" repeatCount="indefinite"/></circle>
    <circle cx="{width // 2}" cy="12" r="0.9"><animate attributeName="opacity" values="0.9;0.2;0.9" dur="5.2s" repeatCount="indefinite"/></circle>
  </g>

  <rect x="0.75" y="0.75" width="{width - 1.5}" height="{height - 1.5}" rx="13.5"
        fill="none" stroke="url(#edge)" stroke-width="1.5"/>

  <g font-family="Segoe UI, Helvetica Neue, Arial, sans-serif">
    <text x="22" y="34" fill="{ACCENT}" font-size="15" font-weight="700" letter-spacing="1.2">{title}</text>
{body}
  </g>
</svg>
"""


ICONS = {
    # Traçados no estilo lucide: 24x24, stroke 2, pontas arredondadas.
    "folder": "M4 20a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2z",
    "star": "M12 3l2.7 5.5 6.1.9-4.4 4.3 1 6-5.4-2.9L6.6 19.7l1-6L3.2 9.4l6.1-.9z",
    "users": "M16 20v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 4a4 4 0 1 1 0 8 4 4 0 0 1 0-8M22 20v-2a4 4 0 0 0-3-3.9",
    "code": "M16 18l6-6-6-6M8 6l-6 6 6 6",
}


def stats_svg(data: dict) -> str:
    rows = [
        ("folder", "Repositorios", data["repos"]),
        ("star", "Estrelas recebidas", data["stars"]),
        ("users", "Seguidores", data["followers"]),
        ("code", "Linguagens usadas", data["lang_count"]),
    ]

    body = []
    for i, (icon, label, value) in enumerate(rows):
        y = 74 + i * 38
        delay = 0.15 * i
        body.append(f"""    <g opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.5s" begin="{delay:.2f}s" fill="freeze"/>
      <g transform="translate(22 {y - 15}) scale(0.83)" fill="none" stroke="{ACCENT}"
         stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="{ICONS[icon]}"/>
      </g>
      <text x="56" y="{y}" fill="{TEXT}" font-size="14">{label}</text>
      <text x="418" y="{y}" fill="{ACCENT}" font-size="19" font-weight="700" text-anchor="end">{value}</text>
    </g>""")

    return shell(440, 226, "PANORAMA", "\n".join(body))


def langs_svg(data: dict, top: int = 6) -> str:
    langs = data["langs"][:top]
    if not langs:
        return shell(440, 226, "LINGUAGENS", '    <text x="22" y="80" fill="%s" font-size="13">Sem dados</text>' % MUTED)

    total = sum(v for _, v in data["langs"])
    bar_x, bar_w, bar_y = 22, 396, 52

    # Barra empilhada: cada faixa cresce a partir da largura zero.
    stacked, offset = [], 0.0
    for i, (lang, count) in enumerate(langs):
        w = bar_w * count / total
        color = LANG_COLORS.get(lang, ACCENT)
        stacked.append(
            f'    <rect x="{bar_x + offset:.1f}" y="{bar_y}" width="0" height="10" fill="{color}">'
            f'<animate attributeName="width" from="0" to="{w:.1f}" dur="0.9s" '
            f'begin="{0.1 * i:.2f}s" fill="freeze"/></rect>'
        )
        offset += w

    body = [
        f'    <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5" fill="#1b1830"/>',
        f'    <clipPath id="barclip"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5"/></clipPath>',
        '    <g clip-path="url(#barclip)">',
        *stacked,
        "    </g>",
    ]

    # Duas colunas de legenda embaixo da barra.
    for i, (lang, count) in enumerate(langs):
        col, row = i % 2, i // 2
        x = 22 + col * 205
        y = 96 + row * 30
        pct = 100 * count / total
        color = LANG_COLORS.get(lang, ACCENT)
        body.append(f"""    <g opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.5s" begin="{0.5 + 0.1 * i:.2f}s" fill="freeze"/>
      <circle cx="{x + 5}" cy="{y - 4}" r="5" fill="{color}"/>
      <text x="{x + 18}" y="{y}" fill="{TEXT}" font-size="13">{lang}</text>
      <text x="{x + 180}" y="{y}" fill="{MUTED}" font-size="12" text-anchor="end">{pct:.1f}%</text>
    </g>""")

    return shell(440, 226, "LINGUAGENS", "\n".join(body))


def main() -> None:
    data = collect()
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "stats.svg").write_text(stats_svg(data), encoding="utf-8")
    (ASSETS / "langs.svg").write_text(langs_svg(data), encoding="utf-8")
    print(f"repos={data['repos']} estrelas={data['stars']} seguidores={data['followers']}")
    print("linguagens: " + ", ".join(f"{k}" for k, _ in data["langs"][:6]))


if __name__ == "__main__":
    main()
