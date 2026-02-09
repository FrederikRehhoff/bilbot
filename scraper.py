#!/usr/bin/env python3
"""Simple Bilbasen scraper.

This script lets you define search filters and prints a list of car results.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from html import unescape
from typing import Any
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
from urllib.error import URLError


BASE_URL = "https://www.bilbasen.dk/brugt/bil"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


@dataclass(slots=True)
class CarListing:
    title: str
    price: str | None
    link: str
    location: str | None = None


class BilbasenScraper:
    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout

    def search(self, filters: dict[str, str], limit: int = 20) -> list[CarListing]:
        query = urlencode(filters)
        url = f"{BASE_URL}?{query}" if query else BASE_URL
        request = Request(url=url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=self.timeout) as response:
            html = response.read().decode("utf-8", errors="replace")
        return self._parse_listings(html, limit=limit)

    def _parse_listings(self, html: str, limit: int = 20) -> list[CarListing]:
        listings = self._parse_json_ld(html)
        if not listings:
            listings = self._parse_card_links(html)
        return listings[:limit]

    def _parse_json_ld(self, html: str) -> list[CarListing]:
        listings: list[CarListing] = []
        scripts = re.findall(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        for raw in scripts:
            payload = unescape(raw).strip()
            if not payload:
                continue
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue

            blocks = data if isinstance(data, list) else [data]
            for block in blocks:
                if not isinstance(block, dict) or block.get("@type") != "ItemList":
                    continue
                for item in block.get("itemListElement", []):
                    parsed = self._listing_from_item(item)
                    if parsed:
                        listings.append(parsed)
        return listings

    def _listing_from_item(self, item: dict[str, Any]) -> CarListing | None:
        if not isinstance(item, dict):
            return None

        entry = item.get("item") if isinstance(item.get("item"), dict) else item
        if not isinstance(entry, dict):
            return None

        title = entry.get("name")
        link = entry.get("url")
        if not title or not link:
            return None

        offers = entry.get("offers") if isinstance(entry.get("offers"), dict) else {}
        price = offers.get("price")
        currency = offers.get("priceCurrency")
        formatted_price = f"{price} {currency}" if price and currency else (str(price) if price else None)

        location = None
        address = entry.get("address")
        if isinstance(address, dict):
            location = address.get("addressLocality")

        return CarListing(title=str(title), price=formatted_price, link=str(link), location=location)

    def _parse_card_links(self, html: str) -> list[CarListing]:
        listings: list[CarListing] = []
        seen_links: set[str] = set()

        for href, inner_text in re.findall(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL):
            if "/biler/" not in href:
                continue
            link = urljoin("https://www.bilbasen.dk", unescape(href.strip()))
            if link in seen_links:
                continue

            text = re.sub(r"<[^>]+>", " ", inner_text)
            title = " ".join(unescape(text).split())
            if not title:
                continue

            seen_links.add(link)
            listings.append(CarListing(title=title, price=None, link=link, location=None))
        return listings


def parse_filter_args(raw_filters: list[str]) -> dict[str, str]:
    filters: dict[str, str] = {}
    for raw in raw_filters:
        if "=" not in raw:
            raise ValueError(f"Invalid --filter value '{raw}'. Use key=value format.")
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Invalid --filter value '{raw}'. Missing key.")
        filters[key] = value
    return filters


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape Bilbasen search results.")
    parser.add_argument(
        "--filter",
        action="append",
        default=[],
        help="Search filter in key=value format. Can be repeated.",
    )
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of results to print.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        filters = parse_filter_args(args.filter)
    except ValueError as exc:
        parser.error(str(exc))

    scraper = BilbasenScraper()
    try:
        results = scraper.search(filters=filters, limit=args.limit)
    except URLError as exc:
        parser.exit(status=1, message=f"Failed to fetch Bilbasen: {exc}\n")

    if not results:
        print("No listings found for the current filter set.")
        return

    for idx, listing in enumerate(results, start=1):
        print(f"{idx:>2}. {listing.title}")
        if listing.price:
            print(f"    Price: {listing.price}")
        if listing.location:
            print(f"    Location: {listing.location}")
        print(f"    URL: {listing.link}")


if __name__ == "__main__":
    main()