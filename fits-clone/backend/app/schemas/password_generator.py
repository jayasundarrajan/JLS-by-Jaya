from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID


class OutfitCreate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = None  # manual | ai_saved


class OutfitOut(BaseModel):
    id: UUID
    user_id: UUID
    name: Optional[str]
    notes: Optional[str]
    source: Optional[str]
    is_archived: bool

    class Config:
        from_attributes = True


class OutfitItemCreate(BaseModel):
    closet_item_id: UUID

    # Optional: if omitted, backend will default to center (0.5, 0.5)
    x: Optional[float] = Field(None, ge=0.0, le=1.0)
    y: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Optional: backend defaults if omitted
    scale: Optional[float] = Field(None, gt=0.0)
    rotation: Optional[float] = None
    z_index: Optional[int] = None


class OutfitItemBulkPatch(BaseModel):
    id: UUID
    x: Optional[float] = Field(None, ge=0.0, le=1.0)
    y: Optional[float] = Field(None, ge=0.0, le=1.0)
    scale: Optional[float] = Field(None, gt=0.0)
    rotation: Optional[float] = None
    z_index: Optional[int] = None


class OutfitItemsBulkUpdate(BaseModel):
    items: List[OutfitItemBulkPatch]



class OutfitItemPatch(BaseModel):
    x: Optional[float] = Field(None, ge=0.0, le=1.0)
    y: Optional[float] = Field(None, ge=0.0, le=1.0)
    scale: Optional[float] = Field(None, gt=0.0)
    rotation: Optional[float] = None
    z_index: Optional[int] = None


class OutfitItemOut(BaseModel):
    id: UUID
    outfit_id: UUID
    closet_item_id: UUID
    x: float
    y: float
    scale: float
    rotation: float
    z_index: int

    class Config:
        from_attributes = True

class OutfitItemRenderOut(OutfitItemOut):
    cutout_url: Optional[str] = None
    original_url: Optional[str] = None

class OutfitDetailOut(OutfitOut):
    items: List[OutfitItemRenderOut] = []

#!/usr/bin/env python3
"""
Keyword-based password generator (defensive / personal use).

- Input: JSON file containing {"keywords": ["word1", "word2", ...]}
- Output: N generated passwords, using randomized mixes of keywords + separators + digits + symbols.

Example:
  python3 keyword_password_generator.py keywords.json --count 20 --min-len 14 --max-len 22
"""

from __future__ import annotations

import argparse
import json
import random
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_SEPARATORS = ["-", "_", ".", ":", "~"]
DEFAULT_SYMBOLS = list("!@#$%^&*?+=")


@dataclass(frozen=True)
class Config:
    count: int
    min_len: int
    max_len: int
    min_keywords: int
    max_keywords: int
    allow_leetspeak: bool
    capitalize_mode: str  # "none" | "first" | "random"
    separators: list[str]
    symbols: list[str]
    digits_min: int
    digits_max: int
    symbols_min: int
    symbols_max: int


LEET_MAP = {
    "a": ["a", "A", "4", "@"],
    "e": ["e", "E", "3"],
    "i": ["i", "I", "1", "!"],
    "o": ["o", "O", "0"],
    "s": ["s", "S", "$", "5"],
    "t": ["t", "T", "7"],
}


def load_keywords(json_path: Path) -> list[str]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "keywords" not in data:
        raise ValueError('JSON must be an object like {"keywords": [...]}')

    keywords = data["keywords"]
    if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
        raise ValueError('"keywords" must be a list of strings')

    cleaned = []
    for k in keywords:
        k2 = k.strip()
        if k2:
            cleaned.append(k2)

    if len(cleaned) < 1:
        raise ValueError("Provide at least 1 non-empty keyword")

    return cleaned


def maybe_capitalize(word: str, mode: str) -> str:
    if mode == "none":
        return word
    if mode == "first":
        return word[:1].upper() + word[1:]
    if mode == "random":
        choice = random.choice(["lower", "first", "upper"])
        if choice == "lower":
            return word.lower()
        if choice == "upper":
            return word.upper()
        return word[:1].upper() + word[1:].lower()
    raise ValueError(f"Unknown capitalize_mode: {mode}")


def maybe_leet(word: str, enabled: bool) -> str:
    if not enabled:
        return word

    out_chars = []
    for ch in word:
        key = ch.lower()
        if key in LEET_MAP and random.random() < 0.35:  # probability of substituting
            out_chars.append(random.choice(LEET_MAP[key]))
        else:
            out_chars.append(ch)
    return "".join(out_chars)


def rand_digits(n: int) -> str:
    return "".join(random.choice(string.digits) for _ in range(n))


def rand_symbols(symbols: list[str], n: int) -> str:
    return "".join(random.choice(symbols) for _ in range(n))


