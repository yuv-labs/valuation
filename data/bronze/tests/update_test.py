"""Tests for update.py helpers."""

from data.bronze.update import _is_valid_stooq_csv


class TestIsValidStooqCsv:

  def test_valid_csv(self):
    content = (b'Date,Open,High,Low,Close,Volume\n'
               b'2026-01-02,150.0,155.0,149.0,153.0,1000000\n')
    assert _is_valid_stooq_csv(content) is True

  def test_valid_csv_windows_line_endings(self):
    content = (b'Date,Open,High,Low,Close,Volume\r\n'
               b'2026-01-02,150.0,155.0,149.0,153.0,1000000\r\n')
    assert _is_valid_stooq_csv(content) is True

  def test_html_error_page(self):
    content = b'Get your apikey:\n\n1. Open https://stooq.com'
    assert _is_valid_stooq_csv(content) is False

  def test_generic_html(self):
    content = b'<html><body>Error</body></html>'
    assert _is_valid_stooq_csv(content) is False

  def test_empty_bytes(self):
    assert _is_valid_stooq_csv(b'') is False
