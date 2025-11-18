# Quick Start with uv

This guide shows how to quickly get started with TogoID using [uv](https://github.com/astral-sh/uv), a blazingly fast Python package installer.

## Why uv?

- 🚀 **10-100x faster** than pip
- 📦 **Better dependency resolution**
- 🔒 **Reproducible builds** with lock files
- 💾 **Global cache** for faster reinstalls

## Installation

### 1. Install uv

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Using pip (if you prefer)
pip install uv
```

### 2. Clone the repository

```bash
git clone https://github.com/togoid/togoid-lib-python.git
cd togoid-lib-python
```

### 3. Create virtual environment

```bash
# Create .venv directory
uv venv

# Activate the virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

### 4. Install the package

```bash
# Basic installation
uv pip install -e .

# With pandas support (recommended)
uv pip install -e ".[pandas]"

# With development tools
uv pip install -e ".[dev]"
```

## Quick Test

```bash
# Test the installation
python3 -c "from togoid import TogoIDConverter; print('✓ Installation successful')"

# Try the CLI
togoid --version

# Convert some IDs
togoid convert --ids 1,9 --route ncbigene,ensembl_gene
```

## Common Tasks

### Run tests

```bash
# Python library tests
python3 test_readme_examples.py

# CLI tests
bash test_cli_examples.sh
```

### Add new dependencies

```bash
# Add a dependency
uv pip install requests

# Generate requirements.txt
uv pip freeze > requirements.txt
```

### Update dependencies

```bash
# Update all packages
uv pip install --upgrade -e ".[pandas,dev]"
```

### Clean environment

```bash
# Deactivate and remove
deactivate
rm -rf .venv

# Recreate
uv venv
source .venv/bin/activate
uv pip install -e ".[pandas,dev]"
```

## Speed Comparison

Here's a real-world comparison of installation times:

| Tool | Time | Speed |
|------|------|-------|
| **uv** | ~2s | 🚀🚀🚀 |
| pip | ~30s | 🐌 |

*Results may vary depending on your system and network connection.*

## Troubleshooting

### Command not found: uv

```bash
# Add to PATH (Linux/macOS)
export PATH="$HOME/.cargo/bin:$PATH"

# Or reinstall
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Import errors

```bash
# Make sure you're in the virtual environment
which python3  # Should show .venv/bin/python3

# If not, activate it
source .venv/bin/activate
```

### Slow installation

```bash
# Clear cache and retry
rm -rf ~/.cache/uv
uv pip install -e ".[pandas]"
```

## Next Steps

- Read the [README.md](README.md) for detailed usage
- Check [TESTING.md](TESTING.md) for testing guide
- See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for project overview

## Learn More About uv

- [uv Documentation](https://github.com/astral-sh/uv)
- [uv vs pip benchmark](https://github.com/astral-sh/uv#benchmarks)
- [Python Packaging Guide](https://packaging.python.org/)
