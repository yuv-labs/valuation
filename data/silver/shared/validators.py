"""
Shared validators.
"""
import logging

import pandas as pd

from data.silver.core.validator import ValidationResult
from data.silver.core.validator import Validator

logger = logging.getLogger(__name__)


class BasicValidator(Validator):
  """Basic validation checks."""

  def validate(self, name: str, df: pd.DataFrame) -> ValidationResult:
    """Run basic validation checks."""
    errors: list[str] = []
    warnings: list[str] = []

    if df.empty:
      warnings.append(f'{name}: DataFrame is empty')

    if 'end' in df.columns and 'filed' in df.columns:
      bad = df['filed'] < df['end']
      if bad.any():
        n = int(bad.sum())
        warnings.append(f'{name}: {n} rows have filed < end')

    for warn in warnings:
      logger.warning(warn)

    return ValidationResult(is_valid=len(errors) == 0,
                            errors=errors,
                            warnings=warnings)
