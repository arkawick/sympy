#!/usr/bin/env python3
"""
Generate comprehensive license comparison report across all analysis layers:
- ORT (Open Review Toolkit)
- PyPI API (Fast license fetch)
- ScanCode Toolkit (Deep source scanning)

Outputs a beautiful HTML page showing side-by-side license information.
"""

import json
import yaml
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from collections import defaultdict


class LicenseComparison:
    def __init__(self, ort_result_path: str, pypi_results_path: Optional[str],
                 scancode_results_dir: Optional[str], spdx_path: Optional[str],
                 uncertain_packages_path: Optional[str] = None):
        self.ort_result_path = Path(ort_result_path)
        self.pypi_results_path = Path(pypi_results_path) if pypi_results_path else None
        self.scancode_results_dir = Path(scancode_results_dir) if scancode_results_dir else None
        self.spdx_path = Path(spdx_path) if spdx_path else None
        self.uncertain_packages_path = Path(uncertain_packages_path) if uncertain_packages_path else None

        self.packages = {}  # Package ID -> License info from all sources
        self.uncertain_packages = {}  # Package ID -> uncertain package info (for ScanCode matching)

    def load_ort_licenses(self):
        """Extract declared licenses from ORT analyzer results."""
        print("📦 Loading ORT licenses...")

        if not self.ort_result_path.exists():
            print(f"⚠️  ORT result not found: {self.ort_result_path}")
            return

        with open(self.ort_result_path, 'r', encoding='utf-8') as f:
            ort_data = yaml.safe_load(f)

        analyzer = ort_data.get('analyzer', {})
        result = analyzer.get('result', {})
        packages = result.get('packages', [])

        for pkg in packages:
            pkg_id = pkg.get('id', '')
            declared = pkg.get('declared_licenses', [])
            declared_processed = pkg.get('declared_licenses_processed', {})
            spdx_expression = declared_processed.get('spdx_expression', '')

            # Parse package ID
            parts = pkg_id.split(':')
            pkg_type = parts[0] if len(parts) > 0 else 'Unknown'
            namespace = parts[1] if len(parts) > 1 else ''
            name = parts[2] if len(parts) > 2 else ''
            version = parts[3] if len(parts) > 3 else ''

            display_name = f"{namespace}/{name}" if namespace else name

            self.packages[pkg_id] = {
                'id': pkg_id,
                'type': pkg_type,
                'namespace': namespace,
                'name': name,
                'display_name': display_name,
                'version': version,
                'ort_declared': declared,
                'ort_spdx': spdx_expression if spdx_expression else 'NOASSERTION',
                'pypi_license': None,
                'pypi_expression': None,
                'scancode_licenses': [],
                'scancode_concluded': None,
                'homepage': pkg.get('homepage_url', ''),
                'repository': pkg.get('vcs', {}).get('url', ''),
            }

        print(f"✓ Loaded {len(self.packages)} packages from ORT")

    def load_uncertain_packages(self):
        """Load uncertain packages list (needed for ScanCode matching)."""
        if not self.uncertain_packages_path or not self.uncertain_packages_path.exists():
            print("⚠️  Uncertain packages file not found, will try basic ScanCode matching...")
            return

        print("📋 Loading uncertain packages list...")

        with open(self.uncertain_packages_path, 'r', encoding='utf-8') as f:
            uncertain_list = json.load(f)

        for pkg in uncertain_list:
            pkg_id = pkg.get('id', '')
            if pkg_id:
                self.uncertain_packages[pkg_id] = pkg

        print(f"✓ Loaded {len(self.uncertain_packages)} uncertain packages")

    def load_pypi_licenses(self):
        """Extract licenses from PyPI API fetch results."""
        if not self.pypi_results_path or not self.pypi_results_path.exists():
            print("⚠️  PyPI results not found, skipping...")
            return

        print("🐍 Loading PyPI licenses...")

        with open(self.pypi_results_path, 'r', encoding='utf-8') as f:
            pypi_data = json.load(f)

        packages_analyzed = pypi_data.get('packages', [])
        pypi_count = 0

        for pkg in packages_analyzed:
            pkg_id = pkg.get('id', '')
            fetched_license = pkg.get('fetched_license', {})

            if pkg_id in self.packages and fetched_license:
                # Check if fetch was successful
                if fetched_license.get('success'):
                    license_found = fetched_license.get('license', '')
                    license_expr = fetched_license.get('license_expression', '')

                    # Only set if we actually found a license
                    if license_found and license_found.lower() not in ['unknown', 'none', '', 'n/a']:
                        self.packages[pkg_id]['pypi_license'] = license_found
                        self.packages[pkg_id]['pypi_expression'] = license_expr
                        pypi_count += 1

        print(f"✓ Loaded PyPI licenses for {pypi_count} packages")

    def load_scancode_licenses(self):
        """Extract concluded licenses from ScanCode results.

        ScanCode only runs on uncertain packages (packages with missing licenses after ORT+PyPI).
        Files are named: {package-name}-{version}.json
        """
        if not self.scancode_results_dir or not self.scancode_results_dir.exists():
            print("⚠️  ScanCode results not found, skipping...")
            return

        print("🔍 Loading ScanCode licenses...")

        scancode_files = list(self.scancode_results_dir.glob("*.json"))
        print(f"   Found {len(scancode_files)} ScanCode JSON files")

        if not scancode_files:
            print("   No ScanCode results to process")
            return

        scancode_count = 0

        # If we have uncertain packages list, use it for accurate matching
        if self.uncertain_packages:
            print(f"   Using uncertain packages list for matching ({len(self.uncertain_packages)} packages)")

            for json_file in scancode_files:
                try:
                    # Extract package name and version from filename
                    # Format: package-name-version.json
                    file_stem = json_file.stem

                    # Try to match this file to an uncertain package
                    matched_pkg_id = None

                    for pkg_id, uncertain_pkg in self.uncertain_packages.items():
                        pkg_name = uncertain_pkg.get('name', '')
                        pkg_version = uncertain_pkg.get('version', '')

                        # Build expected filename (same as workflow logic)
                        expected_name = f"{pkg_name}-{pkg_version}".replace('/', '-').replace(':', '-')

                        if file_stem.lower() == expected_name.lower():
                            matched_pkg_id = pkg_id
                            print(f"   ✓ Matched {json_file.name} to {pkg_id}")
                            break

                        # Also try without version
                        if file_stem.lower().startswith(pkg_name.lower().replace('/', '-').replace(':', '-')):
                            matched_pkg_id = pkg_id
                            print(f"   ✓ Matched {json_file.name} to {pkg_id} (partial match)")
                            break

                    if not matched_pkg_id:
                        print(f"   ⚠️  Could not match {json_file.name} to any uncertain package")
                        continue

                    # Load and parse ScanCode results
                    with open(json_file, 'r', encoding='utf-8') as f:
                        scan_data = json.load(f)

                    # First, check package-level license (from package manifest)
                    # This is more reliable for well-packaged software
                    package_level_license = None
                    packages_section = scan_data.get('packages', [])

                    if packages_section and len(packages_section) > 0:
                        pkg_info = packages_section[0]  # Usually just one package per scan
                        package_level_license = pkg_info.get('declared_license_expression_spdx')

                        if package_level_license and package_level_license not in ['NOASSERTION', 'NONE', '']:
                            print(f"      Found package-level license: {package_level_license}")

                    # Also extract file-level licenses as backup/supplementary info
                    license_detections = defaultdict(int)

                    for file_info in scan_data.get('files', []):
                        if file_info.get('type') != 'file':
                            continue

                        for lic in file_info.get('licenses', []):
                            score = lic.get('score', 0)
                            if score >= 80:  # High confidence only
                                spdx_key = lic.get('spdx_license_key', lic.get('key', ''))
                                if spdx_key:
                                    license_detections[spdx_key] += 1

                    # Use package-level license if available, otherwise use file-level
                    if matched_pkg_id in self.packages:
                        if package_level_license:
                            # Use package-level license (most reliable)
                            self.packages[matched_pkg_id]['scancode_concluded'] = package_level_license

                            # Also store file-level detections if any
                            if license_detections:
                                sorted_licenses = sorted(license_detections.items(), key=lambda x: x[1], reverse=True)
                                self.packages[matched_pkg_id]['scancode_licenses'] = [
                                    {'license': lic, 'count': count} for lic, count in sorted_licenses
                                ]

                            scancode_count += 1

                        elif license_detections:
                            # No package-level license, use file-level detections
                            sorted_licenses = sorted(license_detections.items(), key=lambda x: x[1], reverse=True)

                            self.packages[matched_pkg_id]['scancode_licenses'] = [
                                {'license': lic, 'count': count} for lic, count in sorted_licenses
                            ]

                            # Primary license is most frequently detected
                            self.packages[matched_pkg_id]['scancode_concluded'] = sorted_licenses[0][0]
                            scancode_count += 1
                            print(f"      Found file-level license: {sorted_licenses[0][0]} (detected in {sorted_licenses[0][1]} files)")

                except Exception as e:
                    print(f"   ⚠️  Error processing {json_file.name}: {e}")

        else:
            # Fallback: try fuzzy matching if no uncertain packages list
            print("   No uncertain packages list - using fuzzy matching")

            for json_file in scancode_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        scan_data = json.load(f)

                    # First, check package-level license (from package manifest)
                    package_level_license = None
                    packages_section = scan_data.get('packages', [])

                    if packages_section and len(packages_section) > 0:
                        pkg_info = packages_section[0]
                        package_level_license = pkg_info.get('declared_license_expression_spdx')

                    # Also extract file-level licenses
                    license_detections = defaultdict(int)

                    for file_info in scan_data.get('files', []):
                        if file_info.get('type') != 'file':
                            continue

                        for lic in file_info.get('licenses', []):
                            score = lic.get('score', 0)
                            if score >= 80:  # High confidence only
                                spdx_key = lic.get('spdx_license_key', lic.get('key', ''))
                                if spdx_key:
                                    license_detections[spdx_key] += 1

                    # Match to package by fuzzy name matching
                    pkg_name_from_file = json_file.stem.lower()

                    matched_pkg_id = None
                    best_match_score = 0

                    for pkg_id, pkg_info in self.packages.items():
                        pkg_name = pkg_info['name'].lower()
                        pkg_name_normalized = pkg_name.replace('_', '-').replace('.', '-')

                        # Try exact match first
                        if pkg_name_normalized in pkg_name_from_file or pkg_name_from_file.startswith(pkg_name_normalized):
                            match_score = len(pkg_name_normalized)
                            if match_score > best_match_score:
                                matched_pkg_id = pkg_id
                                best_match_score = match_score

                    if matched_pkg_id:
                        if package_level_license and package_level_license not in ['NOASSERTION', 'NONE', '']:
                            # Use package-level license
                            self.packages[matched_pkg_id]['scancode_concluded'] = package_level_license

                            # Also store file-level detections if any
                            if license_detections:
                                sorted_licenses = sorted(license_detections.items(), key=lambda x: x[1], reverse=True)
                                self.packages[matched_pkg_id]['scancode_licenses'] = [
                                    {'license': lic, 'count': count} for lic, count in sorted_licenses
                                ]

                            scancode_count += 1

                        elif license_detections:
                            # Use file-level detections
                            sorted_licenses = sorted(license_detections.items(), key=lambda x: x[1], reverse=True)

                            self.packages[matched_pkg_id]['scancode_licenses'] = [
                                {'license': lic, 'count': count} for lic, count in sorted_licenses
                            ]

                            # Primary license is most frequently detected
                            self.packages[matched_pkg_id]['scancode_concluded'] = sorted_licenses[0][0]
                            scancode_count += 1

                except Exception as e:
                    print(f"   ⚠️  Error processing {json_file.name}: {e}")

        print(f"✓ Loaded ScanCode licenses for {scancode_count} packages")

    def load_spdx_concluded(self):
        """Extract concluded licenses from enhanced SPDX document."""
        if not self.spdx_path or not self.spdx_path.exists():
            print("⚠️  Enhanced SPDX not found, skipping...")
            return

        print("📋 Loading SPDX concluded licenses...")

        with open(self.spdx_path, 'r', encoding='utf-8') as f:
            if self.spdx_path.suffix == '.json':
                spdx_data = json.load(f)
            else:
                spdx_data = yaml.safe_load(f)

        spdx_packages = spdx_data.get('packages', [])

        for spdx_pkg in spdx_packages:
            pkg_name = spdx_pkg.get('name', '')
            concluded = spdx_pkg.get('licenseConcluded', 'NOASSERTION')

            # Match to our packages
            for pkg_id, pkg_info in self.packages.items():
                if pkg_info['name'] in pkg_name or pkg_name in pkg_info['name']:
                    if concluded != 'NOASSERTION' and not pkg_info.get('scancode_concluded'):
                        pkg_info['scancode_concluded'] = concluded
                    break

        print(f"✓ Loaded SPDX concluded licenses")

    def determine_status(self, pkg_info: Dict) -> str:
        """Determine license status across all sources."""
        ort_license = pkg_info['ort_spdx']
        pypi_license = pkg_info.get('pypi_expression') or pkg_info.get('pypi_license')
        scancode_license = pkg_info.get('scancode_concluded')

        # Normalize for comparison
        licenses = set()
        if ort_license and ort_license != 'NOASSERTION':
            licenses.add(ort_license)
        if pypi_license and pypi_license != 'NOASSERTION':
            licenses.add(pypi_license)
        if scancode_license and scancode_license != 'NOASSERTION':
            licenses.add(scancode_license)

        if not licenses:
            return 'missing'
        elif len(licenses) == 1:
            return 'complete'
        else:
            # Check if they're similar (MIT vs MIT License, etc.)
            normalized = {lic.upper().replace('-', '').replace(' ', '') for lic in licenses}
            if len(normalized) == 1:
                return 'complete'
            return 'conflict'

    def generate_html_report(self, output_path: str):
        """Generate beautiful HTML comparison report."""
        print("🎨 Generating HTML report...")

        # Sort packages by status and name
        packages_list = list(self.packages.values())
        packages_list.sort(key=lambda p: (
            0 if self.determine_status(p) == 'conflict' else
            1 if self.determine_status(p) == 'missing' else 2,
            p['display_name']
        ))

        # Count statistics
        total = len(packages_list)
        complete = sum(1 for p in packages_list if self.determine_status(p) == 'complete')
        conflicts = sum(1 for p in packages_list if self.determine_status(p) == 'conflict')
        missing = sum(1 for p in packages_list if self.determine_status(p) == 'missing')

        # Count how many packages have data from each source
        with_ort = sum(1 for p in packages_list if p['ort_spdx'] != 'NOASSERTION')
        with_pypi = sum(1 for p in packages_list if p.get('pypi_license'))
        with_scancode = sum(1 for p in packages_list if p.get('scancode_concluded'))

        print(f"   Packages with ORT data: {with_ort}")
        print(f"   Packages with PyPI data: {with_pypi}")
        print(f"   Packages with ScanCode data: {with_scancode}")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Layer License Comparison Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px 40px;
            background: #f8f9fa;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .stat-card h3 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .stat-card p {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .stat-complete {{ color: #10b981; }}
        .stat-conflicts {{ color: #f59e0b; }}
        .stat-missing {{ color: #ef4444; }}
        .stat-total {{ color: #667eea; }}

        .filters {{
            padding: 20px 40px;
            background: white;
            border-bottom: 2px solid #e5e7eb;
        }}

        .filter-buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .filter-btn {{
            padding: 10px 20px;
            border: 2px solid #e5e7eb;
            background: white;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9em;
        }}

        .filter-btn:hover {{
            background: #f3f4f6;
        }}

        .filter-btn.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}

        .table-container {{
            padding: 40px;
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}

        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        td {{
            padding: 15px;
            border-bottom: 1px solid #e5e7eb;
        }}

        tbody tr:hover {{
            background: #f9fafb;
        }}

        .package-name {{
            font-weight: 600;
            color: #1f2937;
        }}

        .package-version {{
            color: #6b7280;
            font-size: 0.9em;
        }}

        .license-cell {{
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
        }}

        .license-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 5px;
            background: #e5e7eb;
            margin: 2px;
            font-size: 0.85em;
        }}

        .license-noassertion {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .license-found {{
            background: #d1fae5;
            color: #065f46;
        }}

        .status-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .status-complete {{
            background: #d1fae5;
            color: #065f46;
        }}

        .status-conflict {{
            background: #fed7aa;
            color: #92400e;
        }}

        .status-missing {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .scancode-details {{
            font-size: 0.8em;
            color: #6b7280;
            margin-top: 5px;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            background: #f9fafb;
            color: #6b7280;
            font-size: 0.9em;
        }}

        .ltts-branding {{
            margin-top: 10px;
            font-weight: 600;
            color: #667eea;
        }}

        .legend {{
            padding: 20px 40px;
            background: #f9fafb;
            border-top: 2px solid #e5e7eb;
        }}

        .legend h3 {{
            margin-bottom: 15px;
            color: #1f2937;
        }}

        .legend-items {{
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .legend-icon {{
            width: 30px;
            height: 30px;
            border-radius: 5px;
        }}

        @media (max-width: 768px) {{
            .stats {{
                grid-template-columns: 1fr;
            }}

            .table-container {{
                padding: 20px;
            }}

            th, td {{
                padding: 10px;
                font-size: 0.85em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Multi-Layer License Comparison</h1>
            <p>Comprehensive license analysis from ORT, PyPI API, and ScanCode Toolkit</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <h3 class="stat-total">{total}</h3>
                <p>Total Packages</p>
            </div>
            <div class="stat-card">
                <h3 class="stat-complete">{complete}</h3>
                <p>Complete ({complete/total*100:.1f}%)</p>
            </div>
            <div class="stat-card">
                <h3 class="stat-conflicts">{conflicts}</h3>
                <p>Conflicts ({conflicts/total*100:.1f}%)</p>
            </div>
            <div class="stat-card">
                <h3 class="stat-missing">{missing}</h3>
                <p>Missing ({missing/total*100:.1f}%)</p>
            </div>
        </div>

        <div style="padding: 20px 40px; background: #f9fafb; border-bottom: 2px solid #e5e7eb;">
            <h3 style="margin-bottom: 15px; color: #1f2937;">📊 Data Sources Coverage</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 12px; height: 12px; background: #10b981; border-radius: 50%;"></div>
                    <span><strong>ORT:</strong> {with_ort}/{total} packages ({with_ort/total*100:.1f}%)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 12px; height: 12px; background: #3b82f6; border-radius: 50%;"></div>
                    <span><strong>PyPI API:</strong> {with_pypi}/{total} packages ({with_pypi/total*100:.1f}%)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 12px; height: 12px; background: #f59e0b; border-radius: 50%;"></div>
                    <span><strong>ScanCode:</strong> {with_scancode}/{total} packages ({with_scancode/total*100:.1f}%)</span>
                </div>
            </div>
        </div>

        <div class="filters">
            <div class="filter-buttons">
                <button class="filter-btn active" onclick="filterTable('all')">All Packages</button>
                <button class="filter-btn" onclick="filterTable('conflict')">Conflicts Only</button>
                <button class="filter-btn" onclick="filterTable('missing')">Missing Only</button>
                <button class="filter-btn" onclick="filterTable('complete')">Complete Only</button>
            </div>
        </div>

        <div class="table-container">
            <table id="licenseTable">
                <thead>
                    <tr>
                        <th>Package</th>
                        <th>Type</th>
                        <th>ORT Declared</th>
                        <th>PyPI API</th>
                        <th>ScanCode Concluded</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""

        for pkg in packages_list:
            status = self.determine_status(pkg)
            status_class = f"status-{status}"
            status_text = status.upper()

            # ORT license
            ort_license = pkg['ort_spdx']
            ort_class = 'license-noassertion' if ort_license == 'NOASSERTION' else 'license-found'

            # PyPI license
            pypi_license = pkg.get('pypi_expression') or pkg.get('pypi_license') or 'N/A'
            pypi_class = 'license-noassertion' if pypi_license in ['N/A', 'NOASSERTION'] else 'license-found'

            # ScanCode license
            scancode_license = pkg.get('scancode_concluded') or 'N/A'
            scancode_class = 'license-noassertion' if scancode_license == 'N/A' else 'license-found'

            # ScanCode details
            scancode_details = ''
            if pkg.get('scancode_licenses'):
                details = [f"{lic['license']} ({lic['count']} files)"
                          for lic in pkg['scancode_licenses'][:3]]
                scancode_details = f'<div class="scancode-details">Detected: {", ".join(details)}</div>'

            html += f"""
                    <tr data-status="{status}">
                        <td>
                            <div class="package-name">{pkg['display_name']}</div>
                            <div class="package-version">{pkg['version']}</div>
                        </td>
                        <td>{pkg['type']}</td>
                        <td class="license-cell">
                            <span class="license-badge {ort_class}">{ort_license}</span>
                        </td>
                        <td class="license-cell">
                            <span class="license-badge {pypi_class}">{pypi_license}</span>
                        </td>
                        <td class="license-cell">
                            <span class="license-badge {scancode_class}">{scancode_license}</span>
                            {scancode_details}
                        </td>
                        <td>
                            <span class="status-badge {status_class}">{status_text}</span>
                        </td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
        </div>

        <div class="legend">
            <h3>📖 Legend</h3>
            <div class="legend-items">
                <div class="legend-item">
                    <div class="legend-icon" style="background: #d1fae5;"></div>
                    <span><strong>Complete:</strong> All sources agree on license</span>
                </div>
                <div class="legend-item">
                    <div class="legend-icon" style="background: #fed7aa;"></div>
                    <span><strong>Conflict:</strong> Different licenses detected across sources</span>
                </div>
                <div class="legend-item">
                    <div class="legend-icon" style="background: #fee2e2;"></div>
                    <span><strong>Missing:</strong> No license found in any source</span>
                </div>
            </div>
            <p style="margin-top: 20px; color: #6b7280; font-size: 0.9em;">
                <strong>Data Sources:</strong><br>
                • <strong>ORT:</strong> Declared licenses from package manifests (package.json, setup.py, pom.xml, etc.)<br>
                • <strong>PyPI API:</strong> License information from Python Package Index metadata (Python packages only)<br>
                • <strong>ScanCode:</strong> License detected by deep file-level source code scanning (high confidence ≥80%)
            </p>
        </div>

        <div class="footer">
            <p>Multi-Layer License Comparison Report</p>
            <p class="ltts-branding">L&T Technology Services - Enhanced ORT Analysis System</p>
            <p style="margin-top: 10px;">Generated with ORT + PyPI API + ScanCode Toolkit + AI Curation</p>
        </div>
    </div>

    <script>
        function filterTable(filter) {
            const rows = document.querySelectorAll('#licenseTable tbody tr');
            const buttons = document.querySelectorAll('.filter-btn');

            // Update button states
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            // Filter rows
            rows.forEach(row => {
                const status = row.getAttribute('data-status');
                if (filter === 'all' || status === filter) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
"""

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ Report generated: {output_file}")
        print(f"\n📊 Summary:")
        print(f"   Total packages: {total}")
        print(f"   Complete: {complete} ({complete/total*100:.1f}%)")
        print(f"   Conflicts: {conflicts} ({conflicts/total*100:.1f}%)")
        print(f"   Missing: {missing} ({missing/total*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description='Generate multi-layer license comparison report'
    )
    parser.add_argument(
        '--ort-result',
        required=True,
        help='Path to ORT analyzer-result.yml'
    )
    parser.add_argument(
        '--pypi-results',
        help='Path to PyPI license fetch JSON (pypi-licenses-full.json)'
    )
    parser.add_argument(
        '--scancode-dir',
        help='Directory containing ScanCode JSON results'
    )
    parser.add_argument(
        '--spdx',
        help='Path to enhanced SPDX document (optional)'
    )
    parser.add_argument(
        '--uncertain-packages',
        help='Path to uncertain-packages.json (needed for accurate ScanCode matching)'
    )
    parser.add_argument(
        '--output',
        default='license-comparison.html',
        help='Output HTML file path (default: license-comparison.html)'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("MULTI-LAYER LICENSE COMPARISON REPORT GENERATOR")
    print("=" * 80)
    print("\n📂 Input Files:")
    print(f"   ORT Result: {args.ort_result}")
    print(f"   PyPI Results: {args.pypi_results or 'Not provided'}")
    print(f"   ScanCode Directory: {args.scancode_dir or 'Not provided'}")
    print(f"   Uncertain Packages: {args.uncertain_packages or 'Not provided'}")
    print(f"   SPDX Document: {args.spdx or 'Not provided'}")
    print(f"\n📄 Output File: {args.output}")
    print("\n" + "=" * 80 + "\n")

    # Create comparison object
    comparison = LicenseComparison(
        ort_result_path=args.ort_result,
        pypi_results_path=args.pypi_results,
        scancode_results_dir=args.scancode_dir,
        spdx_path=args.spdx,
        uncertain_packages_path=args.uncertain_packages
    )

    # Load data from all sources
    # IMPORTANT: Load uncertain packages BEFORE ScanCode for accurate matching
    comparison.load_ort_licenses()
    comparison.load_uncertain_packages()  # Load this first for ScanCode matching
    comparison.load_pypi_licenses()
    comparison.load_scancode_licenses()  # Now this can use uncertain packages for matching
    comparison.load_spdx_concluded()

    # Generate report
    comparison.generate_html_report(args.output)

    print("\n" + "=" * 80)
    print("✅ License comparison report generation complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
