#!/usr/bin/env python3
"""Generate landing page for GitHub Pages deployment"""

import sys
import os
from pathlib import Path

def generate_landing_page(public_dir='public'):
    """Generate index.html landing page for ORT reports"""

    public_path = Path(public_dir)

    # Detect available files
    webapp_file = ''
    ai_report = ''
    cyclonedx = ''
    spdx_enhanced = ''
    spdx_original = ''
    uncertain_report = ''

    # Find files
    for file in public_path.glob('*web-app*.html'):
        webapp_file = file.name
        break

    if (public_path / 'curation-report-enhanced.html').exists():
        ai_report = 'curation-report-enhanced.html'

    if (public_path / 'bom.cyclonedx.json').exists():
        cyclonedx = 'bom.cyclonedx.json'

    if (public_path / 'bom-enhanced.spdx.json').exists():
        spdx_enhanced = 'bom-enhanced.spdx.json'

    if (public_path / 'bom.spdx.yml').exists():
        spdx_original = 'bom.spdx.yml'

    if (public_path / 'uncertain-packages-report.md').exists():
        uncertain_report = 'uncertain-packages-report.md'

    print(f"✅ Detected files:")
    print(f"  WebApp: {webapp_file or 'N/A'}")
    print(f"  AI Report: {ai_report or 'N/A'}")
    print(f"  CycloneDX: {cyclonedx or 'N/A'}")
    print(f"  SPDX Enhanced: {spdx_enhanced or 'N/A'}")
    print(f"  SPDX Original: {spdx_original or 'N/A'}")
    print(f"  Uncertain Report: {uncertain_report or 'N/A'}")

    # Generate HTML
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Enhanced ORT Analysis Reports</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, rgba(102,126,234,0.9), rgba(118,75,162,0.9)),
                  url('background.jpg') no-repeat center center fixed;
      background-size: cover;
      min-height: 100vh;
      padding: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .container {
      background: white;
      border-radius: 16px;
      padding: 40px;
      max-width: 1000px;
      width: 100%;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    h1 {
      color: #2d3748;
      margin-bottom: 10px;
      font-size: 2.5rem;
    }
    .subtitle {
      color: #718096;
      margin-bottom: 30px;
      font-size: 1.1rem;
    }
    .badge {
      display: inline-block;
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      padding: 6px 16px;
      border-radius: 20px;
      font-size: 0.75rem;
      font-weight: 600;
      margin-left: 8px;
    }
    .report-grid {
      display: grid;
      gap: 16px;
      margin-top: 30px;
    }
    .report-card {
      background: #f7fafc;
      border: 2px solid #e2e8f0;
      border-radius: 12px;
      padding: 24px;
      transition: all 0.3s;
      text-decoration: none;
      display: block;
    }
    .report-card:hover {
      border-color: #667eea;
      box-shadow: 0 4px 12px rgba(102,126,234,0.2);
      transform: translateY(-2px);
    }
    .highlight {
      background: linear-gradient(135deg, #667eea, #764ba2);
      border: none;
    }
    .highlight .report-title,
    .highlight .report-desc {
      color: white;
    }
    .report-icon {
      font-size: 2rem;
      margin-bottom: 12px;
    }
    .report-title {
      color: #2d3748;
      font-size: 1.3rem;
      font-weight: 600;
      margin-bottom: 8px;
    }
    .report-desc {
      color: #718096;
      font-size: 0.95rem;
      line-height: 1.5;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>🔍 Enhanced ORT Analysis Reports</h1>
    <p class="subtitle">Multi-Tool License Compliance Analysis <span class="badge">ENHANCED</span></p>

    <div class="report-grid">
'''

    # Add AI curation report
    if ai_report:
        html += f'''
      <a href="{ai_report}" class="report-card highlight">
        <div class="report-icon">🤖</div>
        <div class="report-title">Enhanced AI Curation Report <span class="badge">NEW</span></div>
        <div class="report-desc">Multi-tool AI analysis with ORT + ScanCode + SPDX validation</div>
      </a>
'''

    # Add ORT WebApp
    if webapp_file:
        html += f'''
      <a href="{webapp_file}" class="report-card">
        <div class="report-icon">🔍</div>
        <div class="report-title">ORT WebApp Report</div>
        <div class="report-desc">Interactive dependency tree and license visualization</div>
      </a>
'''

    # Add enhanced SPDX
    if spdx_enhanced:
        html += f'''
      <a href="{spdx_enhanced}" class="report-card">
        <div class="report-icon">✨</div>
        <div class="report-title">Enhanced SPDX Document</div>
        <div class="report-desc">SPDX enhanced with ScanCode license detections</div>
      </a>
'''

    # Add CycloneDX
    if cyclonedx:
        html += f'''
      <a href="{cyclonedx}" class="report-card">
        <div class="report-icon">📦</div>
        <div class="report-title">CycloneDX SBOM</div>
        <div class="report-desc">Software Bill of Materials in CycloneDX format</div>
      </a>
'''

    # Add original SPDX if no enhanced version
    if spdx_original and not spdx_enhanced:
        html += f'''
      <a href="{spdx_original}" class="report-card">
        <div class="report-icon">📋</div>
        <div class="report-title">SPDX Document</div>
        <div class="report-desc">Software Package Data Exchange standard format</div>
      </a>
'''

    # Add uncertain packages report
    if uncertain_report:
        html += f'''
      <a href="{uncertain_report}" class="report-card">
        <div class="report-icon">⚠️</div>
        <div class="report-title">Uncertain Packages Report</div>
        <div class="report-desc">Packages requiring manual license review</div>
      </a>
'''

    # Close HTML
    html += '''
    </div>
  </div>
</body>
</html>
'''

    # Write index.html
    index_path = public_path / 'index.html'
    with open(index_path, 'w') as f:
        f.write(html)

    print(f"✅ Landing page generated: {index_path}")

if __name__ == '__main__':
    public_dir = sys.argv[1] if len(sys.argv) > 1 else 'public'
    generate_landing_page(public_dir)
