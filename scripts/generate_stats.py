#!/usr/bin/env python3
"""Generate GitHub stats SVG cards for the profile README.

Self-hosted replacement for github-readme-stats.vercel.app, which is
frequently paused. Uses only the standard library and the GitHub REST API,
authenticated with the workflow's built-in GITHUB_TOKEN. All data queried is
public.
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from urllib.error import HTTPError

USERNAME = "lorenzoliuzzo"
API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT_DIR = Path(__file__).resolve().parent.parent / "generated"

ACCENT = "#26647f"
TEXT = "#21262b"
MUTED = "#5f6971"
BORDER = "#e5e1d8"
BG = "#fdfcfa"

# GitHub's canonical language colors, for the top-languages card.
LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "C++": "#f34b7d",
    "C": "#555555",
    "Julia": "#a270ba",
    "Nim": "#ffc200",
    "Jupyter Notebook": "#DA5B0B",
    "TeX": "#3D6117",
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Shell": "#89e051",
    "Makefile": "#427819",
    "CMake": "#DA3434",
}
DEFAULT_LANGUAGE_COLOR = "#8a939b"


def _request(url: str, headers: dict[str, str] | None = None) -> object:
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", USERNAME)
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def fetch_user() -> dict:
    return _request(f"{API}/users/{USERNAME}")


def fetch_repos() -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        batch = _request(f"{API}/users/{USERNAME}/repos?per_page=100&page={page}&type=owner")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def fetch_language_bytes(repos: list[dict]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        try:
            langs = _request(f"{API}/repos/{USERNAME}/{repo['name']}/languages")
        except HTTPError:
            continue
        for lang, count in langs.items():
            totals[lang] = totals.get(lang, 0) + count
    return totals


def fetch_commit_count() -> int:
    try:
        result = _request(
            f"{API}/search/commits?q=author:{USERNAME}",
            headers={"Accept": "application/vnd.github.cloak-preview+json"},
        )
    except HTTPError:
        return 0
    return result.get("total_count", 0)


def render_stats_card(*, stars: int, commits: int, repos: int, followers: int) -> str:
    rows = [
        ("Total stars", f"{stars:,}"),
        ("Total commits", f"{commits:,}"),
        ("Public repos", f"{repos:,}"),
        ("Followers", f"{followers:,}"),
    ]
    row_height = 28
    top_pad = 52
    height = top_pad + row_height * len(rows) + 16
    body = "\n".join(
        f'<text x="24" y="{top_pad + i * row_height}" class="label">{label}</text>'
        f'<text x="296" y="{top_pad + i * row_height}" class="value" text-anchor="end">{value}</text>'
        for i, (label, value) in enumerate(rows)
    )
    return f"""<svg width="320" height="{height}" viewBox="0 0 320 {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GitHub stats for {USERNAME}">
  <title>GitHub stats for {USERNAME}</title>
  <style>
    .title {{ font: 600 15px -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; fill: {ACCENT}; }}
    .label {{ font: 400 13px -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; fill: {MUTED}; }}
    .value {{ font: 600 13px -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; fill: {TEXT}; }}
  </style>
  <rect x="0.5" y="0.5" width="319" height="{height - 1}" rx="8" fill="{BG}" stroke="{BORDER}" />
  <text x="24" y="30" class="title">{USERNAME}'s GitHub stats</text>
  {body}
</svg>"""


def render_top_langs_card(language_bytes: dict[str, int], *, limit: int = 6) -> str:
    total = sum(language_bytes.values()) or 1
    top = sorted(language_bytes.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    row_height = 26
    top_pad = 52
    height = top_pad + row_height * len(top) + 8
    bars = []
    for i, (lang, count) in enumerate(top):
        pct = count / total * 100
        bar_width = 160 * count / total
        color = LANGUAGE_COLORS.get(lang, DEFAULT_LANGUAGE_COLOR)
        y = top_pad + i * row_height - 14
        bars.append(
            f'<text x="24" y="{top_pad + i * row_height}" class="label">{lang}</text>'
            f'<rect x="150" y="{y}" width="160" height="10" rx="5" fill="{BORDER}" />'
            f'<rect x="150" y="{y}" width="{bar_width:.1f}" height="10" rx="5" fill="{color}" />'
            f'<text x="316" y="{top_pad + i * row_height}" class="pct" text-anchor="end">{pct:.1f}%</text>'
        )
    body = "\n  ".join(bars)
    return f"""<svg width="340" height="{height}" viewBox="0 0 340 {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Most used languages for {USERNAME}">
  <title>Most used languages for {USERNAME}</title>
  <style>
    .title {{ font: 600 15px -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; fill: {ACCENT}; }}
    .label {{ font: 400 12px -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; fill: {MUTED}; }}
    .pct {{ font: 600 12px -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; fill: {TEXT}; }}
  </style>
  <rect x="0.5" y="0.5" width="339" height="{height - 1}" rx="8" fill="{BG}" stroke="{BORDER}" />
  <text x="24" y="30" class="title">Most used languages</text>
  {body}
</svg>"""


def main() -> None:
    user = fetch_user()
    repos = fetch_repos()
    stars = sum(r["stargazers_count"] for r in repos if not r.get("fork"))
    commits = fetch_commit_count()
    languages = fetch_language_bytes(repos)

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "stats.svg").write_text(
        render_stats_card(
            stars=stars,
            commits=commits,
            repos=user["public_repos"],
            followers=user["followers"],
        )
    )
    (OUT_DIR / "top-langs.svg").write_text(render_top_langs_card(languages))


if __name__ == "__main__":
    main()
