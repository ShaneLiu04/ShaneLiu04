#!/usr/bin/env python3
"""Generate a self-hosted GitHub streak-stats SVG card.

The card is committed to ``assets/streak-stats.svg`` by the daily workflow, so
the README references a commit-pinned local asset: GitHub serves the raw URL
with the commit SHA, which busts the camo/browser cache automatically on every
regeneration. Day boundaries follow the GitHub contributions calendar (the same
day attribution the profile page shows) with an explicit Asia/Shanghai "today".
"""

import os
import re
import sys
import urllib.request
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

USER = os.environ.get("GITHUB_USERNAME", "ShaneLiu04")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "assets/streak-stats.svg")
TIMEZONE = ZoneInfo(os.environ.get("STREAK_TIMEZONE", "Asia/Shanghai"))
START_YEAR = int(os.environ.get("STREAK_START_YEAR", "2023"))

MONTHS = {
    name: index
    for index, name in enumerate(
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        start=1,
    )
}
DAY_PATTERN = re.compile(r"(\d+)\s+contributions?\s+on\s+([A-Z][a-z]+)\s+(\d+)")

BG = "#0d1117"
TEXT = "#c9d1d9"
DIVIDER = "#0ea5e9"
ACCENT = "#38bdf8"
FIRE = "#fbbf24"
FONT = '"Segoe UI", Ubuntu, sans-serif'


def fetch_year(year: int) -> dict[date, int]:
    """Fetch one year of contribution days from the public profile calendar."""
    url = f"https://github.com/users/{USER}/contributions?from={year}-01-01&to={year}-12-31"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "github-streak-stats-generator",
            "Accept": "text/html",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        html = response.read().decode("utf-8", errors="replace")

    days: dict[date, int] = {}
    for count, month_name, day_text in DAY_PATTERN.findall(html):
        month = MONTHS.get(month_name)
        if month is None:
            continue
        try:
            current = date(year, month, int(day_text))
        except ValueError:
            continue
        days[current] = max(days.get(current, 0), int(count))
    return days


def fetch_days() -> dict[date, int]:
    """Fetch the whole contribution history covered by the card."""
    today = datetime.now(TIMEZONE).date()
    days: dict[date, int] = {}
    for year in range(START_YEAR, today.year + 1):
        for day, count in fetch_year(year).items():
            if day <= today:
                days[day] = count
    return days


def compute_streaks(days: dict[date, int]) -> tuple[date | None, date | None, date | None, date | None]:
    """Return (current_start, current_end, longest_start, longest_end)."""
    active = sorted(day for day, count in days.items() if count > 0)
    if not active:
        return None, None, None, None

    today = datetime.now(TIMEZONE).date()
    current_end = today if days.get(today, 0) > 0 else today - timedelta(days=1)
    current_start = current_end
    if days.get(current_end, 0) > 0:
        while days.get(current_start - timedelta(days=1), 0) > 0:
            current_start -= timedelta(days=1)
    else:
        current_start = None
        current_end = None

    longest_start = longest_end = active[0]
    run_start = active[0]
    previous = active[0]
    for day in active[1:]:
        if day == previous + timedelta(days=1):
            previous = day
            continue
        if (previous - run_start).days > (longest_end - longest_start).days:
            longest_start, longest_end = run_start, previous
        run_start = previous = day
    if (previous - run_start).days > (longest_end - longest_start).days:
        longest_start, longest_end = run_start, previous

    return current_start, current_end, longest_start, longest_end


def format_short(day: date | None) -> str:
    return f"{day.strftime('%b')} {day.day}" if day else "-"


def format_long(day: date | None) -> str:
    return f"{day.strftime('%b')} {day.day}, {day.year}" if day else "-"


def escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render(days: dict[date, int]) -> str:
    total = sum(days.values())
    first_day = min((day for day, count in days.items() if count > 0), default=None)
    current_start, current_end, longest_start, longest_end = compute_streaks(days)
    current_len = (
        (current_end - current_start).days + 1 if current_start and current_end else 0
    )
    longest_len = (
        (longest_end - longest_start).days + 1 if longest_start and longest_end else 0
    )
    total_range = f"{format_long(first_day)} - Present" if first_day else "-"
    current_range = (
        f"{format_short(current_start)} - {format_short(current_end)}"
        if current_start
        else "-"
    )
    longest_range = (
        f"{format_short(longest_start)} - {format_short(longest_end)}"
        if longest_start
        else "-"
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 495 195" width="495" height="195" role="img" aria-label="GitHub streak stats">
    <style>
        text {{ font-family: {FONT}; }}
        .num {{ font-size: 28px; font-weight: 700; fill: {TEXT}; }}
        .label {{ font-size: 14px; font-weight: 400; fill: {TEXT}; }}
        .range {{ font-size: 12px; font-weight: 400; fill: {TEXT}; }}
        .accent-label {{ font-size: 14px; font-weight: 700; fill: {ACCENT}; }}
    </style>
    <rect width="495" height="195" rx="4.5" fill="{BG}"/>
    <line x1="165" y1="28" x2="165" y2="170" stroke="{DIVIDER}" stroke-width="1"/>
    <line x1="330" y1="28" x2="330" y2="170" stroke="{DIVIDER}" stroke-width="1"/>

    <text x="82.5" y="80" text-anchor="middle" class="num">{total:,}</text>
    <text x="82.5" y="116" text-anchor="middle" class="label">Total Contributions</text>
    <text x="82.5" y="146" text-anchor="middle" class="range">{escape(total_range)}</text>

    <text x="247.5" y="140" text-anchor="middle" class="accent-label">Current Streak</text>
    <text x="247.5" y="166" text-anchor="middle" class="range">{escape(current_range)}</text>
    <circle cx="247.5" cy="71" r="40" fill="none" stroke="{ACCENT}" stroke-width="5"/>
    <path d="M 1.5 0.67 C 1.5 0.67 2.24 3.32 2.24 5.47 C 2.24 7.53 0.89 9.2 -1.17 9.2 C -3.23 9.2 -4.79 7.53 -4.79 5.47 L -4.76 5.11 C -6.78 7.51 -8 10.62 -8 13.99 C -8 18.41 -4.42 22 0 22 C 4.42 22 8 18.41 8 13.99 C 8 8.6 5.41 3.79 1.5 0.67 Z M -0.29 19 C -2.07 19 -3.51 17.6 -3.51 15.86 C -3.51 14.24 -2.46 13.1 -0.7 12.74 C 1.07 12.38 2.9 11.53 3.92 10.16 C 4.31 11.45 4.51 12.81 4.51 14.2 C 4.51 16.85 2.36 19 -0.29 19 Z" fill="{FIRE}" transform="translate(247.5, 19.5)"/>
    <text x="247.5" y="80" text-anchor="middle" class="num">{current_len}</text>

    <text x="412.5" y="80" text-anchor="middle" class="num">{longest_len}</text>
    <text x="412.5" y="116" text-anchor="middle" class="label">Longest Streak</text>
    <text x="412.5" y="146" text-anchor="middle" class="range">{escape(longest_range)}</text>
</svg>
"""


def main() -> int:
    try:
        days = fetch_days()
    except Exception as error:  # noqa: BLE001 - keep the published asset on failure
        print(f"failed to fetch contributions: {error}", file=sys.stderr)
        return 1
    if not days:
        print("no contribution days parsed; refusing to overwrite the asset", file=sys.stderr)
        return 1
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        handle.write(render(days))
    print(f"wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
