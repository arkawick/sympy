#!/usr/bin/env python3
"""
ORT Curation Database Management Tool
Helps add, validate, and manage package license curations.
"""

import yaml
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class CurationManager:
    """Manages ORT package curations"""

    def __init__(self, curation_file: str = '.ort/curations.yml'):
        self.curation_file = Path(curation_file)
        self.curations = self.load_curations()

    def load_curations(self) -> Dict:
        """Load existing curations file"""
        if not self.curation_file.exists():
            print(f"⚠️  Curation file not found: {self.curation_file}")
            print("   Creating new file...")
            self.curation_file.parent.mkdir(parents=True, exist_ok=True)
            return {'curations': []}

        with open(self.curation_file, 'r') as f:
            data = yaml.safe_load(f) or {}

        return data

    def save_curations(self):
        """Save curations back to file"""
        with open(self.curation_file, 'w') as f:
            yaml.dump(self.curations, f, default_flow_style=False, sort_keys=False)

        print(f"✅ Curations saved to: {self.curation_file}")

    def add_curation(self, pkg_id: str, concluded_license: str, comment: str, **kwargs):
        """Add a new package curation"""

        # Check if curation already exists
        for i, curation in enumerate(self.curations.get('curations', [])):
            if curation.get('id') == pkg_id:
                print(f"⚠️  Curation already exists for {pkg_id}")
                print("   Would you like to update it? (y/n): ", end='')
                # In automated mode, just update
                self.curations['curations'][i] = self._build_curation_entry(
                    pkg_id, concluded_license, comment, **kwargs
                )
                print(f"✅ Updated curation for {pkg_id}")
                return

        # Add new curation
        if 'curations' not in self.curations:
            self.curations['curations'] = []

        new_curation = self._build_curation_entry(pkg_id, concluded_license, comment, **kwargs)
        self.curations['curations'].append(new_curation)

        print(f"✅ Added curation for {pkg_id}")

    def _build_curation_entry(self, pkg_id: str, concluded_license: str, comment: str, **kwargs) -> Dict:
        """Build a curation entry dictionary"""
        entry = {
            'id': pkg_id,
            'curations': {
                'comment': f"{comment} (Added: {datetime.now().strftime('%Y-%m-%d')})",
                'concluded_license': concluded_license
            }
        }

        # Add declared license mapping if original license specified
        if 'original_license' in kwargs:
            entry['curations']['declared_license_mapping'] = {
                kwargs['original_license']: concluded_license
            }

        # Add optional fields
        for field in ['homepage_url', 'source_artifact_url', 'vcs_url', 'vcs_type', 'vcs_revision']:
            if field in kwargs and kwargs[field]:
                if field.startswith('vcs_'):
                    if 'vcs' not in entry['curations']:
                        entry['curations']['vcs'] = {}
                    vcs_field = field[4:]  # Remove 'vcs_' prefix
                    entry['curations']['vcs'][vcs_field] = kwargs[field]
                else:
                    entry['curations'][field] = kwargs[field]

        return entry

    def add_from_uncertain_packages(self, uncertain_packages_file: str):
        """Add curations from uncertain packages JSON file"""
        print(f"📖 Loading uncertain packages from: {uncertain_packages_file}")

        with open(uncertain_packages_file, 'r') as f:
            uncertain = json.load(f)

        print(f"   Found {len(uncertain)} uncertain packages")
        print("\n🔧 Generating curation templates...\n")

        added = 0
        for pkg in uncertain:
            pkg_id = pkg['id']
            pkg_name = pkg['name']

            # Create template curation
            comment = f"Package '{pkg_name}' had uncertain license. REVIEW REQUIRED: Update with correct license after manual verification."

            self.add_curation(
                pkg_id=pkg_id,
                concluded_license="REVIEW-REQUIRED",
                comment=comment,
                original_license="NOASSERTION",
                homepage_url=pkg.get('homepage_url', ''),
                source_artifact_url=pkg.get('source_artifact_url', ''),
                vcs_url=pkg.get('vcs_url', ''),
                vcs_type='Git' if pkg.get('vcs_url') else None
            )
            added += 1

        print(f"\n✅ Added {added} curation templates")
        print("⚠️  IMPORTANT: Review and update each curation with the correct license!")

    def list_curations(self):
        """List all curations"""
        curations = self.curations.get('curations', [])

        if not curations:
            print("📋 No curations found")
            return

        print(f"📋 Found {len(curations)} curations:\n")

        for i, curation in enumerate(curations, 1):
            pkg_id = curation.get('id', 'unknown')
            concluded = curation['curations'].get('concluded_license', 'N/A')
            comment = curation['curations'].get('comment', '')

            print(f"{i}. {pkg_id}")
            print(f"   License: {concluded}")
            print(f"   Comment: {comment[:80]}{'...' if len(comment) > 80 else ''}")
            print()

    def validate_curations(self):
        """Validate curation entries"""
        print("🔍 Validating curations...\n")

        curations = self.curations.get('curations', [])
        issues = []

        for i, curation in enumerate(curations):
            pkg_id = curation.get('id', '')

            # Check required fields
            if not pkg_id:
                issues.append(f"Curation #{i+1}: Missing package ID")
                continue

            curation_data = curation.get('curations', {})

            if not curation_data.get('concluded_license'):
                issues.append(f"{pkg_id}: Missing concluded_license")

            if not curation_data.get('comment'):
                issues.append(f"{pkg_id}: Missing comment")

            # Check for review-required markers
            concluded = curation_data.get('concluded_license', '')
            if concluded in ['REVIEW-REQUIRED', 'TODO', 'FIXME', 'UNKNOWN']:
                issues.append(f"{pkg_id}: License needs review (current: {concluded})")

            # Validate package ID format
            if pkg_id.count(':') < 2:
                issues.append(f"{pkg_id}: Invalid package ID format (should be TYPE:NAMESPACE:NAME:VERSION)")

        if issues:
            print(f"⚠️  Found {len(issues)} issues:\n")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print(f"✅ All {len(curations)} curations are valid!")
            return True

    def remove_curation(self, pkg_id: str):
        """Remove a curation by package ID"""
        curations = self.curations.get('curations', [])

        for i, curation in enumerate(curations):
            if curation.get('id') == pkg_id:
                del self.curations['curations'][i]
                print(f"✅ Removed curation for {pkg_id}")
                return True

        print(f"⚠️  No curation found for {pkg_id}")
        return False

    def export_to_csv(self, output_file: str):
        """Export curations to CSV for review"""
        import csv

        curations = self.curations.get('curations', [])

        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Package ID', 'Concluded License', 'Original License', 'Comment', 'Homepage', 'Source URL'])

            for curation in curations:
                pkg_id = curation.get('id', '')
                curation_data = curation.get('curations', {})

                concluded = curation_data.get('concluded_license', '')
                comment = curation_data.get('comment', '')
                homepage = curation_data.get('homepage_url', '')
                source = curation_data.get('source_artifact_url', '')

                # Get original license from mapping
                mapping = curation_data.get('declared_license_mapping', {})
                original = ', '.join(mapping.keys()) if mapping else ''

                writer.writerow([pkg_id, concluded, original, comment, homepage, source])

        print(f"✅ Exported {len(curations)} curations to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Manage ORT package license curations'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Add curation command
    add_parser = subparsers.add_parser('add', help='Add a new curation')
    add_parser.add_argument('--id', required=True, help='Package ID (TYPE:NAMESPACE:NAME:VERSION)')
    add_parser.add_argument('--license', required=True, help='Concluded license (SPDX identifier)')
    add_parser.add_argument('--comment', required=True, help='Curation comment/justification')
    add_parser.add_argument('--original-license', help='Original incorrect license')
    add_parser.add_argument('--homepage', help='Package homepage URL')
    add_parser.add_argument('--source-url', help='Source artifact URL')

    # List curations command
    subparsers.add_parser('list', help='List all curations')

    # Validate curations command
    subparsers.add_parser('validate', help='Validate curation file')

    # Remove curation command
    remove_parser = subparsers.add_parser('remove', help='Remove a curation')
    remove_parser.add_argument('--id', required=True, help='Package ID to remove')

    # Import from uncertain packages
    import_parser = subparsers.add_parser('import-uncertain', help='Import from uncertain packages JSON')
    import_parser.add_argument('--file', required=True, help='Path to uncertain-packages.json')

    # Export to CSV
    export_parser = subparsers.add_parser('export', help='Export curations to CSV')
    export_parser.add_argument('--output', default='curations.csv', help='Output CSV file')

    # Curation file location
    parser.add_argument('--curation-file', default='.ort/curations.yml', help='Path to curations.yml')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = CurationManager(args.curation_file)

    if args.command == 'add':
        manager.add_curation(
            pkg_id=args.id,
            concluded_license=args.license,
            comment=args.comment,
            original_license=args.original_license,
            homepage_url=args.homepage,
            source_artifact_url=args.source_url
        )
        manager.save_curations()

    elif args.command == 'list':
        manager.list_curations()

    elif args.command == 'validate':
        manager.validate_curations()

    elif args.command == 'remove':
        if manager.remove_curation(args.id):
            manager.save_curations()

    elif args.command == 'import-uncertain':
        manager.add_from_uncertain_packages(args.file)
        manager.save_curations()
        print("\n⚠️  Next steps:")
        print("   1. Review generated curations in .ort/curations.yml")
        print("   2. Update 'REVIEW-REQUIRED' with actual licenses")
        print("   3. Run: python manage_curations.py validate")
        print("   4. Re-run ORT analysis with curations applied")

    elif args.command == 'export':
        manager.export_to_csv(args.output)


if __name__ == '__main__':
    main()
