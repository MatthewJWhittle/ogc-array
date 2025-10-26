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

