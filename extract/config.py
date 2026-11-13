"""Load and validate the JSON extraction config."""

import json

VALID_METHODS = ("tag_text", "attr", "regex")
VALID_SOURCES = ("list", "detail", "any")
VALID_NORMALIZERS = ("text", "spec", "price", "url", "none")


def load_config(path):
    with open(path, encoding="utf-8") as fh:
        config = json.load(fh)
    validate_config(config)
    return config


def validate_config(config):
    fields = config.get("fields")
    if not isinstance(fields, dict) or not fields:
        raise ValueError("config must contain a non-empty 'fields' object")
    for name, field in fields.items():
        rules = field.get("rules")
        if not isinstance(rules, list) or not rules:
            raise ValueError("field %r must declare at least one rule" % name)
        normalizer = field.get("normalize", "text")
        if normalizer not in VALID_NORMALIZERS:
            raise ValueError(
                "field %r has unknown normalizer %r" % (name, normalizer))
        for rule in rules:
            method = rule.get("method")
            if method not in VALID_METHODS:
                raise ValueError(
                    "field %r has unknown method %r" % (name, method))
            source = rule.get("source", "any")
            if source not in VALID_SOURCES:
                raise ValueError(
                    "field %r has unknown source %r" % (name, source))
            if method == "attr" and "attr" not in rule:
                raise ValueError("field %r attr rule needs 'attr'" % name)
            if method == "regex" and "pattern" not in rule:
                raise ValueError("field %r regex rule needs 'pattern'" % name)
