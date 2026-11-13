"""Minimal HTML DOM built on html.parser (standard library only)."""

from html.parser import HTMLParser

_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class Node:
    __slots__ = ("tag", "attrs", "children", "texts", "parent")

    def __init__(self, tag, attrs, parent=None):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []
        self.texts = []
        self.parent = parent

    def text(self):
        parts = list(self.texts)
        for child in self.children:
            parts.append(child.text())
        return "".join(parts)

    def iter(self):
        yield self
        for child in self.children:
            yield from child.iter()

    def find_all(self, tag=None, class_=None, id_=None):
        matches = []
        for node in self.iter():
            if tag is not None and node.tag != tag:
                continue
            if id_ is not None and node.attrs.get("id") != id_:
                continue
            if class_ is not None and class_ not in node.attrs.get("class", "").split():
                continue
            matches.append(node)
        return matches


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document", {})
        self._stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self._stack[-1])
        self._stack[-1].children.append(node)
        if tag not in _VOID_TAGS:
            self._stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, attrs, self._stack[-1])
        self._stack[-1].children.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self._stack) - 1, 0, -1):
            if self._stack[i].tag == tag:
                del self._stack[i:]
                break

    def handle_data(self, data):
        self._stack[-1].texts.append(data)


def parse(html_text):
    builder = _TreeBuilder()
    builder.feed(html_text)
    builder.close()
    return builder.root
