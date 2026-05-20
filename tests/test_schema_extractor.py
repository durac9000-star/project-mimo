"""Schema extractor unit tests — no MiMo calls, fully deterministic."""
from __future__ import annotations

import textwrap

from sentinel.agents import schema_extractor


SPEC = textwrap.dedent(
    """\
    openapi: 3.0.3
    info:
      title: demo
      version: 0.1.0
    paths:
      /users/{id}:
        get:
          parameters:
            - name: id
              in: path
              required: true
              schema:
                type: integer
      /search:
        get:
          parameters:
            - name: q
              in: query
              schema:
                type: string
    """
)


def test_load_spec_yaml_roundtrip():
    spec = schema_extractor.load_spec(SPEC)
    assert "paths" in spec
    assert "/search" in spec["paths"]


def test_extract_endpoints_finds_all_paths():
    spec = schema_extractor.load_spec(SPEC)
    eps = schema_extractor.extract_endpoints(spec)
    paths = sorted(e.path for e in eps)
    assert paths == ["/search", "/users/{id}"]


def test_extract_endpoints_keeps_parameters():
    spec = schema_extractor.load_spec(SPEC)
    eps = {e.path: e for e in schema_extractor.extract_endpoints(spec)}
    assert any(p["name"] == "id" for p in eps["/users/{id}"].parameters)
    assert any(p["name"] == "q" for p in eps["/search"].parameters)
