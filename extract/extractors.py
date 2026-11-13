"""Rule evaluation: tag_text / attr / regex, candidate index, match filter."""

import re
from urllib.parse import urljoin

from .normalize import normalize_value
from .pagedetect import detect_page_type, find_product_blocks


def rule_candidates(rule, context):
    method = rule["method"]
    if method == "tag_text":
        elements = context.find_all(rule.get("tag"), rule.get("class"), rule.get("id"))
        values = [el.text() for el in elements]
    elif method == "attr":
        elements = context.find_all(rule.get("tag"), rule.get("class"), rule.get("id"))
        attr = rule["attr"]
        values = [el.attrs[attr] for el in elements if attr in el.attrs]
    elif method == "regex":
        pattern = re.compile(rule["pattern"])
        values = []
        for match in pattern.finditer(context.text()):
            values.append(match.group(1) if match.groups() else match.group(0))
    else:
        raise ValueError("unknown method: %r" % method)

    cleaned = []
    for value in values:
        value = value.strip()
        if value:
            cleaned.append(value)
    match_filter = rule.get("match")
    if match_filter:
        regex = re.compile(match_filter)
        cleaned = [v for v in cleaned if regex.search(v)]
    return cleaned


def apply_rule(rule, context):
    candidates = rule_candidates(rule, context)
    index = rule.get("index", 0)
    if 0 <= index < len(candidates):
        return candidates[index]
    return None


def extract_field(field_config, page_type, context):
    for rule in field_config["rules"]:
        source = rule.get("source", "any")
        if source not in ("any", page_type):
            continue
        value = apply_rule(rule, context)
        if value is not None:
            return value
    return None


def find_source_url(root, path):
    for node in root.find_all("link"):
        rel = node.attrs.get("rel", "")
        if "canonical" in rel.split() and node.attrs.get("href"):
            return node.attrs["href"]
    for node in root.find_all("base"):
        if node.attrs.get("href"):
            return urljoin(node.attrs["href"], path.name)
    return path.resolve().as_uri()


def extract_fields(config, root, source_url):
    page_type = detect_page_type(root)
    if page_type == "list":
        context = find_product_blocks(root)[0]
    else:
        context = root
    values = {}
    missing = []
    for name, field_config in config["fields"].items():
        raw = extract_field(field_config, page_type, context)
        if raw is None:
            values[name] = None
            missing.append(name)
        else:
            normalizer = field_config.get("normalize", "text")
            values[name] = normalize_value(normalizer, raw, source_url)
    return page_type, values, missing
