# Test Suite Improvement Plan

## Current State Analysis

### ✅ What We Have (Good)
- **103 tests** across 5 modules
- **Organized by module** (test_core.py, test_array.py, etc.)
- **Realistic data** in tests (no excessive mocking)
- **Bug regression tests** (TypeError, DataArray shape bugs)
- **Integration tests** with real services

### ❌ What We're Missing (Critical Issues)

#### 1. **Test Taxonomy Violations** (Guideline #2)
- **No separation** between unit/contract/integration tests
- **All tests mixed together** in single files
- **No markers** for test types (@pytest.mark.slow, @pytest.mark.net)
- **No property-based tests** using hypothesis

#### 2. **Layout Violations** (Guideline #4)
- **Missing proper structure**: tests/unit/, tests/contract/, tests/integration/
- **No VCR cassettes** for recorded HTTP interactions
- **No shared fixtures** in conftest.py
- **No test data directory** with fixtures

#### 3. **Mocking Policy Violations** (Guideline #5)
- **Over-mocking** in some tests (mocking internal logic)
- **No fake server** for testing retry/backoff logic
- **Missing proper HTTP mocking** with respx/httpx

#### 4. **Coverage Issues** (Guideline #3)
- **No coverage reporting** configured
- **No branch coverage** enabled
- **No coverage thresholds** enforced

#### 5. **Performance Issues** (Guideline #12)
- **No performance budgets** enforced
- **No timeout controls** on tests
- **No parallel execution** configured

#### 6. **Bad Practices Present** (Guideline #13)
- **Some try/except** blocks suppressing failures
- **Module-level imports** missing in some tests
- **Long tests** checking multiple concerns
- **Hidden state** between tests

## Improvement Plan

### Phase 1: Restructure Test Layout (Priority: HIGH)

#### 1.1 Create Proper Directory Structure
```bash
tests/
├── unit/                    # Fast, pure logic tests
│   ├── test_tiling_math.py
│   ├── test_url_builder.py
│   ├── test_cache_policy.py
│   ├── test_retry_backoff.py
│   └── data/               # Tiny fixture files (≤50 KB)
├── contract/               # VCR-recorded HTTP interactions
│   ├── wcs/
│   │   ├── test_wcs_contract.py
│   │   └── cassettes/
│   ├── wms/
│   │   ├── test_wms_contract.py
│   │   └── cassettes/
│   └── wmts/
│       ├── test_wmts_contract.py
│       └── cassettes/
├── integration/            # Live service tests
│   └── test_live_endpoints.py
├── conftest.py            # Shared fixtures, markers, VCR config
└── pytest.ini            # Test configuration
```

#### 1.2 Move Existing Tests to Correct Categories
- **Unit tests**: Pure logic (bbox math, tile grid, CRS conversion)
- **Contract tests**: HTTP interactions with recorded responses
- **Integration tests**: Real service calls (marked @pytest.mark.slow @pytest.mark.net)

### Phase 2: Implement Proper Test Markers (Priority: HIGH)

#### 2.1 Add Test Markers
```python
# conftest.py
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow (>1s)")
    config.addinivalue_line("markers", "net: marks tests requiring network")
    config.addinivalue_line("markers", "contract: marks VCR-backed tests")
    config.addinivalue_line("markers", "property: marks property-based tests")
```

#### 2.2 Configure CI Policy
- **PR CI**: `pytest -m "not slow and not net"` (unit + contract only)
- **Nightly CI**: `pytest -m "slow or net"` (integration tests)

### Phase 3: Add Property-Based Testing (Priority: MEDIUM)

#### 3.1 Install Hypothesis
```bash
uv add --dev hypothesis
```

#### 3.2 Create Property Tests
- **Bbox round-trip**: bbox → tile → bbox consistency
- **Tile math**: Parent/child tile relationships
- **CRS conversion**: Coordinate transformation invariants
- **Cache keys**: URL + headers → stable cache keys

### Phase 4: Implement Proper HTTP Mocking (Priority: MEDIUM)

#### 4.1 Replace requests with httpx + respx
```bash
uv add httpx
uv add --dev respx
```

#### 4.2 Create Fake Server Fixture
```python
# conftest.py
@pytest.fixture
def fake_server():
    """Programmable server for testing redirects/errors/gzip"""
    with HTTPServer(host="127.0.0.1", port=0) as server:
        yield server
```

#### 4.3 Add VCR Recording
```bash
uv add --dev pytest-vcr
```

### Phase 5: Add Coverage & Performance Monitoring (Priority: MEDIUM)

#### 5.1 Configure Coverage
```toml
# pyproject.toml
[tool.coverage.run]
source = ["src/tilearray"]
branch = true

[tool.coverage.report]
fail_under = 85
show_missing = true
```

#### 5.2 Add Performance Budgets
```python
# conftest.py
@pytest.fixture
def performance_budget():
    """Enforce performance budgets"""
    return {
        "import_time": 0.2,  # < 200ms
        "tile_fetch": 0.05,  # < 50ms
    }
```

### Phase 6: Fix Bad Practices (Priority: LOW)

#### 6.1 Remove try/except Suppression
- Replace with proper assertions
- Use pytest.raises() for expected exceptions

#### 6.2 Add Module-Level Imports
- Move imports to top of test files
- Use conftest.py for shared imports

#### 6.3 Split Long Tests
- One test per concern
- Use parametrize for multiple scenarios

## Implementation Timeline

### Week 1: Structure & Markers
- [ ] Create new directory structure
- [ ] Move existing tests to correct categories
- [ ] Add test markers and CI configuration
- [ ] Update conftest.py with shared fixtures

### Week 2: HTTP Mocking & VCR
- [ ] Replace requests with httpx + respx
- [ ] Implement fake server fixture
- [ ] Add VCR recording for contract tests
- [ ] Record cassettes for WCS/WMS/WMTS

### Week 3: Property Testing & Coverage
- [ ] Add hypothesis property tests
- [ ] Configure coverage reporting
- [ ] Add performance budgets
- [ ] Implement parallel test execution

### Week 4: Cleanup & Documentation
- [ ] Fix bad practices
- [ ] Add test documentation
- [ ] Update CI configuration
- [ ] Add secret scanning

## Success Metrics

### Coverage Targets
- **Overall coverage**: ≥ 85%
- **Core logic coverage**: ≥ 90%
- **Branch coverage**: Enabled

### Performance Targets
- **Import time**: < 200ms
- **Single tile fetch**: < 50ms
- **Full test suite**: < 60s (unit + contract)

### Quality Targets
- **No network** in unit tests
- **All secrets redacted** in cassettes
- **All tests parallel-safe**
- **No bad practices** present

## Risk Mitigation

### High Risk: Breaking Existing Tests
- **Mitigation**: Implement incrementally, maintain backward compatibility
- **Rollback**: Keep old test structure until new one is proven

### Medium Risk: VCR Cassette Maintenance
- **Mitigation**: Automated cassette refresh, quarterly review
- **Monitoring**: CI job to detect secret leaks

### Low Risk: Performance Regression
- **Mitigation**: Performance budgets enforced in CI
- **Monitoring**: Regular performance testing

## Next Steps

1. **Start with Phase 1**: Restructure test layout
2. **Implement markers**: Add proper test categorization
3. **Add VCR**: Record HTTP interactions
4. **Property tests**: Add hypothesis-based testing
5. **Coverage**: Implement coverage reporting
6. **Cleanup**: Fix bad practices

This plan will transform our test suite from a basic collection of tests into a professional, maintainable, and comprehensive testing framework that follows industry best practices.
