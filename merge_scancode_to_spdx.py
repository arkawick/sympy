#!/usr/bin/env python3
"""
Merge ScanCode Toolkit license detection results into SPDX documents.
Enhances SPDX documents by adding license information found by ScanCode
for packages where ORT couldn't determine the license.
"""

import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict


class ScanCodeSPDXMerger:
    """Merges ScanCode findings into SPDX documents"""

    def __init__(self, spdx_path: str, scancode_dir: str, output_path: str):
        self.spdx_path = Path(spdx_path)
        self.scancode_dir = Path(scancode_dir)
        self.output_path = Path(output_path)

        self.spdx_doc = None
        self.scancode_results = {}
        self.merge_stats = {
            'packages_checked': 0,
            'packages_enhanced': 0,
            'licenses_added': 0,
            'uncertain_resolved': 0
        }

    def load_spdx_document(self) -> dict:
        """Load SPDX document (supports YAML and JSON)"""
        print(f"📖 Loading SPDX document from: {self.spdx_path}")

        with open(self.spdx_path, 'r') as f:
            if self.spdx_path.suffix in ['.yml', '.yaml']:
                doc = yaml.safe_load(f)
            else:
                doc = json.load(f)

        packages_count = len(doc.get('packages', []))
        print(f"   Found {packages_count} packages in SPDX document")
        return doc

    def load_scancode_results(self) -> Dict[str, Dict]:
        """Load all ScanCode JSON results from directory"""
        print(f"\n📖 Loading ScanCode results from: {self.scancode_dir}")

        if not self.scancode_dir.exists():
            print(f"   ⚠️  Directory not found: {self.scancode_dir}")
            return {}

        scancode_files = list(self.scancode_dir.glob('*.json'))
        print(f"   Found {len(scancode_files)} ScanCode result files")

        results = {}

        for scancode_file in scancode_files:
            try:
                with open(scancode_file, 'r') as f:
                    scancode_data = json.load(f)

                # Extract package name from filename
                # Expected format: package-name-version.json
                package_name = scancode_file.stem

                # Analyze ScanCode results
                license_info = self._analyze_scancode_result(scancode_data)

                if license_info['licenses']:
                    results[package_name] = license_info
                    print(f"   ✓ {package_name}: {len(license_info['licenses'])} licenses detected")

            except Exception as e:
                print(f"   ✗ Error processing {scancode_file.name}: {e}")

        print(f"\n   Total packages with ScanCode data: {len(results)}")
        return results

    def _analyze_scancode_result(self, scancode_data: dict) -> Dict:
        """Analyze ScanCode JSON result and extract license information"""
        license_detections = defaultdict(lambda: {'count': 0, 'score': 0.0, 'files': []})

        # Process all scanned files
        for file_info in scancode_data.get('files', []):
            # Skip directories
            if file_info.get('type') != 'file':
                continue

            file_path = file_info.get('path', '')

            # Extract license information
            for license_match in file_info.get('licenses', []):
                license_key = license_match.get('key', '')
                license_spdx = license_match.get('spdx_license_key', license_key)
                score = license_match.get('score', 0.0)

                if license_spdx and score >= 80:  # Only high-confidence matches
                    license_detections[license_spdx]['count'] += 1
                    license_detections[license_spdx]['score'] = max(
                        license_detections[license_spdx]['score'], score
                    )
                    license_detections[license_spdx]['files'].append(file_path)

        # Determine primary licenses (appear in multiple files)
        primary_licenses = []
        secondary_licenses = []

        for license_id, info in license_detections.items():
            if info['count'] >= 3 or info['score'] >= 95:
                primary_licenses.append(license_id)
            else:
                secondary_licenses.append(license_id)

        return {
            'licenses': primary_licenses,
            'secondary_licenses': secondary_licenses,
            'all_detections': dict(license_detections),
            'file_count': len([f for f in scancode_data.get('files', []) if f.get('type') == 'file'])
        }

    def normalize_package_name(self, name: str) -> Set[str]:
        """Generate possible package name variations for matching"""
        variations = {name}

        # Add variations
        variations.add(name.lower())
        variations.add(name.replace('-', '_'))
        variations.add(name.replace('_', '-'))
        variations.add(name.replace('.', '-'))

        return variations

    def find_scancode_data(self, package_name: str) -> Dict:
        """Find ScanCode data for a package by name (with fuzzy matching)"""
        # Try exact match first
        if package_name in self.scancode_results:
            return self.scancode_results[package_name]

        # Try variations
        variations = self.normalize_package_name(package_name)
        for variation in variations:
            if variation in self.scancode_results:
                return self.scancode_results[variation]

        # Try partial match
        for scancode_pkg in self.scancode_results.keys():
            if package_name.lower() in scancode_pkg.lower() or scancode_pkg.lower() in package_name.lower():
                return self.scancode_results[scancode_pkg]

        return {}

    def merge_results(self):
        """Merge ScanCode findings into SPDX document"""
        print(f"\n🔄 Merging ScanCode results into SPDX document...")

        enhanced_packages = []

        for package in self.spdx_doc.get('packages', []):
            self.merge_stats['packages_checked'] += 1

            pkg_name = package.get('name', '')
            pkg_spdx_id = package.get('SPDXID', '')
            license_concluded = package.get('licenseConcluded', 'NOASSERTION')
            license_declared = package.get('licenseDeclared', 'NOASSERTION')

            # Check if this package needs enhancement
            needs_enhancement = (
                license_concluded in ['NOASSERTION', 'NONE', 'UNKNOWN', ''] or
                license_declared in ['NOASSERTION', 'NONE', 'UNKNOWN', '']
            )

            if needs_enhancement:
                # Try to find ScanCode data
                scancode_data = self.find_scancode_data(pkg_name)

                if scancode_data and scancode_data.get('licenses'):
                    licenses = scancode_data['licenses']
                    secondary = scancode_data.get('secondary_licenses', [])
                    file_count = scancode_data.get('file_count', 0)

                    # Build license expression
                    if len(licenses) == 1:
                        license_expression = licenses[0]
                    else:
                        # Multiple licenses - create OR expression
                        license_expression = ' OR '.join(sorted(licenses))

                    # Add or update license information
                    if license_concluded in ['NOASSERTION', 'NONE', 'UNKNOWN', '']:
                        package['licenseConcluded'] = license_expression
                        self.merge_stats['licenses_added'] += 1

                    # Add detailed comment
                    comment_parts = [
                        f"License detected by ScanCode Toolkit from {file_count} source files.",
                        f"Primary licenses: {', '.join(sorted(licenses))}"
                    ]

                    if secondary:
                        comment_parts.append(f"Secondary licenses found: {', '.join(sorted(secondary))}")

                    package['licenseComments'] = ' '.join(comment_parts)

                    # Add license info to package
                    if 'licenseInfoFromFiles' not in package:
                        package['licenseInfoFromFiles'] = []

                    package['licenseInfoFromFiles'].extend(licenses)
                    package['licenseInfoFromFiles'] = list(set(package['licenseInfoFromFiles']))  # Deduplicate

                    self.merge_stats['packages_enhanced'] += 1
                    self.merge_stats['uncertain_resolved'] += 1

                    print(f"   ✓ Enhanced {pkg_name}: {license_expression}")

            enhanced_packages.append(package)

        self.spdx_doc['packages'] = enhanced_packages

    def save_enhanced_spdx(self):
        """Save enhanced SPDX document"""
        print(f"\n💾 Saving enhanced SPDX document to: {self.output_path}")

        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_path, 'w') as f:
            if self.output_path.suffix in ['.yml', '.yaml']:
                yaml.dump(self.spdx_doc, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(self.spdx_doc, f, indent=2)

        print(f"   ✅ Enhanced SPDX document saved successfully")

    def generate_merge_report(self):
        """Generate a detailed merge report"""
        report_path = self.output_path.parent / 'merge-report.md'

        with open(report_path, 'w') as f:
            f.write("# ScanCode to SPDX Merge Report\n\n")
            f.write("## Summary\n\n")
            f.write(f"- **Packages checked**: {self.merge_stats['packages_checked']}\n")
            f.write(f"- **Packages enhanced**: {self.merge_stats['packages_enhanced']}\n")
            f.write(f"- **Licenses added**: {self.merge_stats['licenses_added']}\n")
            f.write(f"- **Uncertain licenses resolved**: {self.merge_stats['uncertain_resolved']}\n\n")

            enhancement_rate = (self.merge_stats['packages_enhanced'] / self.merge_stats['packages_checked'] * 100) if self.merge_stats['packages_checked'] > 0 else 0
            f.write(f"**Enhancement Rate**: {enhancement_rate:.1f}%\n\n")

            f.write("## Process\n\n")
            f.write("1. Loaded SPDX document from ORT reporter\n")
            f.write("2. Loaded ScanCode results for uncertain packages\n")
            f.write("3. Matched packages by name (with fuzzy matching)\n")
            f.write("4. Merged high-confidence license detections (score ≥ 80%)\n")
            f.write("5. Updated SPDX licenseConcluded and licenseComments fields\n\n")

            f.write("## Quality Criteria\n\n")
            f.write("- Only licenses detected with ≥80% confidence are included\n")
            f.write("- Primary licenses appear in ≥3 files or have ≥95% confidence\n")
            f.write("- Multiple licenses are combined with OR operator\n\n")

            f.write("## Next Steps\n\n")
            f.write("1. Validate enhanced SPDX document with: `pyspdxtools -i enhanced-spdx.json --validate`\n")
            f.write("2. Review packages that still have NOASSERTION for manual curation\n")
            f.write("3. Use enhanced SPDX as input for AI curation analysis\n")

        print(f"   📊 Merge report saved to: {report_path}")

    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "="*70)
        print("📊 MERGE SUMMARY")
        print("="*70)
        print(f"SPDX packages checked: {self.merge_stats['packages_checked']}")
        print(f"Packages enhanced with ScanCode data: {self.merge_stats['packages_enhanced']}")
        print(f"Licenses added: {self.merge_stats['licenses_added']}")
        print(f"Uncertain licenses resolved: {self.merge_stats['uncertain_resolved']}")

        if self.merge_stats['packages_checked'] > 0:
            enhancement_rate = self.merge_stats['packages_enhanced'] / self.merge_stats['packages_checked'] * 100
            print(f"\nEnhancement rate: {enhancement_rate:.1f}%")

        print("="*70)

    def run(self):
        """Execute the complete merge workflow"""
        self.spdx_doc = self.load_spdx_document()
        self.scancode_results = self.load_scancode_results()

        if not self.scancode_results:
            print("\n⚠️  No ScanCode results found. Merge aborted.")
            print("   Run ScanCode on uncertain packages first:")
            print("   scancode -l -c --json output.json /path/to/package")
            return False

        self.merge_results()
        self.save_enhanced_spdx()
        self.generate_merge_report()
        self.print_summary()

        return True


def main():
    parser = argparse.ArgumentParser(
        description='Merge ScanCode license detections into SPDX documents'
    )
    parser.add_argument(
        '--spdx',
        required=True,
        help='Path to input SPDX document (YAML or JSON)'
    )
    parser.add_argument(
        '--scancode',
        required=True,
        help='Directory containing ScanCode JSON results'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Path for output enhanced SPDX document'
    )

    args = parser.parse_args()

    merger = ScanCodeSPDXMerger(args.spdx, args.scancode, args.output)
    success = merger.run()

    if success:
        print(f"\n✅ Merge completed successfully!")
        print(f"   Enhanced SPDX: {args.output}")
    else:
        print(f"\n❌ Merge failed. Check errors above.")
        exit(1)


if __name__ == '__main__':
    main()
