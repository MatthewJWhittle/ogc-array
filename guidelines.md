# Python Library Structure & Development Guidelines

## 1. Core Principles

* Use the `src/` layout. All importable code lives under `src/<package_name>/`.
* Keep the **public API minimal**. Re-export core functions and classes in `__init__.py`.
* **Separate logic and I/O.** Pure functions go in `core.py`; side effects and integrations go in `io.py`.
* Avoid global state. Pass configuration explicitly or via dataclasses.
* Prefer **composition over inheritance**. Use `Protocols` for interfaces.

---

## 2. Project Structure

```bash
project/
├─ src/
│  └─ mylib/
│     ├─ __init__.py
│     ├─ _version.py
│     ├─ core.py
│     ├─ io.py
│     ├─ errors.py
│     └─ typing.py
├─ tests/
│  ├─ conftest.py
│  └─ test_core.py
├─ docs/
│  ├─ index.md
│  └─ api.md
├─ pyproject.toml
├─ README.md
├─ LICENSE
├─ CHANGELOG.md
└─ .pre-commit-config.yaml
```

---

## 3. Build & Packaging

* Use **`pyproject.toml`** (PEP 621). Do not use `setup.py`.
* Build with **Hatch** or **uv**.
* Follow **Semantic Versioning** (`MAJOR.MINOR.PATCH`).
* Source version from VCS tags (via `hatch-vcs` or `uv version`).
* Keep runtime dependencies minimal. Use **extras** for optional stacks.
* Include `py.typed` to ship type hints.

---

## 4. Code Quality

* Use **Ruff** for linting and formatting.
* Use **Mypy** with strict type checking.
* Use **Pytest** for testing. Mirror `src/` layout.
* Unit tests should be fast. Mark integration tests as `@pytest.mark.slow`.
* Use **property-based tests** (`hypothesis`) for data validation.
* Pre-commit hooks must run Ruff, Mypy, and Pytest before commit.

---

## 5. Public API

```python
from .core import do_thing, Thing
from .errors import MylibError
__all__ = ["do_thing", "Thing", "MylibError"]
```

* Define exports explicitly in `__init__.py`.
* Use `__version__` from `_version.py`.
* Avoid exposing internal or unstable functions.

---

## 6. Error Handling & Logging

* Define a **base exception** (`MylibError`) and subclass for specific cases.
* Wrap third-party exceptions in custom errors.
* Use `logging.getLogger(__name__)`; never use `print`.

---

## 7. Typing & Interfaces

* Use **Python 3.10+ typing features** (`|`, `TypeAlias`, `Protocol`, `Literal`).
* Store shared aliases and protocols in `typing.py`.
* Always run `mypy --strict`.
* Mark the package as typed with a `py.typed` file.

---

## 8. Documentation

* Use **MkDocs Material** with `mkdocstrings`.
* Use **Google or NumPy docstring style**.
* Keep `README.md` concise:

  * What it does
  * How to install
  * 60-second example
  * Link to docs and changelog

---

## 9. CI/CD

* Use **GitHub Actions** or equivalent CI.
* Run lint, type-check, tests, and build on every push and PR.
* Test on **Python 3.10–3.12**.
* On tag `v*`, build and publish to **PyPI** automatically.

---

## 10. Dependencies

* Keep runtime dependencies broad (`>=,<`) for compatibility.
* Lock dev dependencies using **uv** or **Hatch** environments.
* Use extras for heavy dependencies (`[gdal]`, `[torch]`, `[azure]`).

---

## 11. Config & Data

* No hidden config files.
* Accept configuration via kwargs or TOML.
* No secrets in the repository. Use **environment variables** or **Azure Key Vault**.
* Avoid bundling binary assets. Use runtime downloads with caching.

---

## 12. Testing Policy

* Aim for **>90% coverage** of core logic.
* Integration tests can run slower but must be isolated.
* Every bug fix must include a reproducing test.
* Keep fixtures simple and reusable.

---

## 13. Release Process

1. Update `CHANGELOG.md` following *Keep a Changelog* format.
2. Bump version automatically from tag.
3. Run full CI.
4. Create tag `vX.Y.Z` to trigger PyPI and GitHub Release.

---

## 14. Optional Geospatial / ML Notes

