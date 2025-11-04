#!/usr/bin/env python3
"""Generate consolidated ScanCode HTML and YAML reports from JSON scan results"""

import json
import yaml
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def load_scancode_results(scancode_dir: str) -> List[Dict]:
    """Load all ScanCode JSON results"""
    results = []
    scancode_path = Path(scancode_dir)

    if not scancode_path.exists():
        print(f"Warning: ScanCode directory '{scancode_dir}' not found")
        return results

    for json_file in scancode_path.glob('*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results.append({
                    'package': json_file.stem,
                    'scan_data': data
                })
        except Exception as e:
            print(f"Error loading {json_file}: {e}")

    return results

def analyze_package(scan_data: Dict) -> Dict:
    """Analyze a single package's scan results"""
    licenses = {}
    copyrights = set()
    file_count = 0
    files_with_licenses = 0

    for file_info in scan_data.get('files', []):
        if file_info.get('type') == 'file':
            file_count += 1

            # Collect licenses
            file_licenses = file_info.get('licenses', [])
            if file_licenses:
                files_with_licenses += 1
                for lic in file_licenses:
                    spdx_id = lic.get('spdx_license_key', lic.get('key', 'Unknown'))
                    score = lic.get('score', 0.0)

                    if spdx_id not in licenses:
                        licenses[spdx_id] = {
                            'count': 0,
                            'max_score': 0.0,
                            'files': []
                        }

                    licenses[spdx_id]['count'] += 1
                    licenses[spdx_id]['max_score'] = max(licenses[spdx_id]['max_score'], score)
                    licenses[spdx_id]['files'].append(file_info.get('path', ''))

            # Collect copyrights
            for copyright_info in file_info.get('copyrights', []):
                copyright_text = copyright_info.get('copyright', '').strip()
                if copyright_text:
                    copyrights.add(copyright_text)

    return {
        'total_files': file_count,
        'files_with_licenses': files_with_licenses,
        'licenses': licenses,
        'copyrights': list(copyrights)
    }

def generate_yaml_report(results: List[Dict], output_file: str):
    """Generate YAML summary report"""
    summary = {
        'scancode_summary': {
            'generated_at': datetime.now().isoformat(),
            'total_packages_scanned': len(results),
            'packages': []
        }
    }

    for result in results:
        pkg_name = result['package']
        analysis = analyze_package(result['scan_data'])

        # Format licenses for YAML
        license_list = []
        for lic_id, lic_info in analysis['licenses'].items():
            license_list.append({
                'license': lic_id,
                'file_count': lic_info['count'],
                'confidence': f"{lic_info['max_score']:.1f}%",
                'sample_files': lic_info['files'][:3]  # Top 3 files
            })

        summary['scancode_summary']['packages'].append({
            'package': pkg_name,
            'files_scanned': analysis['total_files'],
            'files_with_licenses': analysis['files_with_licenses'],
            'detected_licenses': license_list,
            'copyright_statements': analysis['copyrights'][:5]  # Top 5
        })

    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(summary, f, default_flow_style=False, sort_keys=False)

    print(f"✅ Generated YAML report: {output_file}")

