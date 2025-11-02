#!/usr/bin/env python3
"""
Enhanced AI-powered license curation using multi-tool analysis.
Combines results from ORT, ScanCode, and SPDX validation to provide
comprehensive license compliance recommendations.
"""

import json
import yaml
import argparse
import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from openai import AzureOpenAI


class EnhancedAICuration:
    """Enhanced AI curation using multi-tool license analysis"""

    def __init__(self, ort_path: str, spdx_path: str, uncertain_packages_path: str, output_path: str):
        self.ort_path = Path(ort_path)
        self.spdx_path = Path(spdx_path)
        self.uncertain_packages_path = Path(uncertain_packages_path)
        self.output_path = Path(output_path)

        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version="2024-02-15-preview",
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
        )

        self.conflicts = []
        self.uncertain_curations = []
        self.stats = {
            'total_packages': 0,
            'conflicts_found': 0,
            'uncertain_resolved': 0,
            'manual_review_needed': 0
        }

    def load_data(self):
        """Load all analysis data"""
        print("📖 Loading multi-tool analysis data...")

        # Load ORT results
        with open(self.ort_path, 'r') as f:
            self.ort_data = yaml.safe_load(f)
        print(f"   ✓ ORT results loaded")

        # Load SPDX document (enhanced with ScanCode)
        with open(self.spdx_path, 'r') as f:
            if self.spdx_path.suffix in ['.yml', '.yaml']:
                self.spdx_data = yaml.safe_load(f)
            else:
                self.spdx_data = json.load(f)
        print(f"   ✓ SPDX document loaded")

        # Load uncertain packages list
        if self.uncertain_packages_path.exists():
            with open(self.uncertain_packages_path, 'r') as f:
                self.uncertain_packages = json.load(f)
            print(f"   ✓ Uncertain packages list loaded ({len(self.uncertain_packages)} packages)")
        else:
            self.uncertain_packages = []
            print(f"   ⚠️  No uncertain packages file found")

    def analyze_conflicts(self):
        """Find packages with conflicting license information between tools"""
        print("\n🔍 Analyzing license conflicts...")

        for package in self.spdx_data.get('packages', []):
            pkg_name = package.get('name', '')
            declared = package.get('licenseDeclared', 'NOASSERTION')
            concluded = package.get('licenseConcluded', 'NOASSERTION')
            comments = package.get('licenseComments', '')

            # Check for conflicts
            has_conflict = (
                declared != concluded and
                declared not in ['NOASSERTION', 'NONE', ''] and
                concluded not in ['NOASSERTION', 'NONE', '']
            )

            # Check for ScanCode enhancement
            has_scancode = 'ScanCode' in comments

            if has_conflict or (has_scancode and declared == 'NOASSERTION'):
                conflict_info = {
                    'package': pkg_name,
                    'version': package.get('versionInfo', 'unknown'),
                    'spdx_id': package.get('SPDXID', ''),
                    'declared': declared,
                    'concluded': concluded,
                    'scancode_enhanced': has_scancode,
                    'comments': comments,
                    'homepage': package.get('homepage', ''),
                    'download_location': package.get('downloadLocation', '')
                }

                self.conflicts.append(conflict_info)
                self.stats['conflicts_found'] += 1

        print(f"   Found {len(self.conflicts)} packages with license conflicts or uncertainties")

    def get_ai_recommendation(self, conflict: Dict) -> Dict:
        """Get AI-powered license recommendation for a conflict"""

        # Build detailed prompt
        prompt = f"""Analyze this license compliance issue for package '{conflict['package']}' version {conflict['version']}:

**License Information:**
- Declared License (from package metadata): {conflict['declared']}
- Concluded License (from source code analysis): {conflict['concluded']}
- ScanCode Enhanced: {conflict['scancode_enhanced']}
- Additional Info: {conflict['comments']}

**Package Information:**
- Homepage: {conflict['homepage']}
- Download Location: {conflict['download_location']}

**Analysis Required:**
1. What is the most likely correct license for this package?
2. Explain the discrepancy between declared and concluded licenses
3. What is the recommended action? (accept concluded license, investigate further, contact maintainer, or add to curation database)
4. What is the compliance risk level? (low/medium/high)
5. Are there any specific compliance concerns or license compatibility issues?

Provide a clear, actionable recommendation."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior software license compliance expert with deep knowledge of open source licenses, SPDX identifiers, and license compatibility. Provide clear, actionable recommendations for license compliance issues."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )

            recommendation = response.choices[0].message.content

            # Parse recommendation to extract key information
            risk_level = 'medium'
            if 'high risk' in recommendation.lower() or 'critical' in recommendation.lower():
                risk_level = 'high'
            elif 'low risk' in recommendation.lower() or 'minimal' in recommendation.lower():
                risk_level = 'low'

            recommended_action = 'investigate'
            if 'accept' in recommendation.lower() and 'concluded' in recommendation.lower():
                recommended_action = 'accept_concluded'
            elif 'contact maintainer' in recommendation.lower():
                recommended_action = 'contact_maintainer'
            elif 'manual review' in recommendation.lower():
                recommended_action = 'manual_review'

            return {
                'full_analysis': recommendation,
                'risk_level': risk_level,
                'recommended_action': recommended_action,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"   ⚠️  AI analysis failed for {conflict['package']}: {e}")
            return {
                'full_analysis': f"AI analysis unavailable: {str(e)}",
                'risk_level': 'unknown',
                'recommended_action': 'manual_review',
                'timestamp': datetime.now().isoformat()
            }

    def curate_with_ai(self):
        """Apply AI curation to conflicts"""
        print(f"\n🤖 Running AI-powered curation analysis...")

        # Limit to most critical conflicts to avoid token limits
        conflicts_to_analyze = self.conflicts[:20]

        if len(self.conflicts) > 20:
            print(f"   Analyzing top 20 conflicts (of {len(self.conflicts)} total)")

        for i, conflict in enumerate(conflicts_to_analyze, 1):
            print(f"   Analyzing {i}/{len(conflicts_to_analyze)}: {conflict['package']}...")

            recommendation = self.get_ai_recommendation(conflict)

            curation = {
                'conflict': conflict,
                'ai_recommendation': recommendation
            }

            self.uncertain_curations.append(curation)

            if recommendation['recommended_action'] == 'manual_review':
                self.stats['manual_review_needed'] += 1
            else:
                self.stats['uncertain_resolved'] += 1

        print(f"   ✓ AI analysis complete for {len(conflicts_to_analyze)} packages")

    def generate_html_report(self):
        """Generate comprehensive HTML report with AI recommendations"""
        print(f"\n📄 Generating enhanced curation report...")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced License Curation Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            padding: 40px;
        }}

        h1 {{
            color: #2d3748;
            border-bottom: 4px solid #667eea;
            padding-bottom: 15px;
            margin-bottom: 30px;
            font-size: 2.5rem;
        }}

        h2 {{
            color: #4a5568;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 1.8rem;
        }}

        .summary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}

        .summary h2 {{
            color: white;
            margin-top: 0;
        }}

        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .stat {{
            background: rgba(255,255,255,0.2);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}

        .stat-value {{
            font-size: 2.5rem;
            font-weight: bold;
            display: block;
        }}

        .stat-label {{
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 5px;
        }}

        .curation-card {{
            background: #f8f9fa;
            border-left: 6px solid #ffc107;
            padding: 25px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
            transition: transform 0.2s;
        }}

        .curation-card:hover {{
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        .curation-card.risk-high {{
            border-left-color: #dc3545;
        }}

        .curation-card.risk-medium {{
            border-left-color: #ffc107;
        }}

        .curation-card.risk-low {{
            border-left-color: #28a745;
        }}

        .package-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}

        .package-name {{
            font-size: 1.4rem;
            font-weight: 700;
            color: #2d3748;
        }}

        .risk-badge {{
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .risk-high {{ background: #fee; color: #c00; }}
        .risk-medium {{ background: #fff3cd; color: #856404; }}
        .risk-low {{ background: #d4edda; color: #155724; }}

        .license-info {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
            border: 1px solid #e2e8f0;
        }}

        .license-row {{
            display: grid;
            grid-template-columns: 150px 1fr;
            gap: 15px;
            margin: 8px 0;
        }}

        .license-label {{
            font-weight: 600;
            color: #4a5568;
        }}

        .license-value {{
            font-family: 'Courier New', monospace;
            color: #2d3748;
            background: #f7fafc;
            padding: 4px 8px;
            border-radius: 4px;
        }}

        .ai-analysis {{
            background: linear-gradient(to right, #e0f2fe, #f0f9ff);
            border-left: 4px solid #3b82f6;
            padding: 20px;
            margin: 15px 0;
            border-radius: 0 6px 6px 0;
        }}

        .ai-analysis h3 {{
            color: #1e40af;
            margin-bottom: 12px;
            font-size: 1.1rem;
        }}

        .ai-text {{
            white-space: pre-wrap;
            font-family: Georgia, serif;
            color: #1e293b;
            line-height: 1.7;
        }}

        .action-recommendation {{
            background: #fffbeb;
            border: 2px solid #f59e0b;
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
        }}

        .action-recommendation strong {{
            color: #92400e;
        }}

        .metadata {{
            color: #718096;
            font-size: 0.9rem;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e2e8f0;
        }}

        .tool-badge {{
            display: inline-block;
            background: #e6fffa;
            color: #234e52;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.8rem;
            margin-right: 8px;
            font-weight: 500;
        }}

        .footer {{
            margin-top: 50px;
            padding-top: 30px;
            border-top: 2px solid #e2e8f0;
            text-align: center;
            color: #718096;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Enhanced License Curation Report</h1>

        <div class="summary">
            <h2>Executive Summary</h2>
            <div class="stat-grid">
                <div class="stat">
                    <span class="stat-value">{self.stats['conflicts_found']}</span>
                    <span class="stat-label">License Conflicts Found</span>
                </div>
                <div class="stat">
                    <span class="stat-value">{self.stats['uncertain_resolved']}</span>
                    <span class="stat-label">AI Recommendations Generated</span>
                </div>
                <div class="stat">
                    <span class="stat-value">{self.stats['manual_review_needed']}</span>
                    <span class="stat-label">Require Manual Review</span>
                </div>
                <div class="stat">
                    <span class="stat-value">{len([c for c in self.uncertain_curations if c['ai_recommendation']['risk_level'] == 'high'])}</span>
                    <span class="stat-label">High Risk Issues</span>
                </div>
            </div>
        </div>

        <p><strong>Analysis Tools Used:</strong></p>
        <p>
            <span class="tool-badge">ORT Analyzer</span>
            <span class="tool-badge">ScanCode Toolkit</span>
            <span class="tool-badge">SPDX Validation</span>
            <span class="tool-badge">Azure OpenAI GPT-4</span>
        </p>

        <h2>📋 License Conflicts & AI Recommendations</h2>
        <p>The following packages have license discrepancies that require attention. Each has been analyzed by AI to provide recommendations.</p>
"""

        # Add each curation with AI analysis
        for curation in self.uncertain_curations:
            conflict = curation['conflict']
            ai_rec = curation['ai_recommendation']

            html += f"""
        <div class="curation-card risk-{ai_rec['risk_level']}">
            <div class="package-header">
                <div class="package-name">📦 {conflict['package']} <span style="font-size: 1rem; color: #718096;">v{conflict['version']}</span></div>
                <div class="risk-badge risk-{ai_rec['risk_level']}">{ai_rec['risk_level']} Risk</div>
            </div>

            <div class="license-info">
                <div class="license-row">
                    <div class="license-label">Declared License:</div>
                    <div class="license-value">{conflict['declared']}</div>
                </div>
                <div class="license-row">
                    <div class="license-label">Concluded License:</div>
                    <div class="license-value">{conflict['concluded']}</div>
                </div>
                <div class="license-row">
                    <div class="license-label">ScanCode Enhanced:</div>
                    <div class="license-value">{'✅ Yes' if conflict['scancode_enhanced'] else '❌ No'}</div>
                </div>
            </div>

            <div class="ai-analysis">
                <h3>🤖 AI Analysis & Recommendation</h3>
                <div class="ai-text">{ai_rec['full_analysis']}</div>
            </div>

            <div class="action-recommendation">
                <strong>💡 Recommended Action:</strong> {ai_rec['recommended_action'].replace('_', ' ').title()}
            </div>

            <div class="metadata">
                <strong>SPDX ID:</strong> {conflict['spdx_id']}<br>
                <strong>Homepage:</strong> {conflict['homepage'] if conflict['homepage'] else 'N/A'}<br>
                <strong>Analysis Date:</strong> {ai_rec['timestamp']}
            </div>
        </div>
"""

        # Add remaining conflicts without AI analysis
        if len(self.conflicts) > len(self.uncertain_curations):
            remaining = len(self.conflicts) - len(self.uncertain_curations)
            html += f"""
        <h2>⚠️ Additional Conflicts Requiring Review</h2>
        <p>The following {remaining} packages also have license conflicts but were not included in the AI analysis due to token limits. They require manual review:</p>
        <ul>
"""
            for conflict in self.conflicts[len(self.uncertain_curations):]:
                html += f"<li><strong>{conflict['package']}</strong> v{conflict['version']} - Declared: {conflict['declared']}, Concluded: {conflict['concluded']}</li>\n"

            html += "</ul>\n"

        # Close HTML
        html += f"""
        <div class="footer">
            <p><strong>Report Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Enhanced License Curation System - Multi-Tool Analysis with AI</p>
        </div>
    </div>
</body>
</html>
"""

        # Save report
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"   ✅ Report saved to: {self.output_path}")

    def print_summary(self):
        """Print analysis summary"""
        print("\n" + "="*70)
        print("📊 ENHANCED CURATION SUMMARY")
        print("="*70)
        print(f"Total conflicts found: {self.stats['conflicts_found']}")
        print(f"AI recommendations generated: {self.stats['uncertain_resolved']}")
        print(f"Manual review required: {self.stats['manual_review_needed']}")
        print(f"\nRisk breakdown:")
        print(f"  High risk: {len([c for c in self.uncertain_curations if c['ai_recommendation']['risk_level'] == 'high'])}")
        print(f"  Medium risk: {len([c for c in self.uncertain_curations if c['ai_recommendation']['risk_level'] == 'medium'])}")
        print(f"  Low risk: {len([c for c in self.uncertain_curations if c['ai_recommendation']['risk_level'] == 'low'])}")
        print("="*70)

    def run(self):
        """Execute enhanced curation workflow"""
        self.load_data()
        self.analyze_conflicts()

        if self.conflicts:
            self.curate_with_ai()

        self.generate_html_report()
        self.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced AI-powered license curation with multi-tool analysis'
    )
    parser.add_argument(
        '--ort-results',
        required=True,
        help='Path to ORT analyzer-result.yml'
    )
    parser.add_argument(
        '--spdx-doc',
        required=True,
        help='Path to enhanced SPDX document (after ScanCode merge)'
    )
    parser.add_argument(
        '--uncertain-packages',
        required=True,
        help='Path to uncertain-packages.json from extraction step'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output path for HTML report'
    )

    args = parser.parse_args()

    # Check for required environment variables
    if not os.getenv('AZURE_OPENAI_API_KEY') or not os.getenv('AZURE_OPENAI_ENDPOINT'):
        print("❌ Error: AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables must be set")
        exit(1)

    curation = EnhancedAICuration(
        args.ort_results,
        args.spdx_doc,
        args.uncertain_packages,
        args.output
    )

    curation.run()

    print(f"\n✅ Enhanced curation complete! View report at: {args.output}")


if __name__ == '__main__':
    main()