* Normalise CRS at data boundaries; keep consistent internal CRS.
* Gate heavy dependencies (`rasterio`, `torch`, `azureml`) behind extras.
* Prefer `xarray` or `numpy` for array ops; avoid in-memory GDAL ops.
* Always handle **nodata values** and **dtypes** explicitly.

---

## 15. Summary Checklist

* [ ] `src/` layout established
* [ ] `pyproject.toml` configured with build tools and extras
* [ ] Ruff, Mypy, Pytest, and Pre-commit set up
* [ ] Custom exceptions and logging implemented
* [ ] Typing complete with `py.typed`
* [ ] Docs built with MkDocs
* [ ] CI/CD pipeline operational
* [ ] SemVer, changelog, and tagged release in place
* [ ] Extras defined for optional dependencies

# TESTING.md — Rules for AI Agent (Python Tile/Data Library)

> Generic, enforceable rules for testing a Python library that fetches tiles/data from web services (XYZ/WMTS/WMS/HTTP APIs). Keep CI fast, deterministic, and provider‑agnostic.

---

## 1. Scope & Goals

* Validate **logic, protocols, and resilience** without depending on live services.
* Default suite: **no network**, finishes **< 60 s** on CI Linux, Python 3.10–3.12.
* Prove correctness at three layers: **unit → contract (recorded) → live (opt‑in)**.

## 2. Test Taxonomy (must separate)

1. **Unit (fast, pure):** No network; test tiling math, URL building, caching, retries/backoff policies, CRS conversions, content validation.
2. **Contract (recorded HTTP):** Use recorded interactions (VCR) to assert protocol compatibility and header/query semantics. Secrets redacted.
3. **Live Integration (opt‑in):** Real endpoints; marked; run only on scheduled/nightly.
4. **Property‑based:** Randomised inputs to check invariants (tile↔bbox round‑trip, bounds handling, cache key stability).
5. **Performance/Smoke:** Lightweight throughput/latency/import‑time checks with strict timeouts.

## 3. Tooling (choose and standardise)

* Test: **pytest**, **pytest‑xdist** (parallel), **pytest‑timeout**.
* Property tests: **hypothesis**.
* HTTP: Prefer **httpx**; mock with **respx** (or `responses` if using `requests`).
* Recording: **vcrpy** or **pytest‑vcr**; redact tokens; record mode `once`.
* Coverage: **coverage.py** (branch), target ≥ **85%** overall, ≥ **90%** for core logic.

## 4. Layout

```bash
tests/
  unit/
    test_tiling_math.py
    test_url_builder.py
    test_cache_policy.py
    test_retry_backoff.py
    data/        # tiny fixture files (≤50 KB)
  contract/
    xyz/
      test_xyz_contract.py
      cassettes/
    wmts/
      test_wmts_contract.py
      cassettes/
  integration/
    test_live_endpoints.py   # @net @slow, skipped on PRs
  conftest.py                # shared fixtures, markers, VCR config
```

## 5. Mocking Policy

* **Mock:** network I/O, disk writes, clocks, randomness (in unit tests only).
* **Do not mock:** library’s own retry/backoff/cache logic—test it against a **fake server**.
* Provide a programmable **fake server** fixture (e.g., `pytest‑httpserver`) for redirects (301/302), rate limits (429), transient errors (5xx), gzip/chunked responses, and ETag flows.

## 6. Behaviours to Assert (tile/data clients)

* **URL templating:** `/{z}/{x}/{y}` patterns, subdomains, query strings; credentials in **headers**, not URLs.
* **Tiling math:** bbox↔tile index round‑trip; parent/child relations; min/max zoom clamping; antimeridian and polar edges.
* **HTTP contract:** explicit connect/read timeouts; retry on **idempotent + retryable** codes (429/502/503/504) with **jittered exponential backoff**; honour `Retry‑After`.
* **Caching:** cache key = URL + relevant headers; `ETag`/`If‑None‑Match`, `Last‑Modified`/`If‑Modified‑Since`, TTL expiry, LRU eviction; assert hit→miss sequences.
* **Content validation:** MIME type; minimal image sanity (dims >0, decodes); for rasters: dtype, shape, nodata; use **tolerant** comparisons (pixel MAE/SSIM), not byte‑equality.
* **Concurrency:** thread/async safety; connection pool reuse; no FD leaks; bounded parallelism.
* **Resource hygiene:** close responses/clients; clean temp files; context managers.