def generate_html_report(results: List[Dict], output_file: str):
    """Generate HTML summary report"""

    # Calculate overall statistics
    total_packages = len(results)
    total_licenses = set()
    total_files = 0

    package_summaries = []

    for result in results:
        pkg_name = result['package']
        analysis = analyze_package(result['scan_data'])

        total_files += analysis['total_files']
        total_licenses.update(analysis['licenses'].keys())

        # Sort licenses by confidence
        sorted_licenses = sorted(
            analysis['licenses'].items(),
            key=lambda x: x[1]['max_score'],
            reverse=True
        )

        package_summaries.append({
            'name': pkg_name,
            'analysis': analysis,
            'sorted_licenses': sorted_licenses
        })

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ScanCode Toolkit Analysis Report</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 20px;
    }}
    .container {{
      max-width: 1200px;
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
      border: 2px solid #e2e8f0;
      border-radius: 8px;
      padding: 24px;
      margin-bottom: 20px;
    }}
    .package-name {{
      font-size: 1.5rem;
      color: #2d3748;
      font-weight: 600;
      margin-bottom: 16px;
    }}
    .package-stats {{
      display: flex;
      gap: 24px;
      margin-bottom: 16px;
      color: #4a5568;
      font-size: 0.95rem;
    }}
    .license-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 16px;
    }}
    .license-table th {{
      background: #edf2f7;
      padding: 12px;
      text-align: left;
      font-weight: 600;
      color: #2d3748;
    }}
    .license-table td {{
      padding: 10px 12px;
      border-bottom: 1px solid #e2e8f0;
    }}
    .confidence-high {{ color: #38a169; font-weight: 600; }}
    .confidence-medium {{ color: #d69e2e; font-weight: 600; }}
    .confidence-low {{ color: #e53e3e; font-weight: 600; }}
    .badge {{
      display: inline-block;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 0.85rem;
      font-weight: 600;
      background: #667eea;
      color: white;
    }}
    .timestamp {{
      color: #a0aec0;
      font-size: 0.9rem;
      margin-top: 40px;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>📊 ScanCode Toolkit Analysis</h1>
    <p class="subtitle">Deep License Detection & Copyright Analysis</p>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{total_packages}</div>
        <div class="stat-label">Packages Scanned</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{len(total_licenses)}</div>
        <div class="stat-label">Unique Licenses</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{total_files}</div>
        <div class="stat-label">Files Analyzed</div>
      </div>
    </div>

    <h2 style="margin-bottom: 20px; color: #2d3748;">Package Analysis Results</h2>
'''

    for pkg_summary in package_summaries:
        pkg_name = pkg_summary['name']
        analysis = pkg_summary['analysis']
        sorted_licenses = pkg_summary['sorted_licenses']

        coverage_pct = (analysis['files_with_licenses'] / analysis['total_files'] * 100) if analysis['total_files'] > 0 else 0

        html += f'''
    <div class="package-card">
      <div class="package-name">{pkg_name}</div>
      <div class="package-stats">
        <span><strong>Files:</strong> {analysis['total_files']}</span>
        <span><strong>Licensed:</strong> {analysis['files_with_licenses']}</span>
        <span><strong>Coverage:</strong> {coverage_pct:.1f}%</span>
        <span><strong>Licenses:</strong> {len(analysis['licenses'])}</span>
      </div>
'''

        if sorted_licenses:
            html += '''
      <table class="license-table">
        <thead>
          <tr>
            <th>License</th>
            <th>Files</th>
            <th>Confidence</th>
            <th>Sample Paths</th>
          </tr>
        </thead>
        <tbody>
'''
            for lic_id, lic_info in sorted_licenses[:10]:  # Top 10 licenses
                confidence = lic_info['max_score']
                confidence_class = 'confidence-high' if confidence >= 90 else 'confidence-medium' if confidence >= 70 else 'confidence-low'
                sample_files = ', '.join([Path(f).name for f in lic_info['files'][:3]])

                html += f'''
          <tr>
            <td><span class="badge">{lic_id}</span></td>
            <td>{lic_info['count']}</td>
            <td class="{confidence_class}">{confidence:.1f}%</td>
            <td style="font-size: 0.85rem; color: #718096;">{sample_files}</td>
          </tr>
'''
            html += '''
        </tbody>
      </table>
'''
        else:
            html += '<p style="color: #a0aec0; font-style: italic;">No licenses detected</p>'

        html += '''
    </div>
'''

    html += f'''
    <div class="timestamp">
      Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
    </div>
  </div>
</body>
</html>
'''

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Generated HTML report: {output_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_scancode_reports.py <scancode-results-dir>")
        sys.exit(1)

    scancode_dir = sys.argv[1]

    print(f"Loading ScanCode results from: {scancode_dir}")
    results = load_scancode_results(scancode_dir)

    if not results:
        print("⚠️  No ScanCode results found. Creating empty reports...")
        results = []

    print(f"Found {len(results)} ScanCode result files")

    # Generate reports
    generate_yaml_report(results, 'scancode-summary.yml')
    generate_html_report(results, 'scancode-summary.html')

    print("✅ ScanCode reports generation complete")

if __name__ == '__main__':
    main()
