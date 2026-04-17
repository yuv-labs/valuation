"""Tests for BronzeCache."""

import os
import time

from data.bronze.cache import BronzeCache


def _set_mtime_old(path):
  old = time.time() - 400 * 86400
  os.utime(path, (old, old))


class TestBronzeCacheGetIfFresh:

  def test_returns_none_for_missing_key(self, tmp_path):
    cache = BronzeCache(cache_dir=tmp_path)

    result = cache.get_if_fresh('nonexistent.json', max_age_days=7)
    assert result is None

  def test_returns_bytes_when_fresh(self, tmp_path):
    cache = BronzeCache(cache_dir=tmp_path)
    cache.put('sec/test.json', b'{"ok": true}')

    result = cache.get_if_fresh('sec/test.json', max_age_days=7)
    assert result == b'{"ok": true}'

  def test_returns_none_when_expired(self, tmp_path):
    cache = BronzeCache(cache_dir=tmp_path)
    cache.put('sec/test.json', b'old')
    _set_mtime_old(tmp_path / 'sec' / 'test.json')

    result = cache.get_if_fresh('sec/test.json', max_age_days=7)
    assert result is None

  def test_none_max_age_returns_regardless_of_age(self, tmp_path):
    cache = BronzeCache(cache_dir=tmp_path)
    cache.put('dart/old.json', b'immutable')
    _set_mtime_old(tmp_path / 'dart' / 'old.json')

    result = cache.get_if_fresh('dart/old.json', max_age_days=None)
    assert result == b'immutable'


class TestBronzeCachePut:

  def test_creates_parent_directories(self, tmp_path):
    cache = BronzeCache(cache_dir=tmp_path)
    cache.put('deep/nested/dir/file.json', b'data')

    path = tmp_path / 'deep' / 'nested' / 'dir' / 'file.json'
    assert path.read_bytes() == b'data'

  def test_overwrites_existing_file(self, tmp_path):
    cache = BronzeCache(cache_dir=tmp_path)
    cache.put('test.json', b'v1')
    cache.put('test.json', b'v2')

    assert (tmp_path / 'test.json').read_bytes() == b'v2'


class TestBronzeCacheResolve:

  def test_copies_to_local_path_on_hit(self, tmp_path):
    cache = BronzeCache(cache_dir=tmp_path / 'cache')
    cache.put('sec/data.json', b'cached_content')

    local_path = tmp_path / 'out' / 'sec' / 'data.json'
    resolved = cache.resolve(
        'sec/data.json', local_path, max_age_days=None)

    assert resolved is True
    assert local_path.read_bytes() == b'cached_content'

  def test_returns_false_on_miss(self, tmp_path):
    cache = BronzeCache(cache_dir=tmp_path / 'cache')

    local_path = tmp_path / 'out' / 'missing.json'
    resolved = cache.resolve(
        'missing.json', local_path, max_age_days=7)

    assert resolved is False
    assert not local_path.exists()

  def test_returns_false_when_expired(self, tmp_path):
    cache = BronzeCache(cache_dir=tmp_path / 'cache')
    cache.put('stale.json', b'old_data')
    _set_mtime_old(tmp_path / 'cache' / 'stale.json')

    local_path = tmp_path / 'out' / 'stale.json'
    resolved = cache.resolve(
        'stale.json', local_path, max_age_days=1)

    assert resolved is False
    assert not local_path.exists()


class TestBronzeCacheDefaultDir:

  def test_default_cache_dir_under_home(self):
    cache = BronzeCache()
    assert '.cache' in str(cache.cache_dir)
    assert 'valuation' in str(cache.cache_dir)

  def test_respects_xdg_cache_home(self, tmp_path, monkeypatch):
    monkeypatch.setenv(
        'XDG_CACHE_HOME', str(tmp_path / 'xdg'))
    cache = BronzeCache()

    expected = tmp_path / 'xdg' / 'valuation' / 'bronze'
    assert cache.cache_dir == expected
