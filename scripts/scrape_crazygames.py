#!/usr/bin/env python3
import sys
import json
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def scrape_crazygames(url: str) -> dict:
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    text_all = " ".join(soup.stripped_strings)

    # Title
    title_tag = soup.find("h1")
    title = (
        title_tag.get_text(strip=True)
        if title_tag
        else (soup.find("meta", attrs={"property": "og:title"}) or {}).get("content", "").strip()
    )

    # Description: first non-empty paragraph
    description = ""
    for p in soup.find_all("p"):
        t = p.get_text(strip=True)
        if t:
            description = t
            break

    # Developer
    developer = None
    for el in soup.find_all(string=re.compile(r"Developer", re.I)):
        parent = el.parent
        sib = parent.find_next_sibling()
        if sib and sib.get_text(strip=True):
            developer = sib.get_text(strip=True)
            break

    # Rating and votes
    rating = None
    votes = None
    m = re.search(r"Rating\s+([0-9.]+)\s*\(([\d,]+)\s+votes?\)", text_all, re.I)
    if m:
        rating = float(m.group(1))
        votes = int(m.group(2).replace(",", ""))

    def extract_after(label_pattern: str):
        m = re.search(label_pattern + r"\s+([A-Za-z0-9 (),.\-]+)", text_all, re.I)
        return m.group(1).strip() if m else None

    technology = extract_after(r"Technology")
    platform = extract_after(r"Platform")
    release_date = extract_after(r"(?:Release Date|Released)")
    last_updated = extract_after(r"Last Updated")

    # Tags
    tags = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/c/" in href or "/t/" in href:
            label = a.get_text(strip=True)
            if label and label not in tags:
                tags.append(label)

    # Controls
    controls_pc = []
    controls_mobile = []
    pc_section = False
    mobile_section = False
    for el in soup.find_all(True):
        txt = el.get_text(strip=True)
        if re.fullmatch(r"PC Controls", txt, re.I):
            pc_section, mobile_section = True, False
            continue
        if re.fullmatch(r"Mobile Controls", txt, re.I):
            pc_section, mobile_section = False, True
            continue
        if el.name == "li" and (pc_section or mobile_section):
            if pc_section:
                controls_pc.append(txt)
            if mobile_section:
                controls_mobile.append(txt)

    # Slug from URL
    path = urlparse(url).path
    m = re.search(r"/game/([^/?#]+)", path)
    slug = m.group(1) if m else None

    return {
        "url": url,
        "slug": slug,
        "title": title,
        "description": description,
        "developer": developer,
        "rating": rating,
        "votes": votes,
        "technology": technology,
        "platform": platform,
        "releaseDate": release_date,
        "lastUpdated": last_updated,
        "tags": tags,
        "controls": {
            "pc": controls_pc,
            "mobile": controls_mobile,
        },
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python scrape_crazygames.py <crazygames-game-url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    try:
        data = scrape_crazygames(url)
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

