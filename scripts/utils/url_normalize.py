#!/usr/bin/env python3
"""URL 规范化 — 用于稳定去重。"""
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "ref", "source", "mc_", "igsh")


def normalize_url(url):
    if not url:
        return ""
    p = urlparse(url)
    scheme = "https"
    netloc = p.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = p.path.rstrip("/")
    kept = sorted(
        (k, v) for k, v in parse_qsl(p.query)
        if not any(k.lower().startswith(t) for t in TRACKING_PREFIXES)
    )
    query = urlencode(kept)
    return urlunparse((scheme, netloc, path, "", query, ""))
