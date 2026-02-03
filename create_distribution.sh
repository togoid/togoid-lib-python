#!/bin/bash
# Create customer distribution ZIP for togoid-lib-python
# This script creates a clean distribution package without development files

set -e  # Exit on error

# Configuration
DIST_DIR="/tmp/togoid-lib-python-dist"
ZIP_FILE="togoid-lib-python.zip"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Creating Customer Distribution ZIP"
echo "=========================================="
echo ""

# Clean up any existing files
echo "1. Cleaning up..."
rm -rf "$DIST_DIR"
rm -f "$PROJECT_DIR/$ZIP_FILE"

# Create distribution directory
echo "2. Creating distribution directory..."
mkdir -p "$DIST_DIR"

# Copy main package (excluding __pycache__)
echo "3. Copying togoid package..."
cp -r "$PROJECT_DIR/togoid" "$DIST_DIR/"

# Remove __pycache__ directories and .pyc files
echo "4. Removing cache files..."
find "$DIST_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$DIST_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true

# Copy essential files
echo "5. Copying documentation and configuration..."
cp "$PROJECT_DIR/README.md" "$DIST_DIR/"
cp "$PROJECT_DIR/TESTING.md" "$DIST_DIR/"
cp "$PROJECT_DIR/pyproject.toml" "$DIST_DIR/"

# Copy optional files if they exist
[ -f "$PROJECT_DIR/.gitignore" ] && cp "$PROJECT_DIR/.gitignore" "$DIST_DIR/"
[ -f "$PROJECT_DIR/requirements.txt" ] && cp "$PROJECT_DIR/requirements.txt" "$DIST_DIR/"
[ -f "$PROJECT_DIR/QUICKSTART_UV.md" ] && cp "$PROJECT_DIR/QUICKSTART_UV.md" "$DIST_DIR/"
[ -f "$PROJECT_DIR/PROJECT_STRUCTURE.md" ] && cp "$PROJECT_DIR/PROJECT_STRUCTURE.md" "$DIST_DIR/"

# Copy test files (only the two main ones for customers)
echo "6. Copying test files..."
cp "$PROJECT_DIR/test_readme_examples.py" "$DIST_DIR/"
cp "$PROJECT_DIR/test_cli_examples.sh" "$DIST_DIR/"

# Make test script executable
chmod +x "$DIST_DIR/test_cli_examples.sh"

# Create ZIP file
echo "7. Creating ZIP archive..."
cd /tmp
zip -r "$ZIP_FILE" togoid-lib-python-dist/ -x "*.pyc" "*/__pycache__/*" -q

# Move to original directory
mv "$ZIP_FILE" "$PROJECT_DIR/"

# Clean up temporary directory
echo "8. Cleaning up temporary files..."
rm -rf "$DIST_DIR"

# Show results
echo ""
echo "=========================================="
echo "✓ Distribution ZIP created successfully!"
echo "=========================================="
echo ""
echo "File: $PROJECT_DIR/$ZIP_FILE"
ls -lh "$PROJECT_DIR/$ZIP_FILE"
echo ""
echo "Contents:"
unzip -l "$PROJECT_DIR/$ZIP_FILE"

echo ""
echo "=========================================="
echo "Included in distribution:"
echo "=========================================="
echo "• Package: togoid/ (all .py files)"
echo "• Tests: test_readme_examples.py, test_cli_examples.sh"
echo "• Docs: README.md, TESTING.md, QUICKSTART_UV.md, PROJECT_STRUCTURE.md"
echo "• Config: pyproject.toml, requirements.txt, .gitignore"
echo ""
echo "Excluded from distribution:"
echo "• Development test files (test_customer_feedback.py, etc.)"
echo "• Internal docs (FEEDBACK_FIX_PLAN.md, etc.)"
echo "• Cache files (__pycache__/, *.pyc)"
echo ""
echo "=========================================="
