# Enhanced License Curation Strategy: Multi-Tool Approach

## The Challenge

ORT alone may miss licenses due to:
- **Incomplete package metadata** - Packages without proper license declarations
- **New/emerging packages** - Recently published packages not yet in ORT's knowledge base
- **Non-standard license formats** - Custom or modified licenses
- **Embedded licenses** - Licenses in source files rather than package manifests
- **Multi-licensed components** - Complex license expressions

## Recommended Multi-Tool Strategy

### Tier 1: ORT (Primary Analysis)
**Strengths**: Fast, package-manager aware, good for standard packages
**Limitations**: Relies on declared licenses, may miss embedded/custom licenses

### Tier 2: ScanCode Toolkit (Deep Scanning)
**Strengths**: File-level license detection, finds embedded licenses, comprehensive
**Limitations**: Slower, generates large outputs

### Tier 3: SPDX Tools (Validation & Enrichment)
**Strengths**: License validation, standardization, SPDX document manipulation
**Limitations**: Requires well-formed input data

### Tier 4: AI Curation (Intelligence Layer)
**Strengths**: Interprets ambiguous results, suggests corrections, explains conflicts
**Limitations**: Requires review, may need human validation

## Implementation Approach

### Strategy 1: Sequential Enhancement Pipeline

```
[ORT Analysis] → [ScanCode Deep Scan] → [SPDX Validation] → [AI Curation] → [Manual Review]
```

**Process Flow**:
1. **ORT**: Quick first pass on all dependencies
2. **ScanCode**: Deep scan on packages where ORT finds:
   - No license declared
   - NOASSERTION or UNKNOWN
   - Ambiguous license expressions
3. **SPDX Tools**: Validate and merge results into standard format
4. **AI**: Analyze conflicts, suggest resolutions
5. **Human**: Review AI suggestions and approve curations

### Strategy 2: Parallel Analysis with Consensus

```
          ┌─── ORT ────┐
Package ──┼─ ScanCode ─┼─→ [Consensus Engine] → [AI Resolution] → [Approval]
          └── FOSSology ┘
```

Run multiple tools simultaneously and use majority voting or AI to resolve conflicts.

## Enhanced GitHub Actions Workflow

### Step 1: Add ScanCode Integration

```yaml
- name: Run ScanCode on Uncertain Packages
  run: |
    # Install ScanCode
    pip install scancode-toolkit
    
    # Extract packages with missing licenses from ORT results
    python extract_uncertain_packages.py \
      --ort-result ort-results/analyzer/analyzer-result.yml \
      --output uncertain-packages.txt
    
    # Run ScanCode on these packages
    mkdir -p scancode-results
    while read package_path; do
      scancode -l -c -i --json scancode-results/$(basename $package_path).json $package_path
    done < uncertain-packages.txt
```

### Step 2: Add SPDX Tools Integration

```yaml
- name: Generate and Validate SPDX Documents
  run: |
    pip install spdx-tools
    
    # Convert ORT results to SPDX
    # (ORT already generates SPDX, but we can enhance it)
    
    # Validate SPDX document
    pyspdxtools -i ort-results/reporter/bom.spdx.yml --validate
    
    # Merge ScanCode results into SPDX
    python merge_scancode_to_spdx.py \
      --spdx ort-results/reporter/bom.spdx.yml \
      --scancode scancode-results/ \
      --output enhanced-spdx.json
```

### Step 3: Enhanced AI Curation

```yaml
- name: Enhanced AI Curation with Multi-Tool Results
  env:
    AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
    AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
  run: |
    python enhanced_curation_script.py \
      --ort-results ort-results/analyzer/analyzer-result.yml \
      --scancode-results scancode-results/ \
      --spdx-doc enhanced-spdx.json \
      --output curation-report-enhanced.html
```

## Practical Python Scripts

### Script 1: Extract Uncertain Packages

```python
# extract_uncertain_packages.py
import yaml
import argparse
from pathlib import Path

def extract_uncertain_packages(ort_result_path, output_path):
    """Extract packages with missing or uncertain licenses from ORT results"""
    
    with open(ort_result_path) as f:
        ort_data = yaml.safe_load(f)
    
    uncertain = []
    
    for package in ort_data.get('analyzer', {}).get('result', {}).get('packages', []):
        declared_licenses = package.get('declared_licenses', [])
        
        # Check for uncertain license declarations
        if not declared_licenses or \
           any(lic in ['NOASSERTION', 'UNKNOWN', 'NONE', ''] for lic in declared_licenses):
            
            package_info = {
                'id': package.get('id'),
                'name': package.get('id', '').split(':')[1] if ':' in package.get('id', '') else '',
                'version': package.get('id', '').split(':')[2] if package.get('id', '').count(':') >= 2 else '',
                'vcs_url': package.get('vcs', {}).get('url', ''),
                'source_artifact': package.get('source_artifact', {}).get('url', '')
            }
            uncertain.append(package_info)
    
    # Write to output
    with open(output_path, 'w') as f:
        for pkg in uncertain:
            f.write(f"{pkg['id']}\n")
    
    print(f"Found {len(uncertain)} packages with uncertain licenses")
    return uncertain

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ort-result', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    extract_uncertain_packages(args.ort_result, args.output)
```

