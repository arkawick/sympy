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

            # Determine the best license info
            determined_license = license_expression or license_info or ''

            # Clean up common non-informative values
            if determined_license.lower() in ['unknown', 'none', '', 'n/a']:
                determined_license = ''

            return {
                'license': determined_license,
                'license_expression': license_expression,
                'license_field': license_info,
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

    print("\n✅ PyPI license fetch complete!")
    print(f"📁 All outputs saved to: {analyzer.output_dir}/")


if __name__ == "__main__":
    main()
