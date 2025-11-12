#!/usr/bin/env python3
"""
AI-Powered Multi-Layer License Resolution Report

Analyzes packages with conflicting or missing licenses across ORT, PyPI API,
and ScanCode results, and uses Azure OpenAI to provide intelligent recommendations
for resolution.

This is the 4th AI report in the Enhanced ORT system:
1. Main ORT Curation Report
2. Conflict Analysis Report
3. Missing Licenses AI Analysis
4. Multi-Layer Resolution Report (THIS SCRIPT)

Author: Enhanced ORT License Curation System
"""

import json
import yaml
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

# Azure OpenAI imports
from openai import AzureOpenAI


class MultiLayerLicenseResolver:
    """Analyzes multi-layer license conflicts and provides AI-powered resolutions"""

    def __init__(self, ort_result_path: str, pypi_results_path: Optional[str],
                 scancode_results_dir: Optional[str], uncertain_packages_path: Optional[str]):
        self.ort_result_path = Path(ort_result_path)
        self.pypi_results_path = Path(pypi_results_path) if pypi_results_path else None
        self.scancode_results_dir = Path(scancode_results_dir) if scancode_results_dir else None
        self.uncertain_packages_path = Path(uncertain_packages_path) if uncertain_packages_path else None

        self.packages = {}
        self.uncertain_packages = {}
        self.resolved_packages = []  # Packages with consistent licenses
        self.conflict_packages = []  # Packages with conflicting licenses
        self.missing_packages = []   # Packages with no licenses found

        # Azure OpenAI client
        self.client = None
        self._init_azure_openai()

    def _init_azure_openai(self):
        """Initialize Azure OpenAI client"""
        api_key = os.environ.get('AZURE_OPENAI_API_KEY')
        endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT', 'https://ltts-cariad-ddd-mvp-ai-foundry.cognitiveservices.azure.com')
        self.model_deployment = os.environ.get('AZURE_OPENAI_MODEL', 'gpt-4.1-mini')

        if not api_key:
            print("⚠️  AZURE_OPENAI_API_KEY not set - AI analysis will be skipped")
            return

        if not endpoint:
            print("⚠️  AZURE_OPENAI_ENDPOINT not set - AI analysis will be skipped")
            return

        try:
            self.client = AzureOpenAI(
                api_key=api_key,
                api_version="2025-01-01-preview",
                azure_endpoint=endpoint
            )
            print(f"✓ Azure OpenAI client initialized")
            print(f"  Using model deployment: {self.model_deployment}")
        except Exception as e:
            print(f"⚠️  Failed to initialize Azure OpenAI: {e}")
            self.client = None

    def load_all_data(self):
        """Load data from all sources"""
        print("\n📊 Loading multi-layer license data...\n")

        self._load_ort_licenses()
        self._load_uncertain_packages()
        self._load_pypi_licenses()
        self._load_scancode_licenses()

        self._identify_conflicts_and_missing()

    def _load_ort_licenses(self):
        """Load ORT licenses"""
        print("📦 Loading ORT licenses...")

        if not self.ort_result_path.exists():
            print(f"   ⚠️  ORT result not found: {self.ort_result_path}")
            return

        with open(self.ort_result_path, 'r', encoding='utf-8') as f:
            ort_data = yaml.safe_load(f)

        packages = ort_data.get('analyzer', {}).get('result', {}).get('packages', [])

        for pkg in packages:
            pkg_id = pkg.get('id', '')
            declared_processed = pkg.get('declared_licenses_processed', {})
            spdx_expression = declared_processed.get('spdx_expression', '')

            parts = pkg_id.split(':')
            pkg_type = parts[0] if len(parts) > 0 else 'Unknown'
            namespace = parts[1] if len(parts) > 1 else ''
            name = parts[2] if len(parts) > 2 else ''
            version = parts[3] if len(parts) > 3 else ''
            display_name = f"{namespace}/{name}" if namespace else name

            self.packages[pkg_id] = {
                'id': pkg_id,
                'type': pkg_type,
                'name': name,
                'display_name': display_name,
                'version': version,
                'ort_license': spdx_expression if spdx_expression else 'NOASSERTION',
                'pypi_license': None,
                'scancode_license': None,
                'homepage': pkg.get('homepage_url', ''),
                'repository': pkg.get('vcs', {}).get('url', ''),
                'description': pkg.get('description', ''),
            }

        print(f"   ✓ Loaded {len(self.packages)} packages from ORT")

    def _load_uncertain_packages(self):
        """Load uncertain packages list"""
        if not self.uncertain_packages_path or not self.uncertain_packages_path.exists():
            return

        print("📋 Loading uncertain packages list...")

        with open(self.uncertain_packages_path, 'r', encoding='utf-8') as f:
            uncertain_list = json.load(f)

        for pkg in uncertain_list:
            pkg_id = pkg.get('id', '')
            if pkg_id:
                self.uncertain_packages[pkg_id] = pkg

        print(f"   ✓ Loaded {len(self.uncertain_packages)} uncertain packages")

    def _load_pypi_licenses(self):
        """Load PyPI licenses"""
        if not self.pypi_results_path or not self.pypi_results_path.exists():
            return

        print("🐍 Loading PyPI licenses...")

        with open(self.pypi_results_path, 'r', encoding='utf-8') as f:
            pypi_data = json.load(f)

        packages_analyzed = pypi_data.get('packages', [])
        count = 0

        for pkg in packages_analyzed:
            pkg_id = pkg.get('id', '')
            fetched_license = pkg.get('fetched_license', {})

            if pkg_id in self.packages and fetched_license:
                if fetched_license.get('success'):
                    license_found = fetched_license.get('license', '')
                    if license_found and license_found.lower() not in ['unknown', 'none', '', 'n/a']:
                        self.packages[pkg_id]['pypi_license'] = license_found
                        count += 1

        print(f"   ✓ Loaded PyPI licenses for {count} packages")

    def _load_scancode_licenses(self):
        """Load ScanCode licenses"""
        if not self.scancode_results_dir or not self.scancode_results_dir.exists():
            return

        print("🔍 Loading ScanCode licenses...")

        scancode_files = list(self.scancode_results_dir.glob("*.json"))
        count = 0

        for json_file in scancode_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    scan_data = json.load(f)

                # Check package-level license
                package_level_license = None
                packages_section = scan_data.get('packages', [])

                if packages_section and len(packages_section) > 0:
                    pkg_info = packages_section[0]
                    package_level_license = pkg_info.get('declared_license_expression_spdx')

                # Match to package
                if self.uncertain_packages:
                    file_stem = json_file.stem
                    matched_pkg_id = None

                    for pkg_id, uncertain_pkg in self.uncertain_packages.items():
                        pkg_name = uncertain_pkg.get('name', '')
                        pkg_version = uncertain_pkg.get('version', '')
                        expected_name = f"{pkg_name}-{pkg_version}".replace('/', '-').replace(':', '-')

                        if file_stem.lower() == expected_name.lower():
                            matched_pkg_id = pkg_id
                            break

                    if matched_pkg_id and package_level_license:
                        if package_level_license not in ['NOASSERTION', 'NONE', '']:
                            self.packages[matched_pkg_id]['scancode_license'] = package_level_license
                            count += 1

            except Exception as e:
                pass

        print(f"   ✓ Loaded ScanCode licenses for {count} packages")

    def _identify_conflicts_and_missing(self):
        """Identify packages as resolved, conflicted, or missing"""
        print("\n🔍 Analyzing license status across all sources...")

        for pkg_id, pkg_info in self.packages.items():
            ort_lic = pkg_info['ort_license']
            pypi_lic = pkg_info['pypi_license']
            scancode_lic = pkg_info['scancode_license']

            # Collect non-empty licenses
            licenses = []
            if ort_lic and ort_lic != 'NOASSERTION':
                licenses.append(ort_lic)
            if pypi_lic:
                licenses.append(pypi_lic)
            if scancode_lic:
                licenses.append(scancode_lic)

            # Categorize package
            if len(licenses) == 0:
                # No license found anywhere
                self.missing_packages.append(pkg_info)
            elif len(licenses) == 1:
                # Single license found - resolved
                pkg_info['resolved_license'] = licenses[0]
                self.resolved_packages.append(pkg_info)
            else:
                # Multiple licenses - check for conflicts
                normalized = {lic.upper().replace('-', '').replace(' ', '').replace('_', '') for lic in licenses}
                if len(normalized) == 1:
                    # Same license, just different formatting - resolved
                    pkg_info['resolved_license'] = licenses[0]
                    self.resolved_packages.append(pkg_info)
                else:
                    # Real conflict
                    self.conflict_packages.append(pkg_info)

        print(f"   ✅ Found {len(self.resolved_packages)} packages with consistent licenses")
        print(f"   ⚠️  Found {len(self.conflict_packages)} packages with license conflicts")
        print(f"   ❌ Found {len(self.missing_packages)} packages with missing licenses")

    def analyze_with_ai(self, package: Dict) -> Dict:
        """Use Azure OpenAI to analyze a package and provide recommendations"""

        if not self.client:
            return {
                'recommendation': 'AI analysis unavailable',
                'reasoning': 'Azure OpenAI not configured',
                'confidence': 'N/A',
                'action': 'Manual review required'
            }

        pkg_name = package['display_name']
        pkg_type = package['type']
        ort_lic = package['ort_license']
        pypi_lic = package['pypi_license'] or 'Not found'
        scancode_lic = package['scancode_license'] or 'Not found'
        homepage = package['homepage']
        repo = package['repository']

        # Determine if conflict or missing
        is_conflict = package in self.conflict_packages
        is_missing = package in self.missing_packages

        if is_conflict:
            prompt = f"""You are a software license compliance expert. Analyze this package with conflicting license information from multiple sources:

Package: {pkg_name} ({pkg_type})
Version: {package['version']}

LICENSE INFORMATION FROM MULTIPLE SOURCES:
- ORT (package manifest): {ort_lic}
- PyPI API: {pypi_lic}
- ScanCode (deep scan): {scancode_lic}

Homepage: {homepage}
Repository: {repo}

TASK: Analyze this license conflict and provide:
1. Which license is most likely correct and why
2. Explain why the sources disagree
3. Recommended action to resolve the conflict
4. Confidence level (High/Medium/Low)

Provide a concise, actionable response in JSON format:
{{
    "recommended_license": "SPDX identifier",
    "reasoning": "Why this license is most likely correct",
    "conflict_explanation": "Why sources disagree",
    "action": "Specific steps to resolve",
    "confidence": "High|Medium|Low",
    "verification_steps": ["step 1", "step 2"]
}}"""
        else:  # Missing
            prompt = f"""You are a software license compliance expert with access to knowledge about open-source packages. This package has NO license information found across all automated detection methods:

Package: {pkg_name} ({pkg_type})
Version: {package['version']}

ATTEMPTED LICENSE DETECTION:
- ORT (package manifest): {ort_lic}
- PyPI API: {pypi_lic}
- ScanCode (source scan): {scancode_lic}

Package Information:
- Homepage: {homepage or 'Not available'}
- Repository: {repo or 'Not available'}
- Description: {package['description'][:200] if package['description'] else 'Not available'}

TASK: Research and suggest the most likely license by analyzing:
1. **Repository URL patterns** (GitHub/GitLab/Bitbucket) - if provided, infer what the LICENSE file would contain
2. **Package ecosystem standards** (PyPI, NPM, Maven typical licenses)
3. **Package name patterns** (common framework/library conventions)
4. **Organization/author patterns** (known publishers and their typical licenses)
5. **Similar packages** in the same ecosystem

Based on your knowledge of open-source licensing:
- Suggest the MOST LIKELY license this package would have
- Explain WHERE to find the actual license (GitHub repo path, package registry, etc.)
- Provide SPECIFIC URLs to check (construct GitHub raw LICENSE URL if repo is known)

Provide a concise, actionable response in JSON format:
{{
    "suggested_license": "SPDX identifier (e.g., MIT, Apache-2.0, BSD-3-Clause)",
    "reasoning": "Why this license is most likely based on package patterns/ecosystem",
    "confidence": "High|Medium|Low",
    "github_license_url": "Direct URL to LICENSE file if repo is GitHub (or empty string)",
    "action": "Specific steps to find and verify the license",
    "verification_steps": ["Check specific URL/path", "Verify in package registry", "etc"],
    "risk_level": "High|Medium|Low",
    "alternative_licenses": ["other possible licenses to check"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model_deployment,
                messages=[
                    {"role": "system", "content": "You are an expert in open-source license compliance and SPDX identifiers. Provide accurate, actionable advice."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )

            # Parse AI response
            ai_response = response.choices[0].message.content.strip()

            # Try to parse as JSON
            try:
                if '```json' in ai_response:
                    ai_response = ai_response.split('```json')[1].split('```')[0].strip()
                elif '```' in ai_response:
                    ai_response = ai_response.split('```')[1].split('```')[0].strip()

                result = json.loads(ai_response)
                return result
            except:
                # Fallback if not valid JSON
                return {
                    'recommendation': ai_response[:200],
                    'reasoning': 'See full response',
                    'confidence': 'Medium',
                    'action': 'Manual review'
                }

        except Exception as e:
            print(f"   ⚠️  AI analysis failed for {pkg_name}: {e}")
            return {
                'recommendation': 'AI analysis failed',
                'reasoning': str(e),
                'confidence': 'N/A',
                'action': 'Manual review required'
            }

    def generate_html_report(self, output_path: str):
        """Generate beautiful HTML report with AI recommendations"""

        print(f"\n🎨 Generating AI-powered resolution report...")

        # Analyze conflicts and missing packages with AI
        conflict_analyses = []
        missing_analyses = []

        # Limit to prevent excessive API costs
        MAX_CONFLICTS = 15
        MAX_MISSING = 10

        print(f"\n🤖 Running AI analysis on problematic packages...")
        print(f"   Analyzing {min(len(self.conflict_packages), MAX_CONFLICTS)} conflict packages...")

        for i, pkg in enumerate(self.conflict_packages[:MAX_CONFLICTS], 1):
            print(f"      [{i}/{min(len(self.conflict_packages), MAX_CONFLICTS)}] {pkg['display_name']}")
            analysis = self.analyze_with_ai(pkg)
            conflict_analyses.append({
                'package': pkg,
                'analysis': analysis
            })

        print(f"   Analyzing {min(len(self.missing_packages), MAX_MISSING)} missing license packages...")

        for i, pkg in enumerate(self.missing_packages[:MAX_MISSING], 1):
            print(f"      [{i}/{min(len(self.missing_packages), MAX_MISSING)}] {pkg['display_name']}")
            analysis = self.analyze_with_ai(pkg)
            missing_analyses.append({
                'package': pkg,
                'analysis': analysis
            })

        # Generate HTML (now includes resolved packages)
        html = self._generate_html_content(self.resolved_packages, conflict_analyses, missing_analyses)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n✅ Report generated: {output_file}")
        print(f"   Resolved packages: {len(self.resolved_packages)}")
        print(f"   Conflicts analyzed: {len(conflict_analyses)}")
        print(f"   Missing analyzed: {len(missing_analyses)}")

    def _generate_html_content(self, resolved_packages: List[Dict], conflict_analyses: List[Dict], missing_analyses: List[Dict]) -> str:
        """Generate HTML content for the report"""

        total_packages = len(resolved_packages) + len(conflict_analyses) + len(missing_analyses)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Multi-Layer License Resolution Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
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

        .stat-conflicts {{ color: #f59e0b; }}
        .stat-missing {{ color: #ef4444; }}
        .stat-total {{ color: #667eea; }}

        .section {{
            padding: 40px;
        }}

        .section-title {{
            font-size: 2em;
            color: #2d3748;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}

        .package-card {{
            background: #f9fafb;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
        }}

        .package-card.conflict {{
            border-left-color: #f59e0b;
        }}

        .package-card.missing {{
            border-left-color: #ef4444;
        }}

        .package-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}

        .package-name {{
            font-size: 1.5em;
            font-weight: 600;
            color: #1f2937;
        }}

        .package-type {{
            background: #e5e7eb;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 0.9em;
            color: #4b5563;
        }}

        .license-comparison {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 15px 0;
            padding: 15px;
            background: white;
            border-radius: 6px;
        }}

        .license-source {{
            text-align: center;
        }}

        .license-source-label {{
            font-size: 0.85em;
            color: #6b7280;
            margin-bottom: 5px;
            font-weight: 600;
        }}

        .license-value {{
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            padding: 8px;
            background: #f3f4f6;
            border-radius: 4px;
        }}

        .license-value.found {{
            background: #d1fae5;
            color: #065f46;
        }}

        .license-value.missing {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .ai-analysis {{
            background: linear-gradient(135deg, #667eea15, #764ba215);
            padding: 20px;
            border-radius: 8px;
            margin-top: 15px;
        }}

        .ai-label {{
            font-weight: 600;
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}

        .ai-recommendation {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 10px;
        }}

        .confidence {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .confidence-high {{ background: #d1fae5; color: #065f46; }}
        .confidence-medium {{ background: #fed7aa; color: #92400e; }}
        .confidence-low {{ background: #fee2e2; color: #991b1b; }}

        .verification-steps {{
            margin-top: 10px;
        }}

        .verification-steps li {{
            margin-left: 20px;
            margin-bottom: 5px;
            color: #4b5563;
        }}

        .links {{
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }}

        .link-btn {{
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 0.9em;
            transition: all 0.3s;
        }}

        .link-btn:hover {{
            background: #5568d3;
        }}

        .footer {{
            text-align: center;
            padding: 30px;
            background: #f9fafb;
            color: #6b7280;
        }}

        .ltts-branding {{
            margin-top: 10px;
            font-weight: 600;
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Multi-Layer License Resolution</h1>
            <p>Intelligent analysis of conflicting and missing licenses</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <h3 class="stat-total">{total_packages}</h3>
                <p>Total Packages</p>
            </div>
            <div class="stat-card">
                <h3 style="color: #10b981;">{len(resolved_packages)}</h3>
                <p>Resolved ({len(resolved_packages)/total_packages*100:.1f}%)</p>
            </div>
            <div class="stat-card">
                <h3 class="stat-conflicts">{len(conflict_analyses)}</h3>
                <p>Conflicts ({len(conflict_analyses)/total_packages*100:.1f}%)</p>
            </div>
            <div class="stat-card">
                <h3 class="stat-missing">{len(missing_analyses)}</h3>
                <p>Missing ({len(missing_analyses)/total_packages*100:.1f}%)</p>
            </div>
        </div>
"""

        # Resolved packages section (show first - the good news!)
        if resolved_packages:
            html += """
        <div class="section">
            <h2 class="section-title">✅ Resolved Packages</h2>
            <p style="margin-bottom: 20px; color: #6b7280;">Packages with consistent license information across all sources</p>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px;">
"""
            for pkg in resolved_packages:
                resolved_lic = pkg.get('resolved_license', 'Unknown')
                ort_lic = pkg['ort_license']
                pypi_lic = pkg['pypi_license']
                scancode_lic = pkg['scancode_license']

                # Determine which sources have the license
                sources = []
                if ort_lic and ort_lic != 'NOASSERTION':
                    sources.append('ORT')
                if pypi_lic:
                    sources.append('PyPI')
                if scancode_lic:
                    sources.append('ScanCode')

                sources_text = ' + '.join(sources)

                html += f"""
                <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 15px; border-radius: 6px;">
                    <div style="font-weight: 600; color: #1f2937; margin-bottom: 5px;">{pkg['display_name']}</div>
                    <div style="font-size: 0.85em; color: #6b7280; margin-bottom: 8px;">{pkg['type']} v{pkg['version']}</div>
                    <div style="background: white; padding: 8px; border-radius: 4px; margin-bottom: 5px;">
                        <div style="font-family: 'Courier New', monospace; color: #065f46; font-weight: 600;">{resolved_lic}</div>
                    </div>
                    <div style="font-size: 0.8em; color: #059669;">
                        Confirmed by: {sources_text}
                    </div>
                </div>
"""

            html += """
            </div>
        </div>
"""

        # Conflicts section
        if conflict_analyses:
            html += """
        <div class="section">
            <h2 class="section-title">⚠️ License Conflicts</h2>
            <p style="margin-bottom: 20px; color: #6b7280;">Packages with disagreeing license information across ORT, PyPI, and ScanCode</p>
"""
            for item in conflict_analyses:
                pkg = item['package']
                analysis = item['analysis']

                recommended = analysis.get('recommended_license', analysis.get('suggestion', 'See reasoning'))
                reasoning = analysis.get('reasoning', analysis.get('conflict_explanation', 'No reasoning provided'))
                confidence = analysis.get('confidence', 'Medium')
                action = analysis.get('action', 'Manual review required')
                verification_steps = analysis.get('verification_steps', [])

                ort_lic = pkg['ort_license']
                pypi_lic = pkg['pypi_license'] or 'Not found'
                scancode_lic = pkg['scancode_license'] or 'Not found'

                ort_class = 'found' if ort_lic != 'NOASSERTION' else 'missing'
                pypi_class = 'found' if pypi_lic != 'Not found' else 'missing'
                scancode_class = 'found' if scancode_lic != 'Not found' else 'missing'

                html += f"""
            <div class="package-card conflict">
                <div class="package-header">
                    <div class="package-name">{pkg['display_name']}</div>
                    <div class="package-type">{pkg['type']}</div>
                </div>

                <div class="license-comparison">
                    <div class="license-source">
                        <div class="license-source-label">ORT</div>
                        <div class="license-value {ort_class}">{ort_lic}</div>
                    </div>
                    <div class="license-source">
                        <div class="license-source-label">PyPI API</div>
                        <div class="license-value {pypi_class}">{pypi_lic}</div>
                    </div>
                    <div class="license-source">
                        <div class="license-source-label">ScanCode</div>
                        <div class="license-value {scancode_class}">{scancode_lic}</div>
                    </div>
                </div>

                <div class="ai-analysis">
                    <div class="ai-label">🤖 AI Recommendation</div>
                    <div class="ai-recommendation">
                        <strong>Recommended License:</strong> {recommended}
                        <span class="confidence confidence-{confidence.lower()}">{confidence} Confidence</span>
                    </div>
                    <div class="ai-recommendation">
                        <strong>Reasoning:</strong><br>
                        {reasoning}
                    </div>
                    <div class="ai-recommendation">
                        <strong>Action Required:</strong><br>
                        {action}
                    </div>
"""

                if verification_steps:
                    html += """
                    <div class="verification-steps">
                        <strong>Verification Steps:</strong>
                        <ol>
"""
                    for step in verification_steps:
                        html += f"                            <li>{step}</li>\n"
                    html += """
                        </ol>
                    </div>
"""

                html += """
                </div>
"""

                if pkg['homepage'] or pkg['repository']:
                    html += """
                <div class="links">
"""
                    if pkg['homepage']:
                        html += f"""                    <a href="{pkg['homepage']}" class="link-btn" target="_blank">Homepage</a>"""
                    if pkg['repository']:
                        html += f"""                    <a href="{pkg['repository']}" class="link-btn" target="_blank">Repository</a>"""
                    html += """
                </div>
"""

                html += """
            </div>
"""

            html += """
        </div>
"""

        # Missing section
        if missing_analyses:
            html += """
        <div class="section">
            <h2 class="section-title">❌ Missing Licenses</h2>
            <p style="margin-bottom: 20px; color: #6b7280;">Packages with no license information found in any source</p>
"""
            for item in missing_analyses:
                pkg = item['package']
                analysis = item['analysis']

                suggested = analysis.get('suggested_license', analysis.get('recommendation', 'Unknown'))
                reasoning = analysis.get('reasoning', 'No reasoning provided')
                confidence = analysis.get('confidence', 'Low')
                action = analysis.get('action', 'Manual investigation required')
                risk = analysis.get('risk_level', 'High')
                verification_steps = analysis.get('verification_steps', [])
                github_license_url = analysis.get('github_license_url', '')
                alternative_licenses = analysis.get('alternative_licenses', [])

                html += f"""
            <div class="package-card missing">
                <div class="package-header">
                    <div class="package-name">{pkg['display_name']}</div>
                    <div class="package-type">{pkg['type']}</div>
                </div>

                <div class="license-comparison">
                    <div class="license-source">
                        <div class="license-source-label">ORT</div>
                        <div class="license-value missing">NOASSERTION</div>
                    </div>
                    <div class="license-source">
                        <div class="license-source-label">PyPI API</div>
                        <div class="license-value missing">Not found</div>
                    </div>
                    <div class="license-source">
                        <div class="license-source-label">ScanCode</div>
                        <div class="license-value missing">Not found</div>
                    </div>
                </div>

                <div class="ai-analysis">
                    <div class="ai-label">🤖 AI Suggestion</div>
                    <div class="ai-recommendation">
                        <strong>Suggested License:</strong> {suggested}
                        <span class="confidence confidence-{confidence.lower()}">{confidence} Confidence</span>
                    </div>
                    <div class="ai-recommendation">
                        <strong>Reasoning:</strong><br>
                        {reasoning}
                    </div>
                    <div class="ai-recommendation">
                        <strong>Risk Level:</strong> <span class="confidence confidence-{risk.lower()}">{risk}</span><br>
                        <strong>Action:</strong> {action}
                    </div>
"""

                if alternative_licenses:
                    alt_licenses_text = ', '.join(alternative_licenses)
                    html += f"""
                    <div class="ai-recommendation">
                        <strong>Alternative Licenses to Check:</strong> {alt_licenses_text}
                    </div>
"""

                if verification_steps:
                    html += """
                    <div class="verification-steps">
                        <strong>How to Verify:</strong>
                        <ol>
"""
                    for step in verification_steps:
                        html += f"                            <li>{step}</li>\n"
                    html += """
                        </ol>
                    </div>
"""

                html += """
                </div>
"""

                # Links section for missing packages - include GitHub LICENSE URL if AI provided it
                if pkg['homepage'] or pkg['repository'] or github_license_url:
                    html += """
                <div class="links">
"""
                    if github_license_url:
                        html += f"""                    <a href="{github_license_url}" class="link-btn" target="_blank" style="background: #10b981;">📄 GitHub LICENSE</a>"""
                    if pkg['homepage']:
                        html += f"""                    <a href="{pkg['homepage']}" class="link-btn" target="_blank">Homepage</a>"""
                    if pkg['repository']:
                        html += f"""                    <a href="{pkg['repository']}" class="link-btn" target="_blank">Repository</a>"""
                    html += """
                </div>
"""

                html += """
            </div>
"""

            html += """
        </div>
"""

        html += """
        <div class="footer">
            <p>AI Multi-Layer License Resolution Report</p>
            <p class="ltts-branding">L&T Technology Services - Enhanced ORT Analysis System</p>
            <p style="margin-top: 10px;">Powered by Azure OpenAI GPT-4o-mini + ORT + PyPI API + ScanCode Toolkit</p>
        </div>
    </div>
</body>
</html>
"""

        return html


