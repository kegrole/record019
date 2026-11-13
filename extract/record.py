"""Record assembly and the missing-value marker."""

import hashlib

MISSING = "missing"


def make_record_id(source_url):
    digest = hashlib.sha1(source_url.encode("utf-8")).hexdigest()
    return "rec-" + digest[:12]


def build_record(source_url, page_type, values, missing):
    fields = {}
    for name, value in values.items():
        fields[name] = value if value is not None else MISSING
    return {
        "record_id": make_record_id(source_url),
        "source_url": source_url,
        "page_type": page_type,
        "status": "partial" if missing else "ok",
        "missing": list(missing),
        "fields": fields,
    }
