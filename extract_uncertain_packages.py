#!/usr/bin/env python3
"""
Extract packages with missing, uncertain, or NOASSERTION licenses from ORT results.
This helps identify which packages need deeper analysis with ScanCode.
"""

import yaml
import json
import argparse
from pathlib import Path
from typing import List, Dict, Set


class UncertainPackageExtractor:
    """Extracts packages with uncertain license information from ORT results"""

    # License values that indicate uncertainty
    UNCERTAIN_LICENSES = {
        'NOASSERTION',
        'NONE',
        'UNKNOWN',
        'NOT-FOUND',
        '',
        'NULL'
    }

    def __init__(self, ort_result_path: str, output_dir: str = 'uncertain-packages'):
        self.ort_result_path = Path(ort_result_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.uncertain_packages = []
        self.stats = {
            'total_packages': 0,
            'uncertain_declared': 0,
            'uncertain_concluded': 0,
            'no_license_info': 0,
            'multiple_licenses': 0
        }

    def load_ort_results(self) -> dict:
        """Load ORT analyzer results from YAML file"""
        with open(self.ort_result_path, 'r') as f:
            return yaml.safe_load(f)

    def is_uncertain_license(self, license_expr: str) -> bool:
        """Check if a license expression indicates uncertainty"""
        if not license_expr:
            return True

        license_upper = str(license_expr).strip().upper()
        return license_upper in self.UNCERTAIN_LICENSES

    def extract_uncertain_packages(self) -> List[Dict]:
        """Extract packages with uncertain licenses from ORT results"""
        print(f"📖 Loading ORT results from: {self.ort_result_path}")
        ort_data = self.load_ort_results()

        # Navigate ORT result structure
        analyzer_result = ort_data.get('analyzer', {}).get('result', {})
        packages = analyzer_result.get('packages', [])

        self.stats['total_packages'] = len(packages)
        print(f"📦 Found {len(packages)} total packages in ORT results\n")

        for package in packages:
            pkg_id = package.get('id', 'unknown')
            declared_licenses = package.get('declared_licenses', [])
            concluded_license = package.get('concluded_license', '')

            # Parse package ID format: "type:namespace:name:version"
            parts = pkg_id.split(':')
            pkg_type = parts[0] if len(parts) > 0 else 'unknown'
            pkg_name = parts[2] if len(parts) > 2 else pkg_id
            pkg_version = parts[3] if len(parts) > 3 else 'unknown'

            # Check for uncertain licenses
            is_uncertain = False
            reasons = []

            # Check declared licenses
            if not declared_licenses or all(self.is_uncertain_license(lic) for lic in declared_licenses):
                is_uncertain = True
                reasons.append('no_declared_license')
                self.stats['uncertain_declared'] += 1

            # Check concluded license
            if self.is_uncertain_license(concluded_license):
                is_uncertain = True
                reasons.append('no_concluded_license')
                self.stats['uncertain_concluded'] += 1

            # Check if package has no license info at all
            if (not declared_licenses or len(declared_licenses) == 0) and not concluded_license:
                is_uncertain = True
                reasons.append('no_license_info')
                self.stats['no_license_info'] += 1

            if is_uncertain:
                package_info = {
                    'id': pkg_id,
                    'type': pkg_type,
                    'name': pkg_name,
                    'version': pkg_version,
                    'declared_licenses': declared_licenses,
                    'concluded_license': concluded_license,
                    'reasons': reasons,
                    'vcs_url': package.get('vcs', {}).get('url', ''),
                    'source_artifact_url': package.get('source_artifact', {}).get('url', ''),
                    'homepage_url': package.get('homepage_url', ''),
                    'description': package.get('description', '')
                }

                self.uncertain_packages.append(package_info)

        print(f"⚠️  Found {len(self.uncertain_packages)} packages with uncertain licenses\n")
        return self.uncertain_packages

    def save_results(self):
        """Save extraction results in multiple formats"""

        # 1. Simple text file with package IDs (for bash scripts)
        id_file = self.output_dir / 'uncertain-package-ids.txt'
        with open(id_file, 'w') as f:
            for pkg in self.uncertain_packages:
                f.write(f"{pkg['id']}\n")
        print(f"✅ Saved package IDs to: {id_file}")

        # 2. JSON file with full details
        json_file = self.output_dir / 'uncertain-packages.json'
        with open(json_file, 'w') as f:
            json.dump(self.uncertain_packages, f, indent=2)
        print(f"✅ Saved detailed JSON to: {json_file}")

        # 3. CSV file for spreadsheet analysis
        csv_file = self.output_dir / 'uncertain-packages.csv'
        with open(csv_file, 'w') as f:
            f.write("Package ID,Name,Version,Type,Declared Licenses,Concluded License,Reasons,VCS URL,Source URL\n")
            for pkg in self.uncertain_packages:
                declared = '|'.join(pkg['declared_licenses']) if pkg['declared_licenses'] else 'NONE'
                reasons = '|'.join(pkg['reasons'])
                f.write(f'"{pkg["id"]}","{pkg["name"]}","{pkg["version"]}","{pkg["type"]}","{declared}","{pkg["concluded_license"]}","{reasons}","{pkg["vcs_url"]}","{pkg["source_artifact_url"]}"\n')
        print(f"✅ Saved CSV report to: {csv_file}")

        # 4. Download script for manual inspection
        download_script = self.output_dir / 'download-packages.sh'
        with open(download_script, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Script to download uncertain packages for manual license inspection\n\n")
            f.write("mkdir -p downloaded-packages\n\n")

            for pkg in self.uncertain_packages:
                if pkg['source_artifact_url']:
                    safe_name = pkg['name'].replace('/', '-').replace(':', '-')
                    f.write(f"# {pkg['name']} {pkg['version']}\n")
                    f.write(f"wget -q -O downloaded-packages/{safe_name}-{pkg['version']}.tar.gz \"{pkg['source_artifact_url']}\" || echo \"Failed to download {pkg['name']}\"\n\n")

        # Make script executable
        download_script.chmod(0o755)
        print(f"✅ Saved download script to: {download_script}")

        # 5. Statistics report
        stats_file = self.output_dir / 'extraction-stats.txt'
        with open(stats_file, 'w') as f:
            f.write("=== License Extraction Statistics ===\n\n")
            f.write(f"Total packages analyzed: {self.stats['total_packages']}\n")
            f.write(f"Packages with uncertain licenses: {len(self.uncertain_packages)}\n")
            f.write(f"  - No declared license: {self.stats['uncertain_declared']}\n")
            f.write(f"  - No concluded license: {self.stats['uncertain_concluded']}\n")
            f.write(f"  - No license info at all: {self.stats['no_license_info']}\n\n")
            f.write(f"Coverage: {((self.stats['total_packages'] - len(self.uncertain_packages)) / self.stats['total_packages'] * 100):.1f}% packages have clear licenses\n")
        print(f"✅ Saved statistics to: {stats_file}")

        # 6. Human-readable report
        report_file = self.output_dir / 'report.md'
        with open(report_file, 'w') as f:
            f.write("# Uncertain License Detection Report\n\n")
            f.write(f"**Analysis Date:** {Path(self.ort_result_path).stat().st_mtime}\n\n")
            f.write(f"## Summary\n\n")
            f.write(f"- Total packages: {self.stats['total_packages']}\n")
            f.write(f"- Packages with uncertain licenses: **{len(self.uncertain_packages)}**\n")
            f.write(f"- License coverage: {((self.stats['total_packages'] - len(self.uncertain_packages)) / self.stats['total_packages'] * 100):.1f}%\n\n")

            f.write("## Packages Requiring Manual Review\n\n")
            f.write("| Package | Version | Type | Declared | Concluded | Source |\n")
            f.write("|---------|---------|------|----------|-----------|--------|\n")

            for pkg in self.uncertain_packages[:50]:  # Limit to first 50 for readability
                declared = ', '.join(pkg['declared_licenses']) if pkg['declared_licenses'] else 'NONE'
                source = 'VCS' if pkg['vcs_url'] else ('Artifact' if pkg['source_artifact_url'] else 'None')
                f.write(f"| {pkg['name']} | {pkg['version']} | {pkg['type']} | {declared} | {pkg['concluded_license'] or 'NONE'} | {source} |\n")

            if len(self.uncertain_packages) > 50:
                f.write(f"\n*... and {len(self.uncertain_packages) - 50} more packages*\n")

            f.write("\n## Next Steps\n\n")
            f.write("1. Run ScanCode on packages with source URLs: `bash download-packages.sh`\n")
            f.write("2. Manually inspect packages without source URLs\n")
            f.write("3. Update curation database with findings\n")
            f.write("4. Re-run ORT analysis with curations applied\n")

        print(f"✅ Saved markdown report to: {report_file}")

    def print_summary(self):
        """Print summary to console"""
        print("\n" + "="*70)
        print("📊 EXTRACTION SUMMARY")
        print("="*70)
        print(f"Total packages: {self.stats['total_packages']}")
        print(f"Uncertain packages: {len(self.uncertain_packages)} ({len(self.uncertain_packages)/self.stats['total_packages']*100:.1f}%)")
        print(f"\nBreakdown:")
        print(f"  - No declared license: {self.stats['uncertain_declared']}")
        print(f"  - No concluded license: {self.stats['uncertain_concluded']}")
        print(f"  - No license info at all: {self.stats['no_license_info']}")

        # Show package types
        type_counts = {}
        for pkg in self.uncertain_packages:
            pkg_type = pkg['type']
            type_counts[pkg_type] = type_counts.get(pkg_type, 0) + 1

        print(f"\nBy package type:")
        for pkg_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {pkg_type}: {count}")

        print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description='Extract packages with uncertain licenses from ORT results'
    )
    parser.add_argument(
        '--ort-result',
        required=True,
        help='Path to ORT analyzer-result.yml file'
    )
    parser.add_argument(
        '--output-dir',
        default='uncertain-packages',
        help='Output directory for results (default: uncertain-packages)'
    )

    args = parser.parse_args()

    # Extract uncertain packages
    extractor = UncertainPackageExtractor(args.ort_result, args.output_dir)
    extractor.extract_uncertain_packages()
    extractor.save_results()
    extractor.print_summary()

    print(f"\n✅ Extraction complete! Check the '{args.output_dir}' directory for results.")


if __name__ == '__main__':
    main()
