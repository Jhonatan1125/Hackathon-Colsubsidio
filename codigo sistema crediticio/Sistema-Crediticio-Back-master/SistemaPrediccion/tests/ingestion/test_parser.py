import pytest

from credit_engine.ingestion.parser import parse_csv, parse_txt


class TestParseCsv:
    def test_parses_single_cell_per_row(self):
        content = "12345678\n87654321\n55555"
        result = parse_csv(content)
        assert result == ["12345678", "87654321", "55555"]

    def test_parses_multiple_cells_per_row(self):
        content = "12345678,87654321\n55555,44444"
        result = parse_csv(content)
        assert result == ["12345678", "87654321", "55555", "44444"]

    def test_skips_empty_cells(self):
        content = "12345678,\n,87654321"
        result = parse_csv(content)
        assert result == ["12345678", "87654321"]

    def test_handles_bytes_input(self):
        content = b"12345678\n87654321"
        result = parse_csv(content)
        assert result == ["12345678", "87654321"]

    def test_strips_utf8_bom(self):
        content = b"\xef\xbb\xbf12345678\n87654321"
        result = parse_csv(content)
        assert result == ["12345678", "87654321"]

    def test_handles_empty_content(self):
        assert parse_csv("") == []

    def test_strips_whitespace_from_cells(self):
        content = "  12345678  ,  87654321  "
        result = parse_csv(content)
        assert result == ["12345678", "87654321"]

    def test_handles_multiple_empty_lines(self):
        content = "\n\n12345\n\n67890\n"
        result = parse_csv(content)
        assert result == ["12345", "67890"]


class TestParseTxt:
    def test_parses_one_id_per_line(self):
        content = "12345678\n87654321\n55555"
        result = parse_txt(content)
        assert result == ["12345678", "87654321", "55555"]

    def test_skips_empty_lines(self):
        content = "12345678\n\n87654321\n\n"
        result = parse_txt(content)
        assert result == ["12345678", "87654321"]

    def test_strips_whitespace(self):
        content = "  12345678  \n  87654321  "
        result = parse_txt(content)
        assert result == ["12345678", "87654321"]

    def test_handles_bytes_input(self):
        content = b"12345678\n87654321"
        result = parse_txt(content)
        assert result == ["12345678", "87654321"]

    def test_strips_utf8_bom(self):
        content = b"\xef\xbb\xbf12345678\n87654321"
        result = parse_txt(content)
        assert result == ["12345678", "87654321"]

    def test_handles_empty_content(self):
        assert parse_txt("") == []

    def test_handles_windows_line_endings(self):
        content = "12345678\r\n87654321\r\n55555"
        result = parse_txt(content)
        assert result == ["12345678", "87654321", "55555"]
