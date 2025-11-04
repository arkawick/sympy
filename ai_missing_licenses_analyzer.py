#!/usr/bin/env python3
"""
AI-Powered Missing Licenses Analyzer

Uses Azure OpenAI to research and suggest licenses for packages with missing/blank licenses.
"""

import json
import yaml
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from openai import AzureOpenAI

class MissingLicensesAnalyzer:
    """Analyzes packages with missing licenses using AI"""

    def __init__(self):
        """Initialize Azure OpenAI client"""
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT', 'https://ltts-openai-poc.openai.azure.com/')

        if not self.api_key:
            raise ValueError("AZURE_OPENAI_API_KEY environment variable not set")

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version="2025-01-01-preview",
            azure_endpoint=self.endpoint
        )

        self.packages_analyzed = []

    def load_ort_results(self, ort_file: str) -> Dict:
        """Load ORT analyzer results"""
        with open(ort_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def load_uncertain_packages(self, uncertain_file: str) -> List[Dict]:
        """Load uncertain packages JSON"""
        if not os.path.exists(uncertain_file):
            return []

        with open(uncertain_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def is_missing_license(self, pkg: Dict) -> bool:
        """Check if package has missing/blank license"""
        declared = pkg.get('declared_licenses', [])
        concluded = pkg.get('concluded_license', '')

        # Missing if no declared licenses or only uncertain ones
        if not declared:
            return True

        uncertain_values = {'NOASSERTION', 'NONE', 'UNKNOWN', 'NOT-FOUND', '', 'NULL'}

        if all(lic in uncertain_values for lic in declared):
            return True

        # Also missing if concluded is uncertain and no valid declared
        if concluded in uncertain_values and all(lic in uncertain_values for lic in declared):
            return True

        return False

    def get_package_registry_url(self, pkg: Dict) -> Optional[str]:
        """Generate package registry URL"""
        pkg_id = pkg.get('id', '')
        pkg_type = pkg_id.split(':')[0] if ':' in pkg_id else ''
        name = pkg.get('name', '')

        if pkg_type == 'NPM':
            return f"https://www.npmjs.com/package/{name}"
        elif pkg_type == 'PyPI':
            return f"https://pypi.org/project/{name}"
        elif pkg_type == 'Maven':
            namespace = pkg.get('namespace', '')
            if namespace:
                return f"https://search.maven.org/artifact/{namespace}/{name}"
        elif pkg_type == 'NuGet':
            return f"https://www.nuget.org/packages/{name}"
        elif pkg_type == 'Gem':
            return f"https://rubygems.org/gems/{name}"

        return None

    def analyze_package_with_ai(self, pkg: Dict) -> Dict:
        """Use Azure OpenAI to suggest license for package"""
        pkg_id = pkg.get('id', 'unknown')
        pkg_name = pkg.get('name', 'unknown')
        pkg_type = pkg_id.split(':')[0] if ':' in pkg_id else 'unknown'
        homepage = pkg.get('homepage_url', '')
        vcs_url = pkg.get('vcs_url', '')
        description = pkg.get('description', '')

        prompt = f"""You are a software license compliance expert. Analyze this package and suggest the most likely license.

Package Information:
- ID: {pkg_id}
- Name: {pkg_name}
- Type: {pkg_type}
- Homepage: {homepage}
- Repository: {vcs_url}
- Description: {description}

The package currently has NO license information in its metadata.

Please provide:
1. Most Likely License: Based on the package type, name, and common patterns (provide SPDX identifier)
2. Confidence Level: High/Medium/Low
3. Reasoning: Why you think this is the likely license
4. Verification Steps: How to manually verify the license
5. Alternative Licenses: Other possible licenses to check
6. Risk Assessment: What are the risks if this license is incorrect

Format your response as JSON with these exact fields:
{{
    "suggested_license": "SPDX-ID",
    "confidence": "High|Medium|Low",
    "reasoning": "explanation",
    "verification_steps": ["step1", "step2"],
    "alternative_licenses": ["license1", "license2"],
    "risk_level": "Low|Medium|High",
    "risk_explanation": "explanation"
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a software license compliance expert. Provide accurate, conservative license suggestions. Always output valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            content = response.choices[0].message.content.strip()

            # Try to parse JSON from response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            result = json.loads(content)
            result['package'] = pkg_name
            result['package_id'] = pkg_id
            result['homepage'] = homepage
            result['vcs_url'] = vcs_url
            result['registry_url'] = self.get_package_registry_url(pkg)

            return result

        except Exception as e:
            print(f"Error analyzing {pkg_name}: {e}")
            return {
                'package': pkg_name,
                'package_id': pkg_id,
                'suggested_license': 'NOASSERTION',
                'confidence': 'Low',
                'reasoning': f'AI analysis failed: {str(e)}',
                'verification_steps': ['Manual verification required'],
                'alternative_licenses': [],
                'risk_level': 'High',
                'risk_explanation': 'License could not be determined automatically',
                'homepage': homepage,
                'vcs_url': vcs_url,
                'registry_url': self.get_package_registry_url(pkg)
            }

    def generate_html_report(self, analyses: List[Dict], output_file: str):
        """Generate HTML report with AI suggestions"""

        total_packages = len(analyses)
        high_confidence = sum(1 for a in analyses if a['confidence'] == 'High')
        medium_confidence = sum(1 for a in analyses if a['confidence'] == 'Medium')
        low_confidence = sum(1 for a in analyses if a['confidence'] == 'Low')

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Missing Licenses Analysis - AI Recommendations</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 20px;
    }}
    .container {{
      max-width: 1400px;
      margin: 0 auto;
      background: white;
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
      padding: 40px;
    }}
    h1 {{
      color: #2d3748;
      margin-bottom: 10px;
      font-size: 2.5rem;
    }}
    .subtitle {{
      color: #718096;
      margin-bottom: 30px;
      font-size: 1.1rem;
    }}
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
      margin-bottom: 40px;
    }}
    .stat-card {{
      background: linear-gradient(135deg, #667eea, #764ba2);
      padding: 20px;
      border-radius: 8px;
      color: white;
    }}
    .stat-value {{
      font-size: 2.5rem;
      font-weight: bold;
      margin-bottom: 8px;
    }}
    .stat-label {{
      font-size: 0.95rem;
      opacity: 0.9;
    }}
    .package-card {{
      background: #f7fafc;
      border-left: 4px solid #667eea;
      border-radius: 8px;
      padding: 24px;
      margin-bottom: 20px;
    }}
    .package-header {{
      display: flex;
      justify-content: space-between;
      align-items: start;
      margin-bottom: 16px;
    }}
    .package-name {{
      font-size: 1.3rem;
      color: #2d3748;
      font-weight: 600;
    }}
    .package-id {{
      font-size: 0.85rem;
      color: #a0aec0;
      margin-top: 4px;
    }}
    .confidence-badge {{
      padding: 6px 16px;
      border-radius: 20px;
      font-size: 0.85rem;
      font-weight: 600;
    }}
    .confidence-high {{
      background: #c6f6d5;
      color: #22543d;
    }}
    .confidence-medium {{
      background: #feebc8;
      color: #7c2d12;
    }}
    .confidence-low {{
      background: #fed7d7;
      color: #742a2a;
    }}
    .suggestion-box {{
      background: white;
      border: 2px solid #e2e8f0;
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 16px;
    }}
    .suggestion-header {{
      font-size: 1.1rem;
      font-weight: 600;
      color: #2d3748;
      margin-bottom: 12px;
    }}
    .license-suggestion {{
      display: inline-block;
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      padding: 8px 20px;
      border-radius: 6px;
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 12px;
    }}
    .reasoning {{
      color: #4a5568;
      line-height: 1.6;
      margin-bottom: 16px;
    }}
    .steps-list {{
      list-style: none;
      padding: 0;
    }}
    .steps-list li {{
      padding: 8px 0;
      padding-left: 24px;
      position: relative;
      color: #4a5568;
    }}
    .steps-list li:before {{
      content: "→";
      position: absolute;
      left: 0;
      color: #667eea;
      font-weight: bold;
    }}
    .risk-box {{
      background: #fff5f5;
      border-left: 4px solid #fc8181;
      padding: 16px;
      border-radius: 4px;
      margin-top: 16px;
    }}
    .risk-box.risk-medium {{
      background: #fffaf0;
      border-left-color: #f6ad55;
    }}
    .risk-box.risk-low {{
      background: #f0fff4;
      border-left-color: #68d391;
    }}
    .links {{
      display: flex;
      gap: 12px;
      margin-top: 16px;
      flex-wrap: wrap;
    }}
    .link-btn {{
      display: inline-block;
      background: #667eea;
      color: white;
      padding: 8px 16px;
      border-radius: 6px;
      text-decoration: none;
      font-size: 0.9rem;
      transition: background 0.2s;
    }}
    .link-btn:hover {{
      background: #5568d3;
    }}
    .curation-command {{
      background: #2d3748;
      color: #68d391;
      padding: 16px;
      border-radius: 6px;
      font-family: 'Courier New', monospace;
      font-size: 0.9rem;
      overflow-x: auto;
      margin-top: 16px;
    }}
    .timestamp {{
      color: #a0aec0;
      font-size: 0.9rem;
      margin-top: 40px;
      text-align: center;
    }}
    .alternatives {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 8px;
    }}
    .alt-license {{
      background: #edf2f7;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 0.85rem;
      color: #2d3748;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>🔍 Missing Licenses Analysis</h1>
    <p class="subtitle">AI-Powered License Suggestions & Verification Guide</p>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{total_packages}</div>
        <div class="stat-label">Packages Analyzed</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{high_confidence}</div>
        <div class="stat-label">High Confidence</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{medium_confidence}</div>
        <div class="stat-label">Medium Confidence</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{low_confidence}</div>
        <div class="stat-label">Low Confidence</div>
      </div>
    </div>

    <h2 style="margin-bottom: 20px; color: #2d3748;">AI License Recommendations</h2>
'''

        for analysis in analyses:
            pkg_name = analysis['package']
            pkg_id = analysis['package_id']
            suggested = analysis['suggested_license']
            confidence = analysis['confidence']
            reasoning = analysis['reasoning']
            verification_steps = analysis.get('verification_steps', [])
            alternatives = analysis.get('alternative_licenses', [])
            risk_level = analysis.get('risk_level', 'Medium')
            risk_explanation = analysis.get('risk_explanation', '')
            homepage = analysis.get('homepage', '')
            vcs_url = analysis.get('vcs_url', '')
            registry_url = analysis.get('registry_url', '')

            confidence_class = f"confidence-{confidence.lower()}"
            risk_class = f"risk-{risk_level.lower()}"

            html += f'''
    <div class="package-card">
      <div class="package-header">
        <div>
          <div class="package-name">{pkg_name}</div>
          <div class="package-id">{pkg_id}</div>
        </div>
        <span class="confidence-badge {confidence_class}">{confidence} Confidence</span>
      </div>

      <div class="suggestion-box">
        <div class="suggestion-header">Suggested License:</div>
        <div class="license-suggestion">{suggested}</div>
        <div class="reasoning">{reasoning}</div>
'''

            if alternatives:
                html += '''
        <div style="margin-top: 12px;">
          <strong style="color: #4a5568; font-size: 0.9rem;">Alternative licenses to check:</strong>
          <div class="alternatives">
'''
                for alt in alternatives:
                    html += f'            <span class="alt-license">{alt}</span>\n'
                html += '''
          </div>
        </div>
'''

            html += '''
      </div>
'''

            if verification_steps:
                html += '''
      <div class="suggestion-box">
        <div class="suggestion-header">Verification Steps:</div>
        <ol class="steps-list">
'''
                for step in verification_steps:
                    html += f'          <li>{step}</li>\n'
                html += '''
        </ol>
      </div>
'''

            html += f'''
      <div class="risk-box {risk_class}">
        <strong>Risk Level: {risk_level}</strong><br>
        {risk_explanation}
      </div>

      <div class="links">
'''

            if registry_url:
                html += f'        <a href="{registry_url}" class="link-btn" target="_blank">📦 Package Registry</a>\n'
            if homepage:
                html += f'        <a href="{homepage}" class="link-btn" target="_blank">🏠 Homepage</a>\n'
            if vcs_url:
                html += f'        <a href="{vcs_url}" class="link-btn" target="_blank">📁 Repository</a>\n'

            html += '''
      </div>

      <div class="curation-command">
python manage_curations.py add \\<br>
&nbsp;&nbsp;--id "{pkg_id}" \\<br>
&nbsp;&nbsp;--license "{suggested}" \\<br>
&nbsp;&nbsp;--comment "Verified from [source]" \\<br>
&nbsp;&nbsp;--original-license "NOASSERTION"
      </div>
    </div>
'''.format(pkg_id=pkg_id, suggested=suggested)

        html += f'''
    <div class="timestamp">
      Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")} using Azure OpenAI GPT-4
    </div>
  </div>
</body>
</html>
'''

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ Missing licenses analysis report generated: {output_file}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python ai_missing_licenses_analyzer.py <uncertain-packages.json> <output.html>")
        sys.exit(1)

    uncertain_file = sys.argv[1]
    output_file = sys.argv[2]

    print("🤖 Starting AI-powered missing licenses analysis...")

    analyzer = MissingLicensesAnalyzer()

    # Load uncertain packages
    print(f"Loading uncertain packages from: {uncertain_file}")
    uncertain_packages = analyzer.load_uncertain_packages(uncertain_file)

    if not uncertain_packages:
        print("⚠️  No uncertain packages found")
        # Generate empty report
        analyzer.generate_html_report([], output_file)
        return

    # Filter to only packages with missing/blank licenses
    missing_license_packages = [pkg for pkg in uncertain_packages if analyzer.is_missing_license(pkg)]

    print(f"Found {len(missing_license_packages)} packages with missing/blank licenses")

    if not missing_license_packages:
        print("✅ No packages with missing licenses - all packages have license declarations")
        analyzer.generate_html_report([], output_file)
        return

    # Limit to first 15 packages to avoid token limits and cost
    if len(missing_license_packages) > 15:
        print(f"⚠️  Limiting analysis to first 15 packages (of {len(missing_license_packages)})")
        missing_license_packages = missing_license_packages[:15]

    # Analyze each package with AI
    analyses = []
    for i, pkg in enumerate(missing_license_packages, 1):
        print(f"Analyzing {i}/{len(missing_license_packages)}: {pkg['name']}")
        analysis = analyzer.analyze_package_with_ai(pkg)
        analyses.append(analysis)

    # Generate report
    analyzer.generate_html_report(analyses, output_file)

    print(f"✅ Analysis complete! Analyzed {len(analyses)} packages")
    print(f"   Report: {output_file}")

if __name__ == '__main__':
    main()