def main():
    parser = argparse.ArgumentParser(
        description='Generate AI-powered multi-layer license resolution report'
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
        '--uncertain-packages',
        help='Path to uncertain-packages.json'
    )
    parser.add_argument(
        '--output',
        default='ai-multilayer-resolution.html',
        help='Output HTML file path (default: ai-multilayer-resolution.html)'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("AI MULTI-LAYER LICENSE RESOLUTION REPORT")
    print("=" * 80)
    print("\nThis tool uses Azure OpenAI to analyze license conflicts and missing licenses")
    print("across ORT, PyPI API, and ScanCode results.\n")
    print("=" * 80)

    # Create resolver
    resolver = MultiLayerLicenseResolver(
        ort_result_path=args.ort_result,
        pypi_results_path=args.pypi_results,
        scancode_results_dir=args.scancode_dir,
        uncertain_packages_path=args.uncertain_packages
    )

    # Load all data
    resolver.load_all_data()

    # Check if we have issues to analyze
    total_packages = len(resolver.resolved_packages) + len(resolver.conflict_packages) + len(resolver.missing_packages)

    if total_packages == 0:
        print("\n⚠️  No packages found to analyze!")
        sys.exit(1)

    print(f"\n📊 Package Analysis Summary:")
    print(f"   Total packages: {total_packages}")
    print(f"   ✅ Resolved: {len(resolver.resolved_packages)}")
    print(f"   ⚠️  Conflicts: {len(resolver.conflict_packages)}")
    print(f"   ❌ Missing: {len(resolver.missing_packages)}")

    # If only resolved packages, create a simple report showing success
    if not resolver.conflict_packages and not resolver.missing_packages:
        print("\n✅ Excellent! All packages have consistent license information.")
        print("   Generating report showing resolved packages...")

    # Generate report
    resolver.generate_html_report(args.output)

    print("\n" + "=" * 80)
    print("✅ AI resolution report generation complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
