#!/bin/bash
#
# This script manages project dependencies using pip-tools.
# It ensures that production and development requirements are consistent
# by using a unified constraints file.

set -e

# Define python executable to ensure consistency
# Compile with the lowest supported Python (see the CI matrix) so the pins install on all of them.
PYTHON_EXEC="python3.10"
PIP_COMPILE_EXEC="$PYTHON_EXEC -m piptools compile"

echo "Using Python executable: $($PYTHON_EXEC --version)"
echo "---"

# Step 1: Generate a unified constraints file from all inputs.
# This resolves all dependencies together to find a compatible set.
echo "1/3: Generating unified constraints file (constraints.txt)..."
$PIP_COMPILE_EXEC \
    --resolver=backtracking \
    --quiet \
    -o constraints.txt \
    requirements-all.in

# Step 2: Compile production requirements, respecting the constraints.
echo "2/3: Compiling production requirements (requirements.txt)..."
$PIP_COMPILE_EXEC \
    --resolver=backtracking \
    --quiet \
    -o requirements.txt \
    --constraint=constraints.txt \
    requirements.in

# Step 3: Compile development requirements, respecting the constraints.
echo "3/3: Compiling development requirements (requirements-dev.txt)..."
$PIP_COMPILE_EXEC \
    --resolver=backtracking \
    --quiet \
    -o requirements-dev.txt \
    --constraint=constraints.txt \
    requirements-dev.in

echo "---"
echo "OK: Dependency files updated successfully!"
