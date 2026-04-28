#!/bin/bash
# test_install.sh - Test the built wheel in a fresh virtual environment

set -e  # exit immediately if any command fails

# Find the most recent wheel in dist/
WHEEL=$(ls -t dist/*.whl 2>/dev/null | head -1)
if [ -z "$WHEEL" ]; then
    echo " No wheel file found in dist/. Run 'python setup.py sdist bdist_wheel' first."
    exit 1
fi

echo "Testing wheel: $WHEEL"

# Create a temporary directory
TEMP_DIR=$(mktemp -d)
echo "Temporary directory: $TEMP_DIR"
cd "$TEMP_DIR"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv test_install
source test_install/bin/activate

# Install the wheel
echo "Installing wheel..."
pip install --quiet "$OLDPWD/$WHEEL"

# Test import
echo " Testing import..."
python -c "import django_user_permissions; print('Import successful!')"

# Optional: run a more thorough check (e.g., list installed package files)
echo "Package contents:"
pip show -f django_user_permissions | grep -E "Location|Files"

# Cleanup
echo "Cleaning up..."
deactivate
cd "$OLDPWD"
rm -rf "$TEMP_DIR"

echo "All tests passed!"