### Script 2: Merge Multi-Tool Results

```python
# merge_scancode_to_spdx.py
import json
import yaml
import argparse
from pathlib import Path

def merge_results(spdx_path, scancode_dir, output_path):
    """Merge ScanCode findings into SPDX document"""
    
    # Load SPDX document
    with open(spdx_path) as f:
        if spdx_path.endswith('.json'):
            spdx_doc = json.load(f)
        else:
            spdx_doc = yaml.safe_load(f)
    
    # Load ScanCode results
    scancode_results = {}
    for scancode_file in Path(scancode_dir).glob('*.json'):
        with open(scancode_file) as f:
            scancode_data = json.load(f)
            package_name = scancode_file.stem
            
            # Extract detected licenses
            licenses = set()
            for file_info in scancode_data.get('files', []):
                for license_info in file_info.get('licenses', []):
                    licenses.add(license_info.get('key', ''))
            
            scancode_results[package_name] = list(licenses)
    
    # Enhance SPDX document with ScanCode findings
    enhanced_packages = []
    
    for package in spdx_doc.get('packages', []):
        pkg_name = package.get('name', '')
        
        # If package had no concluded license, add ScanCode findings
        if package.get('licenseConcluded') in ['NOASSERTION', 'NONE', None]:
            if pkg_name in scancode_results and scancode_results[pkg_name]:
                # Add comment about ScanCode detection
                package['licenseComments'] = (
                    f"License detected by ScanCode: {', '.join(scancode_results[pkg_name])}"
                )
                # Optionally update concluded license
                if len(scancode_results[pkg_name]) == 1:
                    package['licenseConcluded'] = scancode_results[pkg_name][0]
                else:
                    package['licenseConcluded'] = f"({' OR '.join(scancode_results[pkg_name])})"
        
        enhanced_packages.append(package)
    
    spdx_doc['packages'] = enhanced_packages
    
    # Write enhanced SPDX
    with open(output_path, 'w') as f:
        json.dump(spdx_doc, f, indent=2)
    
    print(f"Enhanced SPDX document written to {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--spdx', required=True)
    parser.add_argument('--scancode', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    merge_results(args.spdx, args.scancode, args.output)
```

### Script 3: Enhanced AI Curation

```python
# enhanced_curation_script.py
import json
import yaml
import argparse
from openai import AzureOpenAI
import os

def enhanced_ai_curation(ort_path, scancode_dir, spdx_path, output_path):
    """Use AI to curate and resolve conflicts between tools"""
    
    client = AzureOpenAI(
        api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        api_version="2024-02-15-preview",
        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
    )
    
    # Load all results
    with open(ort_path) as f:
        ort_data = yaml.safe_load(f)
    
    with open(spdx_path) as f:
        spdx_data = json.load(f)
    
    conflicts = []
    
    # Find packages with conflicting license information
    for package in spdx_data.get('packages', []):
        pkg_name = package.get('name')
        declared = package.get('licenseDeclared', 'NOASSERTION')
        concluded = package.get('licenseConcluded', 'NOASSERTION')
        comments = package.get('licenseComments', '')
        
        # Check for conflicts
        if declared != concluded and declared != 'NOASSERTION' and concluded != 'NOASSERTION':
            conflicts.append({
                'package': pkg_name,
                'declared': declared,
                'concluded': concluded,
                'scancode_findings': comments
            })
    
    # Use AI to resolve conflicts
    curations = []
    
    for conflict in conflicts[:10]:  # Limit to avoid token limits
        prompt = f"""
Analyze this license conflict for package '{conflict['package']}':

- Declared License (from package metadata): {conflict['declared']}
- Concluded License (from source code scan): {conflict['concluded']}
- ScanCode Findings: {conflict['scancode_findings']}

Please provide:
1. Most likely correct license
2. Explanation of the discrepancy
3. Recommended action (accept, investigate, or contact maintainer)
4. Compliance risk level (low/medium/high)
"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a software license compliance expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        curations.append({
            'package': conflict['package'],
            'analysis': response.choices[0].message.content,
            'conflict': conflict
        })
    
    # Generate HTML report
    generate_enhanced_html_report(curations, output_path)
    
    return curations

def generate_enhanced_html_report(curations, output_path):
    """Generate enhanced HTML report with multi-tool analysis"""
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced License Curation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        .conflict {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
        .package-name {{ font-size: 1.2em; font-weight: bold; color: #2c3e50; }}
        .license-info {{ margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 4px; }}
        .ai-analysis {{ background: #e8f4f8; border-left: 4px solid #3498db; padding: 15px; margin: 10px 0; }}
        .risk-high {{ color: #dc3545; font-weight: bold; }}
        .risk-medium {{ color: #ffc107; font-weight: bold; }}
        .risk-low {{ color: #28a745; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Enhanced License Curation Report</h1>
        <p><strong>Multi-Tool Analysis:</strong> ORT + ScanCode + AI Curation</p>
        <p><strong>Total Conflicts Found:</strong> {len(curations)}</p>
        <hr>
"""
    
    for curation in curations:
        conflict = curation['conflict']
        html += f"""
        <div class="conflict">
            <div class="package-name">📦 {curation['package']}</div>
            
            <div class="license-info">
                <strong>Declared License (Package Metadata):</strong> {conflict['declared']}<br>
                <strong>Concluded License (Source Scan):</strong> {conflict['concluded']}<br>
                <strong>ScanCode Findings:</strong> {conflict['scancode_findings']}
            </div>
            
            <div class="ai-analysis">
                <strong>🤖 AI Analysis:</strong><br>
                <pre style="white-space: pre-wrap; font-family: Arial;">{curation['analysis']}</pre>
            </div>
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"Enhanced curation report generated: {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ort-results', required=True)
    parser.add_argument('--scancode-results', required=True)
    parser.add_argument('--spdx-doc', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    enhanced_ai_curation(args.ort_results, args.scancode_results, args.spdx_doc, args.output)
```

