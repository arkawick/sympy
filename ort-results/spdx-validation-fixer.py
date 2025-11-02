#!/usr/bin/env python3
"""
SPDX Document Validator and Fixer for ORT-generated SPDX files
Fixes common issues like broken references, missing packages, and invalid IDs
"""

import yaml
import json
import argparse
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


class SPDXValidator:
    def __init__(self, spdx_path: str):
        self.spdx_path = Path(spdx_path)
        self.spdx_doc = self._load_document()
        self.all_spdx_ids: Set[str] = set()
        self.referenced_ids: Set[str] = set()
        self.issues: List[Dict] = []
        
    def _load_document(self) -> dict:
        """Load SPDX document (supports YAML and JSON)"""
        with open(self.spdx_path, 'r') as f:
            if self.spdx_path.suffix in ['.yml', '.yaml']:
                return yaml.safe_load(f)
            else:
                return json.load(f)
    
    def _save_document(self, output_path: str):
        """Save fixed SPDX document"""
        output_path = Path(output_path)
        with open(output_path, 'w') as f:
            if output_path.suffix in ['.yml', '.yaml']:
                yaml.dump(self.spdx_doc, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(self.spdx_doc, f, indent=2)
        print(f"✅ Fixed SPDX document saved to: {output_path}")
    
    def collect_all_spdx_ids(self):
        """Collect all SPDX IDs defined in the document"""
        # Document ID
        if 'SPDXID' in self.spdx_doc:
            self.all_spdx_ids.add(self.spdx_doc['SPDXID'])
        
        # Package IDs
        for package in self.spdx_doc.get('packages', []):
            if 'SPDXID' in package:
                self.all_spdx_ids.add(package['SPDXID'])
        
        # File IDs
        for file_info in self.spdx_doc.get('files', []):
            if 'SPDXID' in file_info:
                self.all_spdx_ids.add(file_info['SPDXID'])
        
        print(f"📊 Found {len(self.all_spdx_ids)} SPDX IDs in document")
    
    def collect_referenced_ids(self):
        """Collect all SPDX IDs that are referenced"""
        
        # Relationships
        for rel in self.spdx_doc.get('relationships', []):
            if 'spdxElementId' in rel:
                self.referenced_ids.add(rel['spdxElementId'])
            if 'relatedSpdxElement' in rel:
                self.referenced_ids.add(rel['relatedSpdxElement'])
        
        # Package relationships
        for package in self.spdx_doc.get('packages', []):
            # External refs
            for ext_ref in package.get('externalRefs', []):
                if 'referenceLocator' in ext_ref and ext_ref['referenceLocator'].startswith('SPDXRef-'):
                    self.referenced_ids.add(ext_ref['referenceLocator'])
        
        print(f"📊 Found {len(self.referenced_ids)} referenced SPDX IDs")
    
    def find_broken_references(self) -> List[str]:
        """Find references to non-existent SPDX IDs"""
        broken = self.referenced_ids - self.all_spdx_ids
        
        if broken:
            print(f"\n❌ Found {len(broken)} broken references:")
            for ref in sorted(broken):
                print(f"   - {ref}")
                self.issues.append({
                    'type': 'broken_reference',
                    'spdx_id': ref,
                    'severity': 'error'
                })
        
        return list(broken)
    
    def fix_package_name_references(self):
        """
        Fix common ORT issue: package names with dots creating invalid SPDX IDs
        Example: coverage.toml -> coverage-toml
        """
        print("\n🔧 Fixing package name references...")
        
        fixed_count = 0
        id_mapping = {}
        
        # First pass: identify and fix package IDs
        for package in self.spdx_doc.get('packages', []):
            original_id = package.get('SPDXID', '')
            
            # Fix dots in package names (common in Python packages)
            if '.' in original_id and not original_id.endswith('.'):
                # Replace dots with hyphens, but preserve version dots
                parts = original_id.split('-')
                if len(parts) >= 3:  # Format: SPDXRef-Package-Type-name.with.dots-version
                    # Reconstruct: keep everything before last part (version), fix middle parts
                    fixed_parts = []
                    for i, part in enumerate(parts[:-1]):  # All except version
                        if i < 3:  # Keep SPDXRef, Package, Type as is
                            fixed_parts.append(part)
                        else:  # Fix package name parts
                            fixed_parts.append(part.replace('.', '-'))
                    fixed_parts.append(parts[-1])  # Add version back
                    
                    fixed_id = '-'.join(fixed_parts)
                    
                    if fixed_id != original_id:
                        id_mapping[original_id] = fixed_id
                        package['SPDXID'] = fixed_id
                        self.all_spdx_ids.add(fixed_id)
                        fixed_count += 1
                        print(f"   ✓ {original_id} → {fixed_id}")
        
        # Second pass: update all references
        for rel in self.spdx_doc.get('relationships', []):
            if rel.get('spdxElementId') in id_mapping:
                rel['spdxElementId'] = id_mapping[rel['spdxElementId']]
            if rel.get('relatedSpdxElement') in id_mapping:
                rel['relatedSpdxElement'] = id_mapping[rel['relatedSpdxElement']]
        
        if fixed_count > 0:
            print(f"✅ Fixed {fixed_count} package ID references")
        
        return id_mapping
    
    def remove_broken_relationships(self, broken_refs: List[str]):
        """Remove relationships that reference non-existent packages"""
        print("\n🔧 Removing broken relationships...")
        
        original_count = len(self.spdx_doc.get('relationships', []))
        
        # Filter out broken relationships
        valid_relationships = []
        removed_count = 0
        
        for rel in self.spdx_doc.get('relationships', []):
            element_id = rel.get('spdxElementId', '')
            related_id = rel.get('relatedSpdxElement', '')
            
            # Keep relationship only if both IDs exist
            if element_id in self.all_spdx_ids and related_id in self.all_spdx_ids:
                valid_relationships.append(rel)
            else:
                removed_count += 1
                print(f"   ✗ Removed: {element_id} → {related_id}")
        
        self.spdx_doc['relationships'] = valid_relationships
        
        print(f"✅ Removed {removed_count} broken relationships ({original_count} → {len(valid_relationships)})")
    
    def create_missing_packages(self, broken_refs: List[str]):
        """Create stub packages for missing references (alternative to removal)"""
        print("\n🔧 Creating stub packages for missing references...")
        
        created_count = 0
        
        for ref in broken_refs:
            # Only create for package references
            if ref.startswith('SPDXRef-Package-'):
                # Parse the reference to extract package info
                # Format: SPDXRef-Package-Type-name-version
                parts = ref.split('-')
                
                if len(parts) >= 4:
                    pkg_type = parts[2] if len(parts) > 2 else 'Unknown'
                    pkg_name = '-'.join(parts[3:-1]) if len(parts) > 4 else parts[3]
                    pkg_version = parts[-1] if len(parts) > 3 else 'unknown'
                    
                    stub_package = {
                        'SPDXID': ref,
                        'name': pkg_name,
                        'versionInfo': pkg_version,
                        'downloadLocation': 'NOASSERTION',
                        'filesAnalyzed': False,
                        'licenseConcluded': 'NOASSERTION',
                        'licenseDeclared': 'NOASSERTION',
                        'copyrightText': 'NOASSERTION',
                        'comment': f'Stub package created by SPDX validator for missing reference'
                    }
                    
                    self.spdx_doc.setdefault('packages', []).append(stub_package)
                    self.all_spdx_ids.add(ref)
                    created_count += 1
                    print(f"   ✓ Created stub: {pkg_name} {pkg_version}")
        
        if created_count > 0:
            print(f"✅ Created {created_count} stub packages")
    
    def validate_and_fix(self, output_path: str, create_stubs: bool = False):
        """Main validation and fixing workflow"""
        print(f"🔍 Validating SPDX document: {self.spdx_path}\n")
        
        # Step 1: Collect all IDs
        self.collect_all_spdx_ids()
        self.collect_referenced_ids()
        
        # Step 2: Fix package name issues
        self.fix_package_name_references()
        
        # Step 3: Re-collect IDs after fixes
        self.all_spdx_ids.clear()
        self.collect_all_spdx_ids()
        
        # Step 4: Find broken references
        broken_refs = self.find_broken_references()
        
        # Step 5: Fix broken references
        if broken_refs:
            if create_stubs:
                self.create_missing_packages(broken_refs)
            else:
                self.remove_broken_relationships(broken_refs)
        
        # Step 6: Save fixed document
        self._save_document(output_path)
        
        # Step 7: Summary
        print("\n" + "="*60)
        print("📋 VALIDATION SUMMARY")
        print("="*60)
        print(f"Total SPDX IDs: {len(self.all_spdx_ids)}")
        print(f"Total references: {len(self.referenced_ids)}")
        print(f"Issues found: {len(self.issues)}")
        print(f"Issues fixed: {len(broken_refs)}")
        print("="*60)
        
        if len(self.issues) == len(broken_refs):
            print("\n✅ All issues resolved! Document should now be valid.")
        else:
            print(f"\n⚠️  {len(self.issues) - len(broken_refs)} issues remain.")
        
        return len(self.issues) == 0


def main():
    parser = argparse.ArgumentParser(
        description='Validate and fix ORT-generated SPDX documents'
    )
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input SPDX document (YAML or JSON)'
    )
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output path for fixed SPDX document'
    )
    parser.add_argument(
        '--create-stubs',
        action='store_true',
        help='Create stub packages for missing references instead of removing relationships'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate without fixing'
    )
    
    args = parser.parse_args()
    
    validator = SPDXValidator(args.input)
    
    if args.validate_only:
        validator.collect_all_spdx_ids()
        validator.collect_referenced_ids()
        validator.find_broken_references()
    else:
        validator.validate_and_fix(args.output, create_stubs=args.create_stubs)


if __name__ == '__main__':
    main()