def build_base_from_keywords(keywords: list[str], cfg: Config) -> str:
    k_count = random.randint(cfg.min_keywords, cfg.max_keywords)
    chosen = random.choices(keywords, k=k_count)

    transformed = []
    for w in chosen:
        w2 = maybe_capitalize(w, cfg.capitalize_mode)
        w3 = maybe_leet(w2, cfg.allow_leetspeak)
        transformed.append(w3)

    sep = random.choice(cfg.separators) if cfg.separators else ""
    base = sep.join(transformed)

    if cfg.separators and random.random() < 0.2:
        base = random.choice(cfg.separators) + base
    if cfg.separators and random.random() < 0.2:
        base = base + random.choice(cfg.separators)

    return base


def enforce_length(s: str, cfg: Config) -> str:
    target = random.randint(cfg.min_len, cfg.max_len)

    if len(s) > target:
        return s[:target]

    while len(s) < target:
        pick = random.random()
        if pick < 0.50:
            s += random.choice(string.digits)
        elif pick < 0.85 and cfg.symbols:
            s += random.choice(cfg.symbols)
        elif cfg.separators:
            s += random.choice(cfg.separators)
        else:
            s += random.choice(string.ascii_letters)
    return s


def generate_password(keywords: list[str], cfg: Config) -> str:
    base = build_base_from_keywords(keywords, cfg)

    d_count = random.randint(cfg.digits_min, cfg.digits_max)
    s_count = random.randint(cfg.symbols_min, cfg.symbols_max)

    extras = []
    if d_count > 0:
        extras.append(rand_digits(d_count))
    if s_count > 0 and cfg.symbols:
        extras.append(rand_symbols(cfg.symbols, s_count))

    random.shuffle(extras)
    extra_blob = "".join(extras)

    if extra_blob:
        mode = random.choice(["start", "end", "middle"])
        if mode == "start":
            candidate = extra_blob + base
        elif mode == "end":
            candidate = base + extra_blob
        else:
            mid = len(base) // 2
            candidate = base[:mid] + extra_blob + base[mid:]
    else:
        candidate = base

    candidate = enforce_length(candidate, cfg)

    return candidate or enforce_length("X", cfg)


def unique_passwords(keywords: list[str], cfg: Config) -> list[str]:
    seen = set()
    out = []
    attempts = 0
    max_attempts = cfg.count * 50  # avoid infinite loop

    while len(out) < cfg.count and attempts < max_attempts:
        attempts += 1
        pw = generate_password(keywords, cfg)
        if pw not in seen:
            seen.add(pw)
            out.append(pw)

    if len(out) < cfg.count:
        raise RuntimeError(
            f"Could only generate {len(out)} unique passwords after {attempts} attempts. "
            "Try increasing keyword variety or widening length bounds."
        )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("json_file", type=Path, help="Path to JSON file containing {'keywords': [...]}")

    p.add_argument("--count", type=int, default=10, help="How many passwords to generate")
    p.add_argument("--min-len", type=int, default=14, help="Minimum password length")
    p.add_argument("--max-len", type=int, default=22, help="Maximum password length")

    p.add_argument("--min-keywords", type=int, default=2, help="Minimum keywords per password")
    p.add_argument("--max-keywords", type=int, default=3, help="Maximum keywords per password")

    p.add_argument("--leetspeak", action="store_true", help="Enable occasional leetspeak substitutions")
    p.add_argument(
        "--capitalize",
        choices=["none", "first", "random"],
        default="random",
        help="Capitalization mode for keywords"
    )

    p.add_argument("--digits-min", type=int, default=2)
    p.add_argument("--digits-max", type=int, default=4)
    p.add_argument("--symbols-min", type=int, default=1)
    p.add_argument("--symbols-max", type=int, default=2)

    p.add_argument("--separators", type=str, default="".join(DEFAULT_SEPARATORS),
                   help="Separator characters to use (string of chars). Example: '-_.'")
    p.add_argument("--symbols", type=str, default="".join(DEFAULT_SYMBOLS),
                   help="Symbol characters to use (string of chars). Example: '!@#$'")

    return p.parse_args()


def main() -> int:
    args = parse_args()

    if args.min_len > args.max_len:
        raise SystemExit("--min-len must be <= --max-len")
    if args.min_keywords > args.max_keywords:
        raise SystemExit("--min-keywords must be <= --max-keywords")

    keywords = load_keywords(args.json_file)

    cfg = Config(
        count=args.count,
        min_len=args.min_len,
        max_len=args.max_len,
        min_keywords=args.min_keywords,
        max_keywords=args.max_keywords,
        allow_leetspeak=args.leetspeak,
        capitalize_mode=args.capitalize,
        separators=list(args.separators) if args.separators else [],
        symbols=list(args.symbols) if args.symbols else [],
        digits_min=args.digits_min,
        digits_max=args.digits_max,
        symbols_min=args.symbols_min,
        symbols_max=args.symbols_max,
    )

    passwords = unique_passwords(keywords, cfg)
    for pw in passwords:
        print(pw)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())