## Complete Enhanced Workflow

```yaml
- name: Enhanced Multi-Tool License Analysis
  run: |
    echo "🔍 Starting enhanced license curation..."
    
    # Stage 1: ORT Analysis (already done)
    echo "✅ ORT analysis complete"
    
    # Stage 2: Extract uncertain packages
    python extract_uncertain_packages.py \
      --ort-result ort-results/analyzer/analyzer-result.yml \
      --output uncertain-packages.txt
    
    # Stage 3: ScanCode deep scan
    pip install scancode-toolkit
    mkdir -p scancode-results
    
    # Download and scan uncertain packages
    python download_and_scan_packages.py \
      --package-list uncertain-packages.txt \
      --output scancode-results/
    
    # Stage 4: Merge results
    pip install spdx-tools
    python merge_scancode_to_spdx.py \
      --spdx ort-results/reporter/bom.spdx.yml \
      --scancode scancode-results/ \
      --output enhanced-spdx.json
    
    # Stage 5: AI-powered curation
    python enhanced_curation_script.py \
      --ort-results ort-results/analyzer/analyzer-result.yml \
      --scancode-results scancode-results/ \
      --spdx-doc enhanced-spdx.json \
      --output curation-report-enhanced.html
    
    echo "✅ Enhanced curation complete"
```

## Best Practices for New Package Compliance

### 1. Create a Curation Database

```yaml
# .ort/curations.yml
curations:
  - id: "NPM::new-package:1.0.0"
    curations:
      declared_license_mapping:
        "NOASSERTION": "MIT"
      comment: "Verified from source code inspection on 2025-01-15"
      
  - id: "PyPI::emerging-lib:2.3.1"
    curations:
      declared_license_mapping:
        "UNKNOWN": "Apache-2.0"
      comment: "Confirmed with maintainer via GitHub issue #123"
```

### 2. Automated License Detection Workflow

For truly new packages:
1. **Clone the source repository**
2. **Run ScanCode** on entire codebase
3. **Check for LICENSE files** in root and subdirectories
4. **Analyze header comments** in source files
5. **Review package.json/setup.py** metadata
6. **Cross-reference** with GitHub license badges
7. **AI summarization** of findings
8. **Human approval** before adding to curation database

### 3. Maintain Compliance Database

```bash
# Create a compliance tracking system
compliance-db/
  ├── curated-licenses.yml      # Approved curations
  ├── pending-review.yml        # Awaiting human review
  ├── blocked-packages.yml      # Packages with incompatible licenses
  └── audit-trail.log           # All curation decisions with timestamps
```

## Tool Comparison Matrix

| Feature | ORT | ScanCode | SPDX Tools | AI Curation |
|---------|-----|----------|------------|-------------|
| Speed | ⚡⚡⚡ Fast | 🐌 Slow | ⚡⚡ Fast | ⚡⚡ Fast |
| Accuracy | ✓✓ Good | ✓✓✓ Excellent | ✓✓ Good | ✓ Variable |
| File-level detection | ✗ | ✓✓✓ | ✗ | ✓ |
| Package manager integration | ✓✓✓ | ✓ | ✓✓ | ✗ |
| Custom licenses | ✓ | ✓✓✓ | ✓✓ | ✓✓✓ |
| Conflict resolution | ✗ | ✗ | ✗ | ✓✓✓ |

## Recommended Implementation Timeline

**Week 1**: Integrate ScanCode for uncertain packages
**Week 2**: Add SPDX validation and enhancement
**Week 3**: Enhance AI curation with multi-tool data
**Week 4**: Build curation database and approval workflow
**Ongoing**: Maintain and improve curation rules

This multi-tool approach significantly improves license detection accuracy and helps you handle new packages systematically!