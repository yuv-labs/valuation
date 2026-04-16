"""EDINET XBRL fact extractor."""

import io
import logging
from pathlib import Path
from xml.etree import ElementTree
import zipfile

import pandas as pd

from data.silver.config.metric_specs_jp import METRIC_SPECS_JP

logger = logging.getLogger(__name__)

_NS = {
    'xbrli': 'http://www.xbrl.org/2003/instance',
}


class EDINETExtractor:
  """Extracts financial facts from EDINET XBRL zip packages."""

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

  def extract_facts(self, xbrl_zip_path: Path) -> pd.DataFrame:
    """Extract facts from an EDINET XBRL zip."""
    xbrl_content = self._read_xbrl_from_zip(xbrl_zip_path)
    if xbrl_content is None:
      return pd.DataFrame()

    tree = ElementTree.parse(io.BytesIO(xbrl_content))
    root = tree.getroot()

    contexts = self._parse_contexts(root)
    facts = self._extract_facts_from_tree(root, contexts)

    if not facts:
      return pd.DataFrame()

    return pd.DataFrame(facts)

  @staticmethod
  def _read_xbrl_from_zip(zip_path: Path) -> bytes | None:
    try:
      with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
          if name.endswith('.xbrl') and 'PublicDoc' in name:
            return zf.read(name)
        for name in zf.namelist():
          if name.endswith('.xbrl'):
            return zf.read(name)
    except (zipfile.BadZipFile, OSError) as exc:
      logger.warning('Failed to read XBRL zip %s: %s',
                     zip_path, exc)
    return None

  @staticmethod
  def _parse_contexts(
      root: ElementTree.Element,
  ) -> dict[str, dict]:
    """Parse xbrli:context elements to get period info."""
    contexts: dict[str, dict] = {}

    for ctx in root.findall('xbrli:context', _NS):
      ctx_id = ctx.get('id', '')
      period = ctx.find('xbrli:period', _NS)
      if period is None:
        continue

      entity = ctx.find('xbrli:entity', _NS)
      identifier = None
      if entity is not None:
        id_el = entity.find('xbrli:identifier', _NS)
        if id_el is not None and id_el.text:
          identifier = id_el.text.strip()

      instant = period.find('xbrli:instant', _NS)
      end_date_el = period.find('xbrli:endDate', _NS)

      if instant is not None and instant.text:
        contexts[ctx_id] = {
            'end': instant.text.strip(),
            'period_type': 'instant',
            'edinet_code': identifier,
        }
      elif end_date_el is not None and end_date_el.text:
        start_el = period.find('xbrli:startDate', _NS)
        start = start_el.text.strip() if (
            start_el is not None and start_el.text) else None
        contexts[ctx_id] = {
            'end': end_date_el.text.strip(),
            'start': start,
            'period_type': 'duration',
            'edinet_code': identifier,
        }

    return contexts

  def _extract_facts_from_tree(
      self,
      root: ElementTree.Element,
      contexts: dict[str, dict],
  ) -> list[dict]:
    """Walk all elements and match against metric specs."""
    facts: list[dict] = []
    seen: set[str] = set()

    for elem in root.iter():
      tag = elem.tag
      if '}' in tag:
        local_name = tag.split('}', 1)[1]
      else:
        local_name = tag

      lookup = self._tag_to_metric.get(local_name)
      if lookup is None:
        continue

      metric_name, _ = lookup
      text = elem.text
      if text is None:
        continue

      text = text.strip()
      if not text:
        continue

      ctx_ref = elem.get('contextRef', '')

      if _is_segment_or_individual_context(ctx_ref):
        continue

      ctx = contexts.get(ctx_ref, {})
      end_date = ctx.get('end')
      edinet_code = ctx.get('edinet_code')

      dedup_key = f'{metric_name}:{ctx_ref}'
      if dedup_key in seen:
        continue
      seen.add(dedup_key)

      try:
        val = float(text)
      except ValueError:
        continue

      facts.append({
          'edinet_code': edinet_code,
          'metric': metric_name,
          'tag': local_name,
          'val': val,
          'end': end_date,
          'context_ref': ctx_ref,
          'period_type': ctx.get('period_type'),
      })

    return facts


_SEGMENT_KEYWORDS = (
    'ReportableSegmentMember',
    'EliminationMember',
    'OtherReportableSegmentsMember',
    'NonConsolidatedMember',
)


def _is_segment_or_individual_context(ctx_ref: str) -> bool:
  """Exclude segment-level and individual (non-consolidated) contexts."""
  return any(kw in ctx_ref for kw in _SEGMENT_KEYWORDS)
