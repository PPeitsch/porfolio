#
# This script manages project dependencies using pip-tools for Windows.
# It ensures that production and development requirements are consistent
# by using a unified constraints file.
#
Write-Host "Using Python executable: $(python --version)"
Write-Host "---"

# Step 1: Generate a unified constraints file from all inputs.
Write-Host "1/3: Generating unified constraints file (constraints.txt)..."
python -m piptools compile --resolver=backtracking --quiet -o constraints.txt requirements-all.in

# Step 2: Compile production requirements, respecting the constraints.
Write-Host "2/3: Compiling production requirements (requirements.txt)..."
python -m piptools compile --resolver=backtracking --quiet -o requirements.txt --constraint=constraints.txt requirements.in

# Step 3: Compile development requirements, respecting the constraints.
Write-Host "3/3: Compiling development requirements (requirements-dev.txt)..."
python -m piptools compile --resolver=backtracking --quiet -o requirements-dev.txt --constraint=constraints.txt requirements-dev.in

Write-Host "---"
Write-Host "OK: Dependency files updated successfully!"
