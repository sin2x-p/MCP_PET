# AGENTS.md

## 工作原则

- **先分析，后行动**：拿到问题先读代码、理解现状，再给出方案。严禁未经确认私自改动文件。

## Overview

Single-file Python MCP server (`run.py`) wrapping an OCR/document recognition API. Uses [FastMCP](https://github.com/jlowin/fastmcp) framework.

## Run

```bash
python run.py
```

Starts on `0.0.0.0:8000`, path `/mcp`, transport `streamable-http`.

## Dependencies

- `fastmcp`
- `httpx`

No `requirements.txt` or `pyproject.toml` exists. Install manually.

## Key conventions

- All tool functions are async, decorated with `@mcp.tool()`.
- Most image inputs require base64 **with** the `data:image/png;base64,` prefix. Exceptions that require **no prefix**: `pet_act`, `pet_detect`, `pet_detect_furbo`, `cat_checking`, `dog_checking`, `cat_limb_checking`, `dog_limb_checking`.
- The `_post()` helper handles auth, timeout (30s), and errors uniformly.
- `JSON_BODY_PATHS` (line 18) controls which endpoints send `json=` vs `data=`. Some endpoints in the upstream API require form-encoded bodies; adding a new endpoint may need updating this set.
- Token is set to `""` on every request (line 27) — authentication is effectively disabled in code.
- API base is hardcoded: `http://192.168.199.121:16880`.

## Upstream API quirks

- Some endpoint paths in the upstream API have typos (`PeytId` instead of `PetId`). Do not "fix" these — they match the real server.
- `openapi.json` documents the full upstream API surface. The MCP server does not expose all endpoints.

## No test/lint/CI

There are no tests, linters, formatters, or CI config. When adding code, follow existing style (Chinese docstrings, camelCase in API payloads).
