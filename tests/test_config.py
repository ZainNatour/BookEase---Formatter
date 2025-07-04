import importlib
import io
from pathlib import Path

import yaml

import src.config as config


def test_defaults_created(monkeypatch):
    fake_file = io.StringIO()

    monkeypatch.setattr(config, 'CONFIG_PATH', Path('dummy.yml'))
    monkeypatch.setattr(Path, 'exists', lambda self: False)
    monkeypatch.setattr(Path, 'open', lambda self, mode='r', encoding=None: fake_file)
    monkeypatch.setattr(yaml, 'safe_dump', lambda data, stream: None)
    monkeypatch.setattr(yaml, 'safe_load', lambda *a, **k: {})

    cfg = importlib.reload(config)
    data = cfg.load_config()

    assert data['copy_icon_templates'] == cfg.DEFAULT_CONFIG['copy_icon_templates']
    assert data['chunk_size'] == cfg.DEFAULT_CONFIG['chunk_size']
    assert data['chunk_overlap'] == cfg.DEFAULT_CONFIG['chunk_overlap']
    assert data['typing_indicator_bbox'] == cfg.DEFAULT_CONFIG['typing_indicator_bbox']


def test_partial_config(monkeypatch):
    fake_file = io.StringIO()

    monkeypatch.setattr(config, 'CONFIG_PATH', Path('dummy.yml'))
    monkeypatch.setattr(Path, 'exists', lambda self: True)
    monkeypatch.setattr(Path, 'open', lambda self, mode='r', encoding=None: fake_file)
    monkeypatch.setattr(yaml, 'safe_load', lambda *a, **k: {'chunk_size': 42})
    monkeypatch.setattr(yaml, 'safe_dump', lambda data, stream: None)

    cfg = importlib.reload(config)
    data = cfg.load_config()

    assert data['chunk_size'] == 42
    assert data['chunk_overlap'] == cfg.DEFAULT_CONFIG['chunk_overlap']
    assert data['copy_icon_templates'] == cfg.DEFAULT_CONFIG['copy_icon_templates']
    assert data['typing_indicator_bbox'] == cfg.DEFAULT_CONFIG['typing_indicator_bbox']
