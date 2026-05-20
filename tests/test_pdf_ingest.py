import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
INGEST_PATH = ROOT / "tools" / "source-ingest" / "pdf" / "ingest_pdf.py"


def load_ingest_module():
    spec = importlib.util.spec_from_file_location("ingest_pdf", INGEST_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ingest_pdf = load_ingest_module()


class FakeImage:
    def save(self, path, format=None):
        Path(path).write_bytes(b"png")


class FakePageImage:
    pil_image = FakeImage()


class FakePage:
    def __init__(self, page_no):
        self.page_no = page_no
        self.image = FakePageImage()


class FakeProv:
    def __init__(self, page_no):
        self.page_no = page_no


class SectionHeaderItem:
    text = "Intro"
    level = 1
    prov = [FakeProv(1)]


class FakePicture:
    label = "picture"
    caption = "Diagram"
    prov = [FakeProv(1)]

    def get_image(self, doc):
        return FakeImage()


class FakeFrame:
    def to_csv(self, path, index=False):
        Path(path).write_text("name,value\nalpha,1\n", encoding="utf-8")


class FakeTable:
    prov = [FakeProv(1)]

    def export_to_dataframe(self, doc):
        return FakeFrame()

    def export_to_html(self, doc):
        return "<table><tr><td>alpha</td></tr></table>"

    def get_image(self, doc):
        return FakeImage()


class FakeDocument:
    def __init__(self, page_numbers=(1, 2)):
        self.page_numbers = tuple(sorted(page_numbers))
        self.pages = {page_number: FakePage(page_number) for page_number in self.page_numbers}
        self.tables = [FakeTable()] if 1 in self.page_numbers else []

    def filter(self, page_nrs=None):
        return FakeDocument(page_nrs or self.page_numbers)

    def export_to_markdown(self, page_no=None, **kwargs):
        if page_no is not None:
            return f"# Page {page_no}\n\nContent from page {page_no}"
        return "\n\n".join(
            f"# Page {page_number}\n\nContent from page {page_number}"
            for page_number in self.page_numbers
        )

    def export_to_dict(self):
        return {
            "pages": [
                {"page_no": page_number, "items": [{"label": "picture"}]}
                for page_number in self.page_numbers
            ]
        }

    def iterate_items(self, *args, **kwargs):
        yield SectionHeaderItem(), 0
        if kwargs.get("traverse_pictures"):
            yield FakePicture(), 0


class FakeResult:
    status = "SUCCESS"
    errors = []
    document = FakeDocument()


class FakeInputFormat:
    PDF = "pdf"


class FakePdfPipelineOptions:
    pass


class FakePdfFormatOption:
    def __init__(self, pipeline_options):
        self.pipeline_options = pipeline_options


class FakeConverter:
    last_page_range = None
    last_pipeline_options = None

    def __init__(self, format_options):
        option = next(iter(format_options.values()))
        FakeConverter.last_pipeline_options = option.pipeline_options

    def convert(self, source, raises_on_error=True, page_range=None):
        FakeConverter.last_page_range = page_range
        return FakeResult()


class FakeChunk:
    text = "Chunk text"
    meta = {"doc_items": [{"prov": [{"page_no": 1}]}]}


class FakeHybridChunker:
    def chunk(self, dl_doc):
        return [FakeChunk()]

    def contextualize(self, chunk):
        return chunk.text


def fake_runtime():
    return ingest_pdf.DoclingRuntime(
        DocumentConverter=FakeConverter,
        PdfFormatOption=FakePdfFormatOption,
        PdfPipelineOptions=FakePdfPipelineOptions,
        InputFormat=FakeInputFormat,
        HybridChunker=FakeHybridChunker,
        PictureItem=FakePicture,
        TableItem=FakeTable,
    )


class PdfIngestTests(unittest.TestCase):
    def test_page_range_selection_validates_and_sorts_ranges(self):
        self.assertEqual([1, 2, 3, 5], ingest_pdf.selected_pages(5, "3-1,5"))
        with self.assertRaises(SystemExit):
            ingest_pdf.selected_pages(2, "1,4")

    def test_malformed_source_id_is_rejected(self):
        with self.assertRaises(SystemExit):
            ingest_pdf.require_source_id("Bad_ID")

    def test_overwrite_is_required_for_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "input.pdf"
            pdf.write_bytes(b"%PDF-1.4\n")
            output_root = root / "derived"
            (output_root / "sample-source").mkdir(parents=True)
            args = ingest_pdf.parse_args(
                [
                    "--pdf",
                    str(pdf),
                    "--source-id",
                    "sample-source",
                    "--source-tier",
                    "reference",
                    "--title",
                    "Sample Source",
                    "--output-root",
                    str(output_root),
                ]
            )

            with self.assertRaises(SystemExit):
                ingest_pdf.ingest_pdf(args, runtime=fake_runtime(), page_count_reader=lambda path: 2)

    def test_mocked_docling_ingest_preserves_output_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "input.pdf"
            pdf.write_bytes(b"%PDF-1.4\n")
            output_root = root / "derived"
            args = ingest_pdf.parse_args(
                [
                    "--pdf",
                    str(pdf),
                    "--source-id",
                    "sample-source",
                    "--source-tier",
                    "primary",
                    "--title",
                    "Sample Source",
                    "--output-root",
                    str(output_root),
                    "--page-range",
                    "1-2",
                    "--overwrite",
                ]
            )

            output_dir = ingest_pdf.ingest_pdf(
                args,
                runtime=fake_runtime(),
                page_count_reader=lambda path: 2,
            )

            self.assertEqual((1, 2), FakeConverter.last_page_range)
            self.assertTrue(FakeConverter.last_pipeline_options.do_ocr)
            self.assertTrue(FakeConverter.last_pipeline_options.generate_page_images)
            self.assertTrue(FakeConverter.last_pipeline_options.generate_picture_images)
            self.assertEqual(2.0, FakeConverter.last_pipeline_options.images_scale)
            self.assertEqual(120.0, FakeConverter.last_pipeline_options.document_timeout)

            manifest = yaml.safe_load((output_dir / "manifest.yaml").read_text(encoding="utf-8"))
            self.assertEqual("docling", manifest["parser_profile"])
            self.assertEqual("primary", manifest["source_tier"])
            self.assertEqual(2, manifest["pdf"]["selected_page_count"])
            self.assertTrue(manifest["conversion"]["settings"]["ocr"])

            page_text = (output_dir / "pages" / "page-0001.md").read_text(encoding="utf-8")
            self.assertIn("source_tier: primary", page_text)
            self.assertIn("Content from page 1", page_text)

            page_json = json.loads((output_dir / "pages" / "page-0001.json").read_text(encoding="utf-8"))
            self.assertEqual("sample-source", page_json["source_id"])
            self.assertEqual(1, page_json["page_number"])

            chunks = [
                json.loads(line)
                for line in (output_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual("sample-source", chunks[0]["source_id"])
            self.assertEqual("Chunk text", chunks[0]["text"])

            self.assertTrue((output_dir / "figures" / "figure-0001.png").exists())
            self.assertTrue((output_dir / "tables" / "table-0001.csv").exists())
            self.assertTrue((output_dir / "tables" / "table-0001.html").exists())
            self.assertTrue((output_dir / "tables" / "table-0001.png").exists())
            self.assertTrue((output_dir / "pages" / "previews" / "page-0001.png").exists())
            self.assertTrue((output_dir / "source-summary.md").exists())
            self.assertTrue((output_dir / "source-maps" / "outline.md").exists())


if __name__ == "__main__":
    unittest.main()
