#!/bin/bash
# Download packages
bash uncertain-packages/download-packages.sh

# Run ScanCode on downloaded packages
mkdir -p scancode-results

for pkg_dir in downloaded-packages/*/; do
  pkg_name=$(basename "$pkg_dir")
  echo "Scanning $pkg_name..."

  scancode \
    -l -c -i \
    --json "scancode-results/${pkg_name}.json" \
    --timeout 120 \
    --max-depth 3 \
    "$pkg_dir"
done