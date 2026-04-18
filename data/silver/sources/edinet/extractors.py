"""EDINET CSV fact extractor."""

import csv
import io
import logging
from pathlib import Path
import zipfile

import pandas as pd

from data.silver.config.metric_specs_jp import METRIC_SPECS_JP

logger = logging.getLogger(__name__)

_SEGMENT_KEYWORDS = (
    'ReportableSegmentMember',
    'EliminationMember',
    'OtherReportableSegmentsMember',
    'NonConsolidatedMember',
)


class EDINETExtractor:
  """Extracts financial facts from EDINET CSV zip packages (type=5)."""

  def __init__(self) -> None:
    self._tag_to_metric = self._build_tag_index()

  @staticmethod
  def _build_tag_index() -> dict[str, tuple[str, str]]:
    """Build {local_tag: (metric_name, namespace)} index."""
    index: dict[str, tuple[str, str]] = {}
    for metric, spec in METRIC_SPECS_JP.items():
      for ns, tags in spec['taxonomies'].items():
        for tag in tags:
          if tag not in index:
            index[tag] = (metric, ns)
    return index

  def extract_facts(self, zip_path: Path) -> pd.DataFrame:
    """Extract facts from an EDINET CSV zip (type=5)."""
    csv_content = self._read_csv_from_zip(zip_path)
    if csv_content is None:
      return pd.DataFrame()

    facts = self._parse_csv(csv_content)
    if not facts:
      return pd.DataFrame()

    return pd.DataFrame(facts)

  @staticmethod
  def _read_csv_from_zip(zip_path: Path) -> str | None:
    try:
      with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
          if 'jpcrp' in name and name.endswith('.csv'):
            raw = zf.read(name)
            for enc in ('utf-16', 'utf-16-le', 'cp932', 'utf-8-sig'):
              try:
                return raw.decode(enc)
              except (UnicodeDecodeError, ValueError):
                continue
    except (zipfile.BadZipFile, OSError) as exc:
      logger.warning('Failed to read CSV zip %s: %s',
                     zip_path, exc)
    return None

  def _parse_csv(self, content: str) -> list[dict]:
    """Parse EDINET CSV and match against metric specs."""
    reader = csv.reader(io.StringIO(content), delimiter='\t')
    header = next(reader, None)
    if header is None:
      return []

    facts: list[dict] = []
    seen: set[str] = set()

    for row in reader:
      if len(row) < 9:
        continue

      elem_id = row[0].strip('"')
      context_id = row[2].strip('"')
      value_str = row[8].strip('"')

      if not elem_id or not value_str:
        continue

      if any(kw in context_id for kw in _SEGMENT_KEYWORDS):
        continue

      if ':' not in elem_id:
        continue
      local_tag = elem_id.split(':')[1]

      lookup = self._tag_to_metric.get(local_tag)
      if lookup is None:
        continue

      metric_name, _ = lookup

      try:
        val = float(value_str)
      except ValueError:
        continue

      dedup_key = f'{metric_name}:{context_id}'
      if dedup_key in seen:
        continue
      seen.add(dedup_key)

      period_type = ('instant' if 'Instant' in context_id
                     else 'duration')

      facts.append({
          'edinet_code': None,
          'metric': metric_name,
          'tag': local_tag,
          'val': val,
          'end': None,
          'context_ref': context_id,
          'period_type': period_type,
      })

    return facts
