"""Offline page provenance and fallback failure tests."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pdf_evidence as evidence


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pdf = Path(self.temp.name) / "paper.pdf"
        self.pdf.write_bytes(b"%PDF-1.4 fixture")
        self.raw_pages = ["A readable page describing a reusable benchmark in English.\n", "Another readable page with complete text and no table structure.\n"]
        self.items = [{"page_idx": 0, "type": "text", "text": "First physical page"},
                      {"page_idx": 1, "type": "table", "table_body": '<table><tr><th colspan="2">Count</th></tr><tr><td>A</td><td>12</td></tr></table>'}]
        self.indices = [0, 1]
        self.fail_mineru = False
        self.fail_poppler = False

    def runner(self, command, **kwargs):
        if command[0] == "pdfinfo":
            return subprocess.CompletedProcess(command, 0, stdout="Pages: 2\n")
        if command[0] == "pdftotext":
            if "-v" in command:
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="pdftotext version test\n")
            if self.fail_poppler:
                raise subprocess.CalledProcessError(1, command)
            self.pdf.with_suffix(".txt").write_text("\f".join(self.raw_pages) + "\f")
        elif "--version" in command:
            return subprocess.CompletedProcess(command, 0, stdout="mineru, version 2.7.6")
        else:
            if self.fail_mineru:
                raise subprocess.TimeoutExpired(command, 600)
            folder = Path(command[command.index("-o") + 1]) / "paper" / "auto"
            folder.mkdir(parents=True)
            (folder / "paper_content_list.json").write_text(json.dumps(self.items))
            (folder / "paper_middle.json").write_text(json.dumps({"pdf_info": [{"page_idx": i} for i in self.indices]}))
        return subprocess.CompletedProcess(command, 0)

    def test_plain_text_avoids_mineru_and_keeps_original_pdf(self):
        before = self.pdf.read_bytes()
        with patch.object(evidence.subprocess, "run", side_effect=self.runner) as run:
            result = evidence.extract_pdf(self.pdf)
        self.assertEqual(result["extraction"]["backend"], "poppler")
        self.assertFalse(any("mineru" in str(call.args[0][0]) for call in run.call_args_list))
        self.assertEqual(self.pdf.read_bytes(), before)
        saved = json.loads(self.pdf.with_suffix(".pages.json").read_text())
        self.assertEqual([p["page"] for p in saved["pages"]], [1, 2])

    def test_oversized_original_text_fails_before_mineru_runs(self):
        self.raw_pages[1] += "Table 2: Results\nA  12  30\n" + "x" * 500
        with patch.object(evidence, "MAX_CHARS", 400), patch.object(evidence.subprocess, "run", side_effect=self.runner) as run:
            with self.assertRaisesRegex(ValueError, "context limit"):
                evidence.extract_pdf(self.pdf)
        self.assertFalse(any(call.args[0][0] == "mineru" for call in run.call_args_list))

    def test_unparsed_table_is_marked_instead_of_discarding_the_paper(self):
        self.raw_pages[1] += "Table 2: Results\nA  12  30\n"
        self.items[1]["table_body"] = ""
        with patch.object(evidence.subprocess, "run", side_effect=self.runner):
            result = evidence.extract_pdf(self.pdf)
        self.assertEqual(result["extraction"]["tables_missing"], 1)
        self.assertIn("could not parse this table", result["pages"][1])
        self.assertIn("Original PDF text (Poppler)", result["pages"][1])

    def test_duplicate_original_text_is_dropped_on_plain_pages_when_over_the_limit(self):
        self.raw_pages[0] += "plain prose " * 20
        self.raw_pages[1] += "Table 2: Results\nA  12  30\n"
        with patch.object(evidence.subprocess, "run", side_effect=self.runner):
            full = sum(map(len, evidence.extract_pdf(self.pdf)["pages"]))
        with patch.object(evidence, "MAX_CHARS", full - 1), patch.object(evidence.subprocess, "run", side_effect=self.runner):
            result = evidence.extract_pdf(self.pdf)
        self.assertTrue(result["extraction"]["original_text_reduced"])
        self.assertNotIn("Original PDF text (Poppler)", result["pages"][0])
        self.assertIn("Original PDF text (Poppler)", result["pages"][1])

    def test_table_fallback_keeps_html_and_original_text_on_same_page(self):
        self.raw_pages[1] += "Table 2: Results\nA  12  30\n"
        with patch.object(evidence.subprocess, "run", side_effect=self.runner):
            result = evidence.extract_pdf(self.pdf)
        self.assertEqual(result["extraction"]["fallback_reasons"], ["table_layout"])
        self.assertIn('colspan="2"', result["pages"][1])
        self.assertIn("Table 2: Results", result["pages"][1])
        self.assertNotIn("<table>", result["pages"][0])

    def test_scanned_or_failed_poppler_uses_mineru(self):
        for fail in (False, True):
            self.fail_poppler = fail
            self.raw_pages = ["", ""]
            with patch.object(evidence.subprocess, "run", side_effect=self.runner):
                result = evidence.extract_pdf(self.pdf)
            self.assertEqual(result["extraction"]["backend"], "mineru")

    def test_blank_physical_page_does_not_shift_indices(self):
        pages = evidence.parse_mineru([{"page_idx": 2, "type": "text", "text": "third"}], 3)
        self.assertEqual(pages[:2], [[], []])
        self.assertEqual(pages[2][0]["text"], "third")

    def test_missing_table_structure_is_marked_not_rejected(self):
        pages = evidence.parse_mineru([{"page_idx": 0, "type": "table"}], 1)
        self.assertTrue(pages[0][0]["table_missing"])
        self.assertIn("could not parse", pages[0][0]["table_body"])

    def test_invalid_indices_are_rejected(self):
        for index in (-1, 2, True, "1", None):
            with self.assertRaisesRegex(ValueError, "page index"):
                evidence.parse_mineru([{"page_idx": index, "type": "text"}], 2)

    def test_mineru_failure_never_returns_poppler_table_as_success(self):
        self.fail_mineru = True
        with patch.object(evidence.subprocess, "run", side_effect=self.runner):
            with self.assertRaises(subprocess.TimeoutExpired):
                evidence.extract_pdf(self.pdf, force_mineru=True)
        self.assertFalse(self.pdf.with_suffix(".pages.json").exists())

    def test_incomplete_mineru_pages_rejected(self):
        self.indices = [0]
        with patch.object(evidence.subprocess, "run", side_effect=self.runner):
            with self.assertRaisesRegex(ValueError, "omitted"):
                evidence.extract_pdf(self.pdf, force_mineru=True)

    def test_combined_evidence_limit_is_enforced(self):
        self.raw_pages[0] *= 4000
        with patch.object(evidence.subprocess, "run", side_effect=self.runner):
            with self.assertRaisesRegex(ValueError, "context limit"):
                evidence.extract_pdf(self.pdf)


if __name__ == "__main__":
    unittest.main()
