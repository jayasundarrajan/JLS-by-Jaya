#!/usr/bin/env python3
"""
Phishing URL Analyzer (defensive)
- Normalizes a URL
- Extracts host / domain structure
- Flags common suspicious indicators (heuristic)

No network calls by default.
Python 3.10+
"""

from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit, unquote

SUSPICIOUS_TLDS = {
    "zip", "mov", "top", "xyz", "click", "country", "stream", "kim", "gq", "tk", "ml", "cf"
}

BRAND_BAIT = {
    "paypal", "apple", "microsoft", "office", "outlook", "google", "gmail",
    "bank", "chase", "wellsfargo", "amex", "visa", "mastercard", "signin",
    "login", "verify", "security", "update", "support"
}

SHORTENERS = {
    "bit.ly", "t.co", "tinyurl.com", "goo.gl", "is.gd", "buff.ly", "rebrand.ly"
}

IPV4_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


@dataclass
class Finding:
    code: str
    severity: str  # "low" | "medium" | "high"
    message: str


def _is_valid_ipv4(host: str) -> bool:
    if not IPV4_RE.match(host):
        return False
    parts = host.split(".")
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def _normalize_url(raw: str) -> str:
    """
    Normalize enough for analysis:
    - Add scheme if missing (assume https)
    - Decode % escapes for display (careful: for analysis we also keep raw)
    """
    raw = raw.strip()
    if not raw:
        raise ValueError("Empty input")

    if "://" not in raw:
        raw = "https://" + raw

    parts = urlsplit(raw)

    scheme = parts.scheme.lower()
    netloc = parts.netloc


    userinfo = ""
    hostport = netloc
    if "@" in netloc:
        userinfo, hostport = netloc.rsplit("@", 1)

    host = hostport
    port = ""
    if ":" in hostport and not hostport.endswith("]"):  # crude IPv6 bracket avoidance
        host, port = hostport.rsplit(":", 1)

    host_l = host.lower()

    if (scheme == "http" and port == "80") or (scheme == "https" and port == "443"):
        port = ""

    rebuilt_hostport = host_l if not port else f"{host_l}:{port}"
    rebuilt_netloc = rebuilt_hostport if not userinfo else f"{userinfo}@{rebuilt_hostport}"

    return urlunsplit((scheme, rebuilt_netloc, parts.path, parts.query, parts.fragment))


def _to_ascii_idna(host: str) -> tuple[str, bool]:
    """
    Convert Unicode host to IDNA ASCII form if needed.
    Returns (ascii_host, was_idn).
    """
    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError:
        return host, False
    return ascii_host, (ascii_host != host)


def analyze_url(raw_url: str) -> tuple[str, list[Finding]]:
    normalized = _normalize_url(raw_url)
    parts = urlsplit(normalized)

    findings: list[Finding] = []

    host = parts.hostname or ""
    if not host:
        findings.append(Finding("NO_HOST", "high", "URL has no host component."))
        return normalized, findings

    ascii_host, was_idn = _to_ascii_idna(host)
    if was_idn:
        findings.append(Finding(
            "IDN_HOST",
            "medium",
            f"Internationalized domain name detected. ASCII/Punycode form: {ascii_host}"
        ))


    if any(ord(c) > 127 for c in host):
        findings.append(Finding(
            "NON_ASCII_HOST",
            "medium",
            "Host contains non-ASCII characters (potential lookalike/homoglyph risk)."
        ))

    if _is_valid_ipv4(host):
        findings.append(Finding(
            "IP_HOST",
            "high",
            "Host is a raw IPv4 address (commonly used in phishing)."
        ))

    if parts.netloc and "@" in parts.netloc:
        findings.append(Finding(
            "USERINFO_AT",
            "high",
            "URL contains userinfo (username@host). Can be used to confuse users."
        ))

    labels = ascii_host.split(".")
    if len(labels) >= 2:
        tld = labels[-1]
        if tld in SUSPICIOUS_TLDS:
            findings.append(Finding(
                "SUSPICIOUS_TLD",
                "medium",
                f"TLD '.{tld}' is frequently abused (heuristic)."
            ))

    if len(labels) >= 4:
        findings.append(Finding(
            "MANY_SUBDOMAINS",
            "medium",
            f"Host has many labels ({len(labels)}). Excessive subdomains can hide the real domain."
        ))

    # Shortener
    if ascii_host in SHORTENERS:
        findings.append(Finding(
            "URL_SHORTENER",
            "medium",
            "Known URL shortener domain. Destination is obscured."
        ))

    # Hyphen-heavy domains
    hyphens = ascii_host.count("-")
    if hyphens >= 3:
        findings.append(Finding(
            "HYPHEN_HEAVY",
            "low",
            f"Host contains many hyphens ({hyphens}). Often seen in lookalike domains."
        ))

    # Path / query bait words
    decoded_path = unquote(parts.path or "").lower()
    decoded_query = unquote(parts.query or "").lower()
    joined = f"{ascii_host.lower()} {decoded_path} {decoded_query}"

    bait_hits = sorted({w for w in BRAND_BAIT if w in joined})
    if bait_hits:
        findings.append(Finding(
            "BAIT_KEYWORDS",
            "medium",
            f"Contains common bait keywords: {', '.join(bait_hits)} (heuristic)."
        ))

    # Long URL
    if len(normalized) >= 120:
        findings.append(Finding(
            "VERY_LONG_URL",
            "low",
            f"URL is very long ({len(normalized)} chars), which can hide suspicious parts."
        ))

    if parts.query.count("&") >= 6:
        findings.append(Finding(
            "MANY_PARAMS",
            "low",
            "URL contains many query parameters; sometimes used to obfuscate tracking/phishing."
        ))

    if "https" in decoded_path or "secure" in decoded_path:
        findings.append(Finding(
            "SECURE_IN_PATH",
            "low",
            "Contains 'https'/'secure' in the path—often used to create false trust."
        ))

    return normalized, findings


def risk_score(findings: list[Finding]) -> int:
    weights = {"low": 1, "medium": 3, "high": 6}
    return sum(weights.get(f.severity, 0) for f in findings)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(f"Usage: {argv[0]} <url1> [url2 ...]\n")
        print("Example:")
        print(f"  {argv[0]} https://example.com/login?verify=1")
        return 2

    for raw in argv[1:]:
        try:
            normalized, findings = analyze_url(raw)
        except Exception as e:
            print(f"\nInput: {raw}\n  ERROR: {e}")
            continue

        score = risk_score(findings)
        verdict = "LOW" if score < 4 else "MEDIUM" if score < 10 else "HIGH"

        print("\n" + "=" * 60)
        print(f"Input:      {raw}")
        print(f"Normalized: {normalized}")
        print(f"Risk score: {score}  ->  {verdict}")

        if not findings:
            print("Findings:   None (no common heuristic flags).")
        else:
            print("Findings:")
            for f in findings:
                print(f"  - [{f.severity.upper():6}] {f.code}: {f.message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))