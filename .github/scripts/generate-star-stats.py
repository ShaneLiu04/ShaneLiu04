#!/usr/bin/env python3
"""Generate a Vercel-style GitHub star stats SVG."""

import json
import os
import urllib.request
from datetime import datetime, timezone


def fetch_repos(username: str, token: str | None = None) -> list[dict]:
    """Fetch public repositories for a GitHub user."""
    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
    headers = {
        "User-Agent": "github-star-stats-generator",
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def escape_xml(text: str) -> str:
    """Escape special XML characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def generate_svg(username: str, repos: list[dict]) -> str:
    """Generate the star stats SVG."""
    # Exclude forks
    own_repos = [r for r in repos if not r.get("fork", False)]
    own_repos.sort(key=lambda r: r["stargazers_count"], reverse=True)

    total_stars = sum(r["stargazers_count"] for r in own_repos)
    repo_count = len(own_repos)
    top_repos = own_repos[:5]
    max_stars = top_repos[0]["stargazers_count"] if top_repos else 0

    # Colors
    bg_start = "#0d1117"
    bg_end = "#161b22"
    border = "#30363d"
    text_muted = "#8b949e"
    text_bright = "#c9d1d9"
    accent = "#f1e05a"
    accent2 = "#ff9f43"

    width = 800
    height = 320
    left_x = 60
    right_x = 420
    row_y = 110
    row_height = 40
    bar_max_width = 340

    # Build repo rows
    repo_rows = []
    for i, repo in enumerate(top_repos):
        name = escape_xml(repo["name"])
        if len(name) > 28:
            name = name[:25] + "..."
        stars = repo["stargazers_count"]
        bar_width = (stars / max_stars) * bar_max_width if max_stars else 0
        y = row_y + i * row_height

        repo_rows.append(f"""
        <g transform="translate({right_x}, {y})">
            <text x="0" y="-6" fill="{text_bright}" font-size="14" font-weight="500" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Helvetica, Arial, sans-serif">{name}</text>
            <rect x="0" y="4" width="{bar_max_width}" height="6" rx="3" fill="#21262d"/>
            <rect x="0" y="4" width="{bar_width:.1f}" height="6" rx="3" fill="url(#barGradient)"/>
            <text x="{bar_max_width + 12}" y="11" fill="{accent}" font-size="13" font-weight="600" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Helvetica, Arial, sans-serif">{stars}</text>
        </g>
        """)

    rows_svg = "\n".join(repo_rows)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
    <defs>
        <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="{bg_start}"/>
            <stop offset="100%" stop-color="{bg_end}"/>
        </linearGradient>
        <linearGradient id="barGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="{accent}"/>
            <stop offset="100%" stop-color="{accent2}"/>
        </linearGradient>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2" result="blur"/>
            <feComposite in="SourceGraphic" in2="blur" operator="over"/>
        </filter>
    </defs>

    <!-- Card background -->
    <rect width="{width}" height="{height}" rx="16" ry="16" fill="url(#bgGradient)" stroke="{border}" stroke-width="1"/>

    <!-- Left side: total stars -->
    <g transform="translate({left_x}, 70)">
        <text fill="{text_muted}" font-size="15" font-weight="500" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Helvetica, Arial, sans-serif">Star Achievements</text>
        <g transform="translate(0, 55)">
            <!-- Star icon -->
            <svg x="0" y="-42" width="48" height="48" viewBox="0 0 24 24" fill="{accent}">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
            <text x="58" y="0" fill="{accent}" font-size="64" font-weight="700" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Helvetica, Arial, sans-serif" filter="url(#glow)">{total_stars}</text>
        </g>
        <text y="115" fill="{text_bright}" font-size="15" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Helvetica, Arial, sans-serif">{repo_count} public repositories</text>
        <text y="138" fill="{text_muted}" font-size="12" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Helvetica, Arial, sans-serif">Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</text>
    </g>

    <!-- Vertical divider -->
    <line x1="380" y1="50" x2="380" y2="{height - 50}" stroke="{border}" stroke-width="1"/>

    <!-- Right side: top repositories -->
    <g transform="translate(0, 0)">
        <text x="{right_x}" y="70" fill="{text_muted}" font-size="15" font-weight="500" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Helvetica, Arial, sans-serif">Top Starred Repositories</text>
        {rows_svg}
    </g>
</svg>"""

    return svg


def main():
    username = os.environ.get("GITHUB_USERNAME", "ShaneLiu04")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("METRICS_TOKEN")
    output_path = os.environ.get("OUTPUT_PATH", "assets/star-stats.svg")

    repos = fetch_repos(username, token)
    svg = generate_svg(username, repos)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Generated {output_path} with {sum(r['stargazers_count'] for r in repos if not r.get('fork'))} total stars")


if __name__ == "__main__":
    main()
