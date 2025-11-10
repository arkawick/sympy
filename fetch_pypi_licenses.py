#!/usr/bin/env python3
"""
ORT Analyzer License Filter - PyPI License Fetcher
Identifies packages with missing licenses and attempts to fetch them from PyPI.

This script works as Stage 2.5 in the enhanced ORT pipeline:
Stage 1: ORT Analyzer
Stage 2: Extract Uncertain Packages
Stage 2.5: Fetch PyPI Licenses (THIS SCRIPT) ← NEW
Stage 3: ScanCode Deep Scan (only for packages still missing licenses)

Author: Enhanced ORT License Curation System
"""

import yaml
import requests
import json
from typing import Dict, List, Tuple, Optional
import sys
from pathlib import Path
import argparse
from datetime import datetime


class ORTLicenseAnalyzer:
    def __init__(self, yaml_file: str, output_dir: str = "pypi-licenses"):
        self.yaml_file = yaml_file
        self.output_dir = Path(output_dir)
        self.data = None
        self.missing_licenses = []
        self.pypi_fetched = []
        self.fetch_stats = {
            'total_missing': 0,
            'pypi_packages': 0,
            'non_pypi_packages': 0,
            'successfully_fetched': 0,
            'fetch_errors': 0,
            'licenses_found': 0,
            'licenses_still_missing': 0
        }

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_yaml(self) -> bool:
        """Load and parse the YAML file."""
        try:
            with open(self.yaml_file, 'r', encoding='utf-8') as f:
                self.data = yaml.safe_load(f)
            print(f"✓ Loaded ORT analyzer results from: {self.yaml_file}")
            return True
        except Exception as e:
            print(f"✗ Error loading YAML file: {e}")
            return False

    def extract_package_info(self, package: Dict) -> Tuple[str, str, List, str]:
        """Extract relevant information from a package entry."""
        pkg_id = package.get('id', '')
        purl = package.get('purl', '')
        declared_licenses = package.get('declared_licenses', [])
        declared_licenses_processed = package.get('declared_licenses_processed', {})
        spdx_expression = declared_licenses_processed.get('spdx_expression', '')

        return pkg_id, purl, declared_licenses, spdx_expression

    def is_license_missing(self, declared_licenses: List, spdx_expression: str) -> bool:
        """Check if license information is missing or empty."""
        # Check for empty or NOASSERTION licenses
        if not declared_licenses or len(declared_licenses) == 0:
            return True

        # Check for NOASSERTION, UNKNOWN, NONE
        uncertain_values = ['NOASSERTION', 'UNKNOWN', 'NONE', '']
        if all(lic in uncertain_values for lic in declared_licenses):
            return True

        # Check SPDX expression
        if not spdx_expression or spdx_expression in uncertain_values:
            return True

        return False

    def find_missing_licenses(self) -> List[Dict]:
        """Find all packages with missing license information."""
        if not self.data or 'analyzer' not in self.data:
            print("✗ Invalid YAML structure - missing 'analyzer' section")
            return []

        packages = self.data.get('analyzer', {}).get('result', {}).get('packages', [])
        print(f"📦 Analyzing {len(packages)} packages from ORT results...")

        for package in packages:
            pkg_id, purl, declared_licenses, spdx_expression = self.extract_package_info(package)

            if self.is_license_missing(declared_licenses, spdx_expression):
                self.missing_licenses.append({
                    'id': pkg_id,
                    'purl': purl,
                    'declared_licenses': declared_licenses,
                    'spdx_expression': spdx_expression,
                    'homepage_url': package.get('homepage_url', ''),
                    'description': package.get('description', ''),
                    'source_artifact_url': package.get('source_artifact', {}).get('url', ''),
                    'vcs_url': package.get('vcs', {}).get('url', ''),
                    'vcs_type': package.get('vcs', {}).get('type', '')
                })

        self.fetch_stats['total_missing'] = len(self.missing_licenses)
        print(f"🔍 Found {len(self.missing_licenses)} packages with missing/uncertain licenses")
        return self.missing_licenses

    def _parse_license_from_classifier(self, classifier: str) -> str:
        """
        Parse PyPI classifier to extract SPDX license identifier.

        Example classifiers:
        - "License :: OSI Approved :: BSD License" → "BSD-3-Clause"
        - "License :: OSI Approved :: MIT License" → "MIT"
        - "License :: OSI Approved :: Apache Software License" → "Apache-2.0"
        """
        classifier_lower = classifier.lower()

        # Common PyPI classifier → SPDX mappings
        mappings = {
            'mit license': 'MIT',
            'apache software license': 'Apache-2.0',
            'bsd license': 'BSD-3-Clause',
            'gnu general public license (gpl)': 'GPL-3.0-or-later',
            'gnu general public license v2 (gplv2)': 'GPL-2.0-only',
            'gnu general public license v3 (gplv3)': 'GPL-3.0-only',
            'gnu lesser general public license v2 (lgplv2)': 'LGPL-2.1-only',
            'gnu lesser general public license v3 (lgplv3)': 'LGPL-3.0-only',
            'mozilla public license 2.0 (mpl 2.0)': 'MPL-2.0',
            'python software foundation license': 'PSF-2.0',
            'isc license (iscl)': 'ISC',
            'zope public license': 'ZPL-2.1',
        }

        # Try to match against known patterns
        for pattern, spdx_id in mappings.items():
            if pattern in classifier_lower:
                return spdx_id

        # Fallback: extract the last part of the classifier
        # "License :: OSI Approved :: BSD License" → "BSD License"
        parts = classifier.split('::')
        if len(parts) >= 3:
            license_name = parts[-1].strip()
            # Remove "License" suffix if present
            license_name = license_name.replace(' License', '').replace(' license', '').strip()
            return license_name

        return ''

    def fetch_pypi_license(self, package_name: str, version: str) -> Dict:
        """Fetch license information from PyPI API."""
        url = f"https://pypi.org/pypi/{package_name}/{version}/json"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            info = data.get('info', {})

            # Try multiple fields for license information
            license_expression = info.get('license_expression', '')
            license_info = info.get('license', '')
            classifiers = info.get('classifiers', [])

            # Extract license from classifiers
            license_classifiers = [c for c in classifiers if c.startswith('License ::')]

            # Try to parse SPDX license from classifiers
            classifier_license = ''
            if license_classifiers:
                classifier_license = self._parse_license_from_classifier(license_classifiers[0])

            # Determine the best license info (priority order)
            determined_license = license_expression or license_info or classifier_license or ''

            # Clean up common non-informative values
            if determined_license.lower() in ['unknown', 'none', '', 'n/a']:
                determined_license = ''

            return {
                'license': determined_license,
                'license_expression': license_expression,
                'license_field': license_info,
                'classifier_license': classifier_license,
                'classifiers': license_classifiers,
                'home_page': info.get('home_page', ''),
                'project_urls': info.get('project_urls', {}),
                'package_url': info.get('package_url', ''),
                'success': True
            }
        except requests.exceptions.RequestException as e:
            return {'error': str(e), 'success': False}

    def parse_package_id(self, pkg_id: str) -> Tuple[str, str, str]:
        """Parse package ID to extract ecosystem, name, and version."""
        # Format: "PyPI::package-name:version"
        parts = pkg_id.split('::')
        if len(parts) >= 2:
            ecosystem = parts[0]
            name_version = parts[1].rsplit(':', 1)
            if len(name_version) == 2:
                return ecosystem, name_version[0], name_version[1]
        return '', '', ''

    def enrich_missing_licenses(self):
        """Attempt to fetch license information for PyPI packages with missing licenses."""
        print(f"\n🌐 Fetching license information from PyPI API...\n")

        for pkg in self.missing_licenses:
            ecosystem, name, version = self.parse_package_id(pkg['id'])

            if ecosystem == 'PyPI' and name and version:
                self.fetch_stats['pypi_packages'] += 1
                print(f"  → Fetching: {name}:{version}...", end=' ')

                license_info = self.fetch_pypi_license(name, version)
                pkg['fetched_license'] = license_info

                if license_info.get('success'):
                    self.fetch_stats['successfully_fetched'] += 1
                    if license_info.get('license'):
                        self.fetch_stats['licenses_found'] += 1
                        self.pypi_fetched.append(pkg)
                        print(f"✓ Found: {license_info['license']}")
                    else:
                        self.fetch_stats['licenses_still_missing'] += 1
                        print("⚠ No license info in PyPI metadata")
                else:
                    self.fetch_stats['fetch_errors'] += 1
                    print(f"✗ Error: {license_info.get('error', 'Unknown')}")
            else:
                self.fetch_stats['non_pypi_packages'] += 1
                pkg['fetched_license'] = {'error': f'Non-PyPI package ({ecosystem})', 'success': False}

        print(f"\n✓ PyPI API fetch complete")

    def print_report(self):
        """Print a formatted report of packages with missing licenses."""
        print("\n" + "=" * 80)
        print("PYPI LICENSE FETCH REPORT")
        print("=" * 80)
        print(f"\n📊 Statistics:")
        print(f"   Total packages with missing licenses: {self.fetch_stats['total_missing']}")
        print(f"   PyPI packages: {self.fetch_stats['pypi_packages']}")
        print(f"   Non-PyPI packages: {self.fetch_stats['non_pypi_packages']}")
        print(f"   Successfully fetched from PyPI: {self.fetch_stats['successfully_fetched']}")
        print(f"   Licenses found in PyPI: {self.fetch_stats['licenses_found']}")
        print(f"   Still missing after PyPI fetch: {self.fetch_stats['licenses_still_missing']}")
        print(f"   Fetch errors: {self.fetch_stats['fetch_errors']}")

        if self.pypi_fetched:
            print(f"\n✅ Packages with licenses found in PyPI ({len(self.pypi_fetched)}):\n")
            for i, pkg in enumerate(self.pypi_fetched, 1):
                print(f"{i}. {pkg['id']}")
                fetched = pkg['fetched_license']
                print(f"   License: {fetched.get('license', 'N/A')}")
                if fetched.get('classifiers'):
                    print(f"   Classifiers:")
                    for classifier in fetched['classifiers'][:3]:  # Show first 3
                        print(f"      - {classifier}")
                print()

        still_missing = [p for p in self.missing_licenses if not p.get('fetched_license', {}).get('license')]
        if still_missing:
            print(f"\n⚠ Packages still needing ScanCode analysis ({len(still_missing)}):")
            for i, pkg in enumerate(still_missing[:10], 1):  # Show first 10
                ecosystem, name, version = self.parse_package_id(pkg['id'])
                print(f"   {i}. {name}:{version} ({ecosystem})")
            if len(still_missing) > 10:
                print(f"   ... and {len(still_missing) - 10} more")

    def export_to_json(self, output_file: Optional[str] = None):
        """Export the missing licenses report to JSON."""
        if output_file is None:
            output_file = self.output_dir / "pypi-licenses-full.json"
        else:
            output_file = Path(output_file)

        export_data = {
            'generated_at': datetime.now().isoformat(),
            'ort_analyzer_file': str(self.yaml_file),
            'statistics': self.fetch_stats,
            'packages': self.missing_licenses
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        print(f"\n💾 Full report exported to: {output_file}")

    def export_pypi_found(self, output_file: Optional[str] = None):
        """Export only packages with licenses found in PyPI."""
        if output_file is None:
            output_file = self.output_dir / "pypi-licenses-found.json"
        else:
            output_file = Path(output_file)

        export_data = {
            'generated_at': datetime.now().isoformat(),
            'ort_analyzer_file': str(self.yaml_file),
            'count': len(self.pypi_fetched),
            'packages': self.pypi_fetched
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        print(f"💾 PyPI found licenses exported to: {output_file}")

    def export_to_csv(self, output_file: Optional[str] = None):
        """Export the missing licenses report to CSV."""
        import csv

        if output_file is None:
            output_file = self.output_dir / "pypi-licenses.csv"
        else:
            output_file = Path(output_file)

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if not self.missing_licenses:
                return

            fieldnames = ['id', 'ecosystem', 'name', 'version', 'purl',
                         'declared_licenses', 'spdx_expression',
                         'fetched_license', 'fetched_classifiers', 'status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for pkg in self.missing_licenses:
                ecosystem, name, version = self.parse_package_id(pkg['id'])

                row = {
                    'id': pkg['id'],
                    'ecosystem': ecosystem,
                    'name': name,
                    'version': version,
                    'purl': pkg['purl'],
                    'declared_licenses': ', '.join(str(x) for x in pkg['declared_licenses']) if pkg['declared_licenses'] else '',
                    'spdx_expression': pkg['spdx_expression'],
                    'fetched_license': '',
                    'fetched_classifiers': '',
                    'status': 'NOT_CHECKED'
                }

                if 'fetched_license' in pkg:
                    fetched = pkg['fetched_license']
                    if fetched.get('success') and fetched.get('license'):
                        row['fetched_license'] = fetched.get('license', '')
                        row['fetched_classifiers'] = '; '.join(fetched.get('classifiers', []))
                        row['status'] = 'FOUND_IN_PYPI'
                    elif fetched.get('success'):
                        row['status'] = 'PYPI_NO_LICENSE'
                    else:
                        row['status'] = 'FETCH_ERROR' if ecosystem == 'PyPI' else 'NON_PYPI'

                writer.writerow(row)

        print(f"💾 CSV report exported to: {output_file}")

    def export_curation_suggestions(self, output_file: Optional[str] = None):
        """Export curation suggestions for packages found in PyPI."""
        if output_file is None:
            output_file = self.output_dir / "curation-suggestions.yml"
        else:
            output_file = Path(output_file)

        curations = []
        for pkg in self.pypi_fetched:
            fetched = pkg['fetched_license']
            if fetched.get('license'):
                curation = {
                    'id': pkg['id'],
                    'curations': {
                        'comment': f"License fetched from PyPI API on {datetime.now().strftime('%Y-%m-%d')}. "
                                  f"License: {fetched['license']}. "
                                  f"⚠️ REVIEW REQUIRED - Verify from source repository before applying!",
                        'concluded_license': fetched['license'],
                        'declared_license_mapping': {
                            'NOASSERTION': fetched['license']
                        },
                        'homepage_url': fetched.get('home_page', ''),
                        'pypi_classifiers': fetched.get('classifiers', [])
                    }
                }
                curations.append(curation)

        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(curations, f, default_flow_style=False, sort_keys=False)

        print(f"💾 Curation suggestions exported to: {output_file}")
        print(f"⚠️  IMPORTANT: Review and verify all suggestions before using!")

    def export_stats(self, output_file: Optional[str] = None):
        """Export statistics summary."""
        if output_file is None:
            output_file = self.output_dir / "pypi-fetch-stats.txt"
        else:
            output_file = Path(output_file)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("PyPI License Fetch Statistics\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"ORT Analyzer File: {self.yaml_file}\n\n")
            f.write("Statistics:\n")
            for key, value in self.fetch_stats.items():
                f.write(f"  {key.replace('_', ' ').title()}: {value}\n")

            reduction_percentage = 0
            if self.fetch_stats['total_missing'] > 0:
                reduction_percentage = (self.fetch_stats['licenses_found'] / self.fetch_stats['total_missing']) * 100

            f.write(f"\nScanCode Workload Reduction: {reduction_percentage:.1f}%\n")
            f.write(f"Packages still needing ScanCode: {self.fetch_stats['licenses_still_missing']}\n")

        print(f"💾 Statistics exported to: {output_file}")

    def export_to_html(self, output_file: Optional[str] = None):
        """Export beautiful HTML report of PyPI license fetch results."""
        if output_file is None:
            output_file = self.output_dir / "pypi-licenses-report.html"
        else:
            output_file = Path(output_file)

        # Calculate statistics
        reduction_percentage = 0
        if self.fetch_stats['total_missing'] > 0:
            reduction_percentage = (self.fetch_stats['licenses_found'] / self.fetch_stats['total_missing']) * 100

        success_rate = 0
        if self.fetch_stats['pypi_packages'] > 0:
            success_rate = (self.fetch_stats['licenses_found'] / self.fetch_stats['pypi_packages']) * 100

        # Separate packages by status
        found_packages = []
        still_missing = []
        non_pypi = []

        for pkg in self.missing_licenses:
            ecosystem, name, version = self.parse_package_id(pkg['id'])

            if ecosystem != 'PyPI':
                non_pypi.append(pkg)
            elif pkg.get('fetched_license', {}).get('license'):
                found_packages.append(pkg)
            else:
                still_missing.append(pkg)

        # Generate HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyPI License Fetch Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}

        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }}

        .stat-card.success {{
            border-left-color: #10b981;
        }}

        .stat-card.warning {{
            border-left-color: #f59e0b;
        }}

        .stat-card.info {{
            border-left-color: #3b82f6;
        }}

        .stat-number {{
            font-size: 2.5em;
            font-weight: 700;
            color: #1f2937;
            margin: 10px 0;
        }}

        .stat-label {{
            color: #6b7280;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .content {{
            padding: 40px;
        }}

        h2 {{
            color: #1f2937;
            margin: 30px 0 20px;
            font-size: 1.8em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}

        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}

        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e5e7eb;
        }}

        tbody tr:hover {{
            background: #f9fafb;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .badge.success {{
            background: #d1fae5;
            color: #065f46;
        }}

        .badge.warning {{
            background: #fef3c7;
            color: #92400e;
        }}

        .badge.error {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .badge.info {{
            background: #dbeafe;
            color: #1e40af;
        }}

        .license-tag {{
            font-family: 'Courier New', monospace;
            background: #f3f4f6;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.9em;
        }}

        .link {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}

        .link:hover {{
            text-decoration: underline;
        }}

        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: #6b7280;
        }}

        .empty-state svg {{
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
            opacity: 0.5;
        }}

        footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #6b7280;
            border-top: 1px solid #e5e7eb;
        }}

        .progress-bar {{
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #10b981 0%, #059669 100%);
            transition: width 0.3s ease;
        }}

        .classifiers {{
            font-size: 0.85em;
            color: #6b7280;
            margin-top: 5px;
        }}

        .package-name {{
            font-weight: 600;
            color: #1f2937;
        }}

        .version {{
            color: #6b7280;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌐 PyPI License Fetch Report</h1>
            <p class="subtitle">Fast License Retrieval from Python Package Index</p>
            <p class="subtitle">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>

        <div class="stats-grid">
            <div class="stat-card info">
                <div class="stat-label">Total Packages Analyzed</div>
                <div class="stat-number">{self.fetch_stats['total_missing']}</div>
            </div>

            <div class="stat-card success">
                <div class="stat-label">Licenses Found in PyPI</div>
                <div class="stat-number">{self.fetch_stats['licenses_found']}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {success_rate}%"></div>
                </div>
                <div style="font-size: 0.9em; margin-top: 5px;">Success Rate: {success_rate:.1f}%</div>
            </div>

            <div class="stat-card warning">
                <div class="stat-label">Still Missing</div>
                <div class="stat-number">{self.fetch_stats['licenses_still_missing']}</div>
                <div style="font-size: 0.9em; margin-top: 5px;">Require ScanCode analysis</div>
            </div>

            <div class="stat-card success">
                <div class="stat-label">Workload Reduction</div>
                <div class="stat-number">{reduction_percentage:.1f}%</div>
                <div style="font-size: 0.9em; margin-top: 5px;">Fewer packages to scan</div>
            </div>
        </div>

        <div class="content">
"""

        # Licenses Found Section
        if found_packages:
            html += f"""
            <h2>✅ Licenses Found in PyPI ({len(found_packages)} packages)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Package</th>
                        <th>Version</th>
                        <th>License Found</th>
                        <th>Source</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
"""
            for pkg in found_packages:
                ecosystem, name, version = self.parse_package_id(pkg['id'])
                fetched = pkg.get('fetched_license', {})
                license_info = fetched.get('license', 'N/A')
                license_expr = fetched.get('license_expression', '')
                classifiers = fetched.get('classifiers', [])

                # Determine source
                source = "license_expression" if license_expr else "license field"
                if classifiers and not license_expr:
                    source = "classifiers"

                pypi_url = f"https://pypi.org/project/{name}/{version}/"

                html += f"""
                    <tr>
                        <td><span class="package-name">{name}</span></td>
                        <td><span class="version">{version}</span></td>
                        <td>
                            <span class="license-tag">{license_info}</span>
                            {'<div class="classifiers">' + '<br>'.join(classifiers[:2]) + '</div>' if classifiers else ''}
                        </td>
                        <td><span class="badge info">{source}</span></td>
                        <td><a href="{pypi_url}" target="_blank" class="link">View on PyPI</a></td>
                    </tr>
"""

            html += """
                </tbody>
            </table>
"""

        # Still Missing Section
        if still_missing:
            html += f"""
            <h2>⚠️ Packages Still Missing Licenses ({len(still_missing)} packages)</h2>
            <p style="color: #6b7280; margin-bottom: 20px;">These PyPI packages need ScanCode analysis or manual verification.</p>
            <table>
                <thead>
                    <tr>
                        <th>Package</th>
                        <th>Version</th>
                        <th>Status</th>
                        <th>Homepage</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
"""
            for pkg in still_missing:
                ecosystem, name, version = self.parse_package_id(pkg['id'])
                fetched = pkg.get('fetched_license', {})
                error = fetched.get('error', 'No license in PyPI metadata')
                homepage = pkg.get('homepage_url', '')
                pypi_url = f"https://pypi.org/project/{name}/{version}/"

                html += f"""
                    <tr>
                        <td><span class="package-name">{name}</span></td>
                        <td><span class="version">{version}</span></td>
                        <td><span class="badge warning">Missing</span></td>
                        <td>{f'<a href="{homepage}" target="_blank" class="link">Homepage</a>' if homepage else '-'}</td>
                        <td><a href="{pypi_url}" target="_blank" class="link">View on PyPI</a></td>
                    </tr>
"""

            html += """
                </tbody>
            </table>
"""

        # Non-PyPI Packages Section
        if non_pypi:
            html += f"""
            <h2>ℹ️ Non-PyPI Packages ({len(non_pypi)} packages)</h2>
            <p style="color: #6b7280; margin-bottom: 20px;">These packages are from other ecosystems and were not checked via PyPI API.</p>
            <table>
                <thead>
                    <tr>
                        <th>Package ID</th>
                        <th>Ecosystem</th>
                        <th>Note</th>
                    </tr>
                </thead>
                <tbody>
"""
            for pkg in non_pypi[:20]:  # Limit to first 20 to avoid huge tables
                ecosystem, name, version = self.parse_package_id(pkg['id'])

                html += f"""
                    <tr>
                        <td><span class="package-name">{name}:{version}</span></td>
                        <td><span class="badge info">{ecosystem}</span></td>
                        <td>Requires ScanCode or ecosystem-specific check</td>
                    </tr>
"""

            if len(non_pypi) > 20:
                html += f"""
                    <tr>
                        <td colspan="3" style="text-align: center; color: #6b7280; font-style: italic;">
                            ... and {len(non_pypi) - 20} more non-PyPI packages
                        </td>
                    </tr>
"""

            html += """
                </tbody>
            </table>
"""

        # Summary Section
        html += f"""
            <h2>📊 Summary & Next Steps</h2>
            <div style="background: #f9fafb; padding: 30px; border-radius: 8px; border-left: 4px solid #667eea;">
                <h3 style="margin-bottom: 15px; color: #1f2937;">Key Findings:</h3>
                <ul style="line-height: 2; color: #374151;">
                    <li><strong>{self.fetch_stats['licenses_found']}</strong> licenses successfully retrieved from PyPI</li>
                    <li><strong>{reduction_percentage:.1f}%</strong> reduction in ScanCode workload</li>
                    <li><strong>{self.fetch_stats['licenses_still_missing']}</strong> packages still require deeper analysis</li>
                    <li><strong>{self.fetch_stats['non_pypi_packages']}</strong> non-PyPI packages (NPM, Maven, etc.)</li>
                </ul>

                <h3 style="margin: 25px 0 15px; color: #1f2937;">Recommended Actions:</h3>
                <ol style="line-height: 2; color: #374151;">
                    <li><strong>Review Found Licenses:</strong> Verify accuracy from PyPI metadata</li>
                    <li><strong>Apply Curations:</strong> Use <code>curation-suggestions.yml</code> after manual verification</li>
                    <li><strong>Run ScanCode:</strong> For {self.fetch_stats['licenses_still_missing']} remaining packages</li>
                    <li><strong>Manual Verification:</strong> Check GitHub repositories for packages with missing licenses</li>
                </ol>

                <div style="margin-top: 20px; padding: 15px; background: #fef3c7; border-radius: 6px; border-left: 4px solid #f59e0b;">
                    <strong>⚠️ Important:</strong> Always verify PyPI license information manually before applying curations.
                    Package metadata may be incomplete or incorrect.
                </div>
            </div>
        </div>

        <footer>
            <p><strong>Enhanced ORT License Curation System</strong></p>
            <p style="margin-top: 10px;">PyPI API License Fetcher - Fast, automated license retrieval for Python packages</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Generated from: {self.yaml_file}</p>
        </footer>
    </div>
</body>
</html>
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"💾 HTML report exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Fetch missing license information from PyPI API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - analyze and fetch
  python fetch_pypi_licenses.py ort-results/analyzer/analyzer-result.yml --fetch

  # Fetch and export all formats
  python fetch_pypi_licenses.py ort-results/analyzer/analyzer-result.yml --fetch --json --csv --curations

  # Custom output directory
  python fetch_pypi_licenses.py analyzer-result.yml --fetch --output-dir my-pypi-results
        """
    )

    parser.add_argument('yaml_file', help='Path to ORT analyzer-result.yml file')
    parser.add_argument('--fetch', action='store_true',
                       help='Attempt to fetch missing licenses from PyPI')
    parser.add_argument('--json', action='store_true',
                       help='Export full report to JSON file')
    parser.add_argument('--csv', action='store_true',
                       help='Export report to CSV file')
    parser.add_argument('--curations', action='store_true',
                       help='Generate curation suggestions YAML (requires manual review!)')
    parser.add_argument('--html', action='store_true',
                       help='Export beautiful HTML report')
    parser.add_argument('--output-dir', default='pypi-licenses',
                       help='Output directory for reports (default: pypi-licenses)')

    args = parser.parse_args()

    if not Path(args.yaml_file).exists():
        print(f"✗ Error: File '{args.yaml_file}' not found")
        sys.exit(1)

    analyzer = ORTLicenseAnalyzer(args.yaml_file, args.output_dir)

    print("🚀 ORT PyPI License Fetcher - Stage 2.5")
    print("=" * 80)

    if not analyzer.load_yaml():
        sys.exit(1)

    print("🔍 Analyzing packages for missing licenses...")
    analyzer.find_missing_licenses()

    if args.fetch:
        analyzer.enrich_missing_licenses()

    analyzer.print_report()

    # Always export stats
    analyzer.export_stats()

    if args.json:
        analyzer.export_to_json()
        analyzer.export_pypi_found()

    if args.csv:
        analyzer.export_to_csv()

    if args.curations and analyzer.pypi_fetched:
        analyzer.export_curation_suggestions()

    if args.html:
        analyzer.export_to_html()

    print("\n✅ PyPI license fetch complete!")
    print(f"📁 All outputs saved to: {analyzer.output_dir}/")


if __name__ == "__main__":
    main()
