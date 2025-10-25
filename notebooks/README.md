# Development Notebooks

This directory contains Jupyter notebooks for development, experimentation, and documentation.

## Notebooks

- `examples/` - Example usage notebooks
- `experiments/` - Experimental code and prototyping
- `documentation/` - Notebooks that generate documentation

## Usage

To run notebooks with the development environment:

```bash
# Install jupyter in development environment
uv add --dev jupyter ipykernel

# Start jupyter
uv run jupyter lab
# or
uv run jupyter notebook
```

## Adding to .gitignore

Consider adding large output files to `.gitignore`:

```
# Jupyter Notebook
.ipynb_checkpoints
*.ipynb_checkpoints

# Large data files
notebooks/data/
notebooks/outputs/
```
