# OGC Array

A Python library for OGC (Open Geospatial Consortium) array operations.

[![Tests](https://github.com/yourusername/ogc-array/workflows/Test/badge.svg)](https://github.com/yourusername/ogc-array/actions)
[![Build](https://github.com/yourusername/ogc-array/workflows/Build%20and%20Publish/badge.svg)](https://github.com/yourusername/ogc-array/actions)
[![codecov](https://codecov.io/gh/yourusername/ogc-array/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/ogc-array)
[![PyPI version](https://badge.fury.io/py/ogc-array.svg)](https://badge.fury.io/py/ogc-array)
[![Python versions](https://img.shields.io/pypi/pyversions/ogc-array.svg)](https://pypi.org/project/ogc-array/)

## Features

- **Array Processing**: Efficient processing of OGC array data structures
- **NumPy Integration**: Built on top of NumPy for high-performance operations
- **Type Safety**: Full type hints and mypy support
- **Testing**: Comprehensive test suite with pytest
- **CI/CD**: Automated testing and building with GitHub Actions

## Installation

### Using uv (Recommended)

```bash
uv add ogc-array
```

### Using pip

```bash
pip install ogc-array
```

## Quick Start

```python
import numpy as np
from ogc_array import ArrayProcessor

# Create a processor
processor = ArrayProcessor()

# Set some data
data = np.array([1, 2, 3, 4, 5])
processor.set_data(data)

# Process the data
mean_value = processor.process("mean")
print(f"Mean: {mean_value}")  # Output: Mean: 3.0

# Get array information
print(f"Shape: {processor.get_shape()}")  # Output: Shape: (5,)
print(f"Data type: {processor.get_dtype()}")  # Output: Data type: int64
```

## Development

### Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) for package management

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ogc-array.git
cd ogc-array
```

2. Install dependencies:
```bash
uv sync --dev
```

3. Install pre-commit hooks:
```bash
make pre-commit
```

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test file
uv run pytest tests/test_core.py
```

### Code Quality

```bash
# Run linting
make lint

# Format code
make format

# Run pre-commit on all files
make pre-commit-run
```

### Building

```bash
# Build the package
make build

# Clean build artifacts
make clean
```

## Project Structure

```
ogc-array/
├── ogc_array/
│   ├── __init__.py
│   └── core.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_core.py
├── notebooks/
│   ├── examples/
│   │   └── basic_usage.ipynb
│   └── README.md
├── .github/
│   └── workflows/
│       ├── test.yml
│       └── build.yml
├── pyproject.toml
├── Makefile
├── tox.ini
├── .pre-commit-config.yaml
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`make test && make lint`)
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### 0.1.0 (2024-01-XX)

- Initial release
- Basic ArrayProcessor class
- NumPy integration
- Comprehensive test suite
- CI/CD pipeline setup