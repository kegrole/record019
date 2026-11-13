import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from extract import cli
from extract.dom import parse
from extract.normalize import normalize_price, normalize_spec, normalize_text
from extract.pagedetect import detect_page_type

DEMO_PAGES = ROOT / "demo" / "pages"
DEMO_CONFIG = ROOT / "demo" / "schema.json"

EXPECTED_FIELDS = {
    "name": "无线蓝牙耳机 X1",
    "price": 129900,
    "sku": "A100",
    "image_url": "https://example.com/img/a.png",
}


def run_demo(out_path):
    return cli.run(str(DEMO_CONFIG), str(DEMO_PAGES), str(out_path))


class ExtractionTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.out_path = Path(self._tmp.name) / "records.jsonl"
        self.stats = run_demo(self.out_path)
        self.lines = self.out_path.read_text(encoding="utf-8").splitlines()
        self.records = [json.loads(line) for line in self.lines]

    def record_for(self, page_name):
        for record in self.records:
            if page_name in record["source_url"]:
                return record
        self.fail("no record for page %r" % page_name)

    def test_1_six_pages_produce_six_records(self):
        self.assertEqual(self.stats["pages"], 6)
        self.assertEqual(self.stats["records"], 6)
        self.assertEqual(len(self.records), 6)

    def test_2_four_complete_records_match_expected_exactly(self):
        complete = [r for r in self.records if r["status"] == "ok"]
        self.assertEqual(len(complete), 4)
        for record in complete:
            self.assertEqual(record["fields"], EXPECTED_FIELDS)
            self.assertEqual(record["missing"], [])

    def test_3_price_normalized_to_integer_cents(self):
        self.assertEqual(normalize_price("1,299.00 元"), 129900)
        self.assertEqual(normalize_price("1299元"), 129900)
        self.assertEqual(normalize_price("¥1,299"), 129900)
        self.assertEqual(self.record_for("list_a")["fields"]["price"], 129900)
        self.assertEqual(self.record_for("list_b")["fields"]["price"], 129900)

    def test_4_missing_fields_are_exactly_the_string_missing(self):
        lazy = self.record_for("lazy_image")
        self.assertEqual(lazy["fields"]["image_url"], "missing")
        self.assertNotEqual(lazy["fields"]["image_url"], "")
        self.assertIsNotNone(lazy["fields"]["image_url"])
        self.assertEqual(lazy["status"], "partial")
        self.assertEqual(lazy["missing"], ["image_url"])

        no_sku = self.record_for("no_sku")
        self.assertEqual(no_sku["fields"]["sku"], "missing")
        self.assertNotEqual(no_sku["fields"]["sku"], "A100")
        self.assertEqual(no_sku["status"], "partial")
        self.assertEqual(no_sku["missing"], ["sku"])

        self.assertEqual(self.stats["missing_fields"], 2)

    def test_5_image_url_is_absolute(self):
        for record in self.records:
            image_url = record["fields"]["image_url"]
            if image_url == "missing":
                continue
            self.assertEqual(image_url, "https://example.com/img/a.png")
            self.assertTrue(image_url.startswith("https://"))

    def test_6_jsonl_format_and_deterministic_output(self):
        self.assertEqual(len(self.lines), 6)
        for line in self.lines:
            obj = json.loads(line)
            for key in ("record_id", "source_url", "status", "fields"):
                self.assertIn(key, obj)
        second_path = Path(self._tmp.name) / "records2.jsonl"
        run_demo(second_path)
        self.assertEqual(self.out_path.read_bytes(), second_path.read_bytes())


class PageDetectionTestCase(unittest.TestCase):
    def test_list_and_detail_detection(self):
        list_html = (DEMO_PAGES / "list_a.html").read_text(encoding="utf-8")
        detail_html = (DEMO_PAGES / "detail_a.html").read_text(encoding="utf-8")
        self.assertEqual(detect_page_type(parse(list_html)), "list")
        self.assertEqual(detect_page_type(parse(detail_html)), "detail")


class NormalizeTestCase(unittest.TestCase):
    def test_text_and_spec_normalization(self):
        self.assertEqual(normalize_text("无线蓝牙耳机　Ｘ１"), "无线蓝牙耳机 X1")
        self.assertEqual(normalize_spec("颜色： 黑色　ＸＬ"), "颜色:黑色XL")


if __name__ == "__main__":
    unittest.main()
