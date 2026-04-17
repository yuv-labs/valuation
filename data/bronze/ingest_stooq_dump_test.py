from data.bronze.ingest_stooq_dump import _convert_dump_to_csv

_HEADER = (b'<TICKER>,<PER>,<DATE>,<TIME>,'
           b'<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>,<OPENINT>\n')


class TestConvertDumpToCsv:

  def test_renames_columns_and_formats_date(self):
    raw = _HEADER + (
        b'AAPL.US,D,20250115,000000,'
        b'100.0,105.0,99.0,103.0,50000,0\n')
    result = _convert_dump_to_csv(raw).decode('utf-8')
    lines = result.strip().split('\n')

    assert lines[0] == 'Date,Open,High,Low,Close,Volume'
    assert lines[1].startswith('2025-01-15,')
    assert '50000' in lines[1]

  def test_drops_extra_columns(self):
    raw = _HEADER + (
        b'TEST.US,D,20240301,000000,'
        b'10,12,9,11,1000,0\n')
    result = _convert_dump_to_csv(raw).decode('utf-8')
    header = result.split('\n')[0]

    assert 'TICKER' not in header
    assert 'PER' not in header
    assert 'OPENINT' not in header

  def test_multiple_rows(self):
    raw = _HEADER + (
        b'X.US,D,20250101,000000,1,2,0.5,1.5,100,0\n'
        b'X.US,D,20250102,000000,1.5,3,1,2.5,200,0\n')
    result = _convert_dump_to_csv(raw).decode('utf-8')
    lines = [l for l in result.strip().split('\n') if l]

    assert len(lines) == 3
    assert lines[1].startswith('2025-01-01,')
    assert lines[2].startswith('2025-01-02,')
