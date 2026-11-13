"""Value normalization: text, spec, price (integer cents), absolute URL."""

import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urljoin


def normalize_text(value):
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_spec(value):
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"\s+", "", value)
    return value.strip()


def normalize_price(value):
    cleaned = re.sub(r"[^0-9.,]", "", value)
    cleaned = cleaned.replace(",", "")
    if not cleaned:
        raise ValueError("no numeric content in price: %r" % value)
    amount = Decimal(cleaned)
    cents = (amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def normalize_url(value, source_url):
    return urljoin(source_url, value)


def normalize_value(kind, value, source_url=None):
    if kind == "none":
        return value
    if kind == "text":
        return normalize_text(value)
    if kind == "spec":
        return normalize_spec(value)
    if kind == "price":
        return normalize_price(value)
    if kind == "url":
        if not source_url:
            raise ValueError("url normalization requires a source_url")
        return normalize_url(value, source_url)
    raise ValueError("unknown normalizer: %r" % kind)
