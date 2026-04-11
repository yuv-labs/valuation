"""Screening domain types."""

from enum import Enum


class Track(Enum):
  MOAT = 'moat'
  OPPORTUNITY = 'opportunity'
  FULL = 'full'