## 7. Raster/Image Comparison Rules

* Compare numerically (MAE/PSNR/SSIM) with explicit tolerances.
* Ignore volatile metadata (timestamps, software tags).
* Provide helper `assert_image_like(a, b, *, max_mae=1.0)` and reuse it.

## 8. Fixtures (required)

* `client()` — configured HTTP client with small timeouts.
* `fake_server()` — programmable server for redirects/errors/gzip.
* `tile_coords()` — `hypothesis` strategy constrained to valid ranges.
* `tmp_cache_dir()` — isolated cache; expose metrics (hits/misses/evictions).
* `vcr_config` — global cassette rules: redact headers (`Authorization`, `X‑API‑Key`), normalise dates, match on method+path+query; `record_mode="once"`.

## 9. Markers & CI Policy

* Default run: **no network**, `-m "not slow and not net"`.
* `@pytest.mark.slow` ⇒ >1 s; `@pytest.mark.net` ⇒ any outbound traffic; `@pytest.mark.contract` ⇒ VCR‑backed.
* PR CI: unit + contract; fail if any cassette contains unredacted secrets (regex scan step).
* Nightly CI: add `@net` integration; rate‑limit and randomise provider order; optional cassette refresh behind maintainer flag.

## 10. Data & Secrets Hygiene

* Keep binary fixtures tiny and committed under `tests/data`.
* Never commit real credentials; require via env vars; skip `@net` tests if missing.
* Redact tokens from cassettes; enforce by CI job that scans repo + cassettes.

## 11. Failure Forensics (make debugging easy)

* On HTTP failure, error messages must include: URL, status, attempt count, backoff ms, and any request/trace IDs present.
* Log cache events at DEBUG in tests; assert expected sequences.

## 12. Performance Budgets

* Importing the library: **< 200 ms** cold start.
* Single tile fetch (mocked): **< 50 ms** median in unit tests.
* Parallel fetch burst (mocked): throughput scales ~linearly up to configured limit; assert no starvation/deadlocks.

## 13. Bad Practices to Avoid

* Using `try/except` in tests to suppress failures. Tests must fail visibly.
* Imports inside tests instead of module-level imports (breaks collection and fixtures).
* Over‑mocking or mocking internal logic.
* Changing tests to fit broken code rather than fixing code to satisfy valid tests.
* Testing private implementation details instead of public behaviour.
* Writing excessively long tests that check multiple concerns instead of focused, short ones.
* Using arbitrary `sleep()` or timing loops—use deterministic clocks or fake time.
* Allowing hidden state between tests (globals, shared caches).
* Writing assertions without context—always include diagnostic messages.
* Network or file system access in unit tests.

## 14. Minimal Snippets (reference only)

**Mock HTTP with respx (httpx):**

```python
import respx
from httpx import Response

@respx.mock
def test_retries_on_503(tile_client):
    route = respx.get("https://tiles.example.com/1/2/3.png").mock(
        side_effect=[Response(503), Response(200, content=b"PNG...")]
    )
    content = tile_client.get(1, 2, 3)
    assert route.called
    assert content.startswith(b"PNG")
```

**Property test skeleton:**

```python
from hypothesis import given, strategies as st

@given(z=st.integers(0, 20), x=st.integers(0, 2**20-1), y=st.integers(0, 2**20-1))
def test_roundtrip(z, x, y):
    x %= 1 << z; y %= 1 << z
    bbox = tile_to_bbox(z, x, y)
    z2, x2, y2 = bbox_to_tile(bbox, z)
    assert (z, x, y) == (z2, x2, y2)
```

## 15. Final Checklist (enforced)

* [ ] Unit tests cover URL/tiling/caching/retry logic with **no network**.
* [ ] Contract tests recorded; secrets redacted; expiries reviewed quarterly.
* [ ] Live tests marked and excluded from PRs; require env‑gated creds.
* [ ] Coverage thresholds met; branch coverage enabled.
* [ ] CI includes secret‑leak scan and cassette policy checks.
* [ ] Fixtures reusable; no global state; tests parallel‑safe.
* [ ] No bad practices present in PRs (see section 13).

**Owner:** AI Agent  • **Policy:** Do not deviate without explicit maintainer approval.
