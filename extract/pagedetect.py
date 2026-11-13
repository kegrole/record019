"""Heuristic page-type detection: list page vs detail page."""

PRODUCT_BLOCK_CLASSES = ("product-item", "product-card", "goods-item", "item")
DETAIL_IDS = ("product-title", "product-detail", "detail-main")
DETAIL_CLASSES = ("product-detail", "product-main", "detail-main")


def find_product_blocks(root):
    blocks = []
    for node in root.iter():
        classes = node.attrs.get("class", "").split()
        if any(c in PRODUCT_BLOCK_CLASSES for c in classes):
            blocks.append(node)
    return blocks


def detect_page_type(root):
    if len(find_product_blocks(root)) >= 2:
        return "list"
    for node in root.iter():
        if node.attrs.get("id") in DETAIL_IDS:
            return "detail"
        classes = node.attrs.get("class", "").split()
        if any(c in DETAIL_CLASSES for c in classes):
            return "detail"
    return "detail"
