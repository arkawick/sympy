# Enhanced ORT License Curation System

> Multi-tool license compliance analysis with AI-powered curation recommendations

[![License Analysis](https://img.shields.io/badge/License-Analysis-blue.svg)](https://github.com/oss-review-toolkit/ort)
[![ScanCode](https://img.shields.io/badge/ScanCode-Toolkit-green.svg)](https://github.com/nexB/scancode-toolkit)
[![SPDX](https://img.shields.io/badge/SPDX-ISO%2FIEC%205962-orange.svg)](https://spdx.dev/)
[![AI Powered](https://img.shields.io/badge/AI-Azure%20OpenAI-purple.svg)](https://azure.microsoft.com/en-us/products/ai-services/openai-service)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Usage](#usage)
- [Generated Reports](#generated-reports)
- [Scripts Reference](#scripts-reference)
- [Workflow Stages](#workflow-stages)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Cost Estimation](#cost-estimation)
- [FAQ](#faq)

---

## 🎯 Overview

This system provides **comprehensive open-source license compliance analysis** using a multi-tool approach to address limitations of single-tool solutions. It combines industry-standard tools with AI-powered research to maximize license detection coverage.

### Problem Solved

**Why do we need multiple tools?**

- **ORT alone** may miss licenses for new/emerging packages
- **Package metadata** is often incomplete or incorrect
- **Non-standard license formats** aren't recognized
- **Embedded licenses** in source files vs. package manifests

**Our Solution:** 5-tier multi-tool approach

```
┌─────────────────────────────────────────────────────────┐
│  Source Code / Dependencies                              │
└────────────────┬────────────────────────────────────────┘
                 │
    ┌────────────▼────────────┐
    │   Tier 1: ORT Analyzer  │  Fast, package-manager aware
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────────┐
    │   Tier 2: Uncertain Package │  Identifies gaps
    │   Extraction                │
    └────────────┬────────────────┘
                 │
    ┌────────────▼────────────┐
    │   Tier 3: ScanCode Deep │  File-level license detection
    │   Scanning (20 pkgs)    │
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │   Tier 4: SPDX Merge &  │  Combines & validates results
    │   Validation            │
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │   Tier 5: AI-Powered    │  Intelligent recommendations
    │   Curation (3 reports)  │  (Advisory only)
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │   Manual Verification   │  Human review & approval
    │   & Team Approval       │  (REQUIRED)
    └─────────────────────────┘
```

---

## ✨ Features

### 🔧 Multi-Tool Analysis
- **ORT (Open Source Review Toolkit)** - Dependency analysis & vulnerability scanning
- **ScanCode Toolkit** - Deep file-level license detection with native HTML/JSON/YAML reports
- **SPDX Tools** - Validation & enhancement (ISO/IEC 5962:2021 standard)
- **CycloneDX** - OWASP SBOM standard

### 🤖 AI-Powered Curation (Advisory)
- **Main ORT Curation Report** - Comprehensive compliance analysis with Go/No-Go verdict
- **Conflict Analysis Report** - Multi-tool conflict resolution (ORT vs ScanCode)
- **Missing Licenses Analysis** - AI suggestions for packages with blank/missing licenses
- **Verification Guides** - Step-by-step instructions for manual verification

### 📊 Comprehensive Reporting
- **10+ Report Formats** generated automatically
- **GitHub Pages Deployment** with beautiful landing page
- **Interactive WebApp** for dependency visualization
- **Static HTML Reports** for traditional compliance documentation
- **Machine-readable formats** (JSON, YAML, SPDX, CycloneDX)

### 🔄 Automated Workflow
- **GitHub Actions CI/CD** integration
- **Scheduled scans** (daily/on-demand)
- **PR comments** with compliance status
- **Artifact retention** (30 days)
- **Multi-branch support** (main, master, develop)

### 📝 Manual Curation Management
- **CLI tool** for managing license overrides
- **Version-controlled database** (`.ort/curations.yml`)
- **Import/export** functionality (CSV, JSON)
- **Validation** before committing
- **Audit trail** with comments and dates

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Repository                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  .github/workflows/enhanced-ort-workflow.yml              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Python Scripts (Root Directory)                          │  │
│  │  • extract_uncertain_packages.py                          │  │
│  │  • merge_scancode_to_spdx.py                              │  │
│  │  • enhanced_ai_curation.py                                │  │
│  │  • ai_missing_licenses_analyzer.py                        │  │
│  │  • ort_curation_script_html.py                            │  │
│  │  • manage_curations.py                                    │  │
│  │  • spdx-validation-fixer.py                               │  │
│  │  • generate_scancode_reports.py                           │  │
│  │  • generate_landing_page.py                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  .ort/curations.yml (Manual curation database)            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions Runner                        │
│                                                                  │
│  Stage 1: ORT Analyzer + Advisor                                │
│  Stage 2: Extract Uncertain Packages (20)                       │
│  Stage 3: ScanCode Deep Scan (HTML/JSON/YAML per package)       │
│  Stage 4: Merge & Validate SPDX                                 │
│  Stage 5: AI Curation (3 reports)                               │
│  Stage 6: Prepare & Deploy to GitHub Pages                      │
│  Stage 7: Upload Artifacts                                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       GitHub Pages                               │
│                                                                  │
│  https://<username>.github.io/<repo>/                           │
│  ├── index.html (Landing page with all reports)                 │
│  ├── curation-report-main.html (AI - Primary)                   │
│  ├── curation-report-conflicts.html (AI - Conflicts)            │
│  ├── curation-report-missing-licenses.html (AI - Missing)       │
│  ├── scancode-summary.html (Consolidated)                       │
│  ├── scan-report.html (ORT Static HTML)                         │
│  ├── scan-report-web-app.html (ORT WebApp)                      │
│  ├── bom.cyclonedx.json (CycloneDX SBOM)                        │
│  ├── bom-enhanced.spdx.json (Enhanced SPDX)                     │
│  └── scancode-reports/ (Individual package reports)             │
│      ├── package-1.0.0.html (Native ScanCode HTML)              │
│      ├── package-1.0.0.json (Raw scan data)                     │
│      └── package-1.0.0.yml (Raw scan data)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- GitHub repository with source code
- Azure OpenAI API access (for AI curation)
- GitHub Actions enabled

### 1. Add Scripts to Repository

```bash
# Clone or download all Python scripts to repository root
git add extract_uncertain_packages.py \
        merge_scancode_to_spdx.py \
        enhanced_ai_curation.py \
        ai_missing_licenses_analyzer.py \
        ort_curation_script_html.py \
        manage_curations.py \
        spdx-validation-fixer.py \
        generate_scancode_reports.py \
        generate_landing_page.py
```

### 2. Add Workflow

```bash
# Add the enhanced workflow
git add .github/workflows/enhanced-ort-workflow.yml
```

### 3. Configure GitHub Secrets

Go to: **Repository Settings → Secrets and variables → Actions**

Add these secrets:
- `AZURE_OPENAI_API_KEY` - Your Azure OpenAI API key (required)
- `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI endpoint (optional, has default)

### 4. Commit and Push

```bash
git commit -m "Add enhanced ORT license curation system"
git push
```

### 5. View Reports

After workflow completes, visit:
```
https://<username>.github.io/<repo>/
```

---

## 🔧 Detailed Setup

### Local Testing (Optional)

#### Install Dependencies

```bash
# Python dependencies
pip install python-inspector openai pyyaml spdx-tools scancode-toolkit

# ORT (Linux/macOS)
ORT_VERSION="70.0.1"
wget https://github.com/oss-review-toolkit/ort/releases/download/${ORT_VERSION}/ort-${ORT_VERSION}.tgz
tar -xzf ort-${ORT_VERSION}.tgz
export PATH="${PWD}/ort-${ORT_VERSION}/bin:$PATH"

# Verify installations
ort --version
scancode --version
```

#### Run Complete Pipeline Locally

```bash
# Stage 1: ORT Analysis
ort analyze -i . -o ort-results/analyzer
ort advise -i ort-results/analyzer/analyzer-result.yml -o ort-results/advisor --advisors OSV
ort report -i ort-results/analyzer/analyzer-result.yml -o ort-results/reporter -f WebApp,StaticHtml,CycloneDx,SpdxDocument

# Stage 2: Extract Uncertain Packages
python extract_uncertain_packages.py \
  --ort-result ort-results/analyzer/analyzer-result.yml \
  --output-dir uncertain-packages

# Stage 3: ScanCode Scanning (manual for local testing)
# Download packages and scan with ScanCode
# (See IMPLEMENTATION_GUIDE.md for details)

# Stage 4: Merge ScanCode Results
python merge_scancode_to_spdx.py \
  --spdx ort-results/reporter/bom.spdx.yml \
  --scancode scancode-results/ \
  --output enhanced-spdx/bom-enhanced.spdx.json

# Stage 5: AI Curation Reports
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="your-endpoint"

python ort_curation_script_html.py
python enhanced_ai_curation.py \
  --ort-results ort-results/analyzer/analyzer-result.yml \
  --spdx-doc enhanced-spdx/bom-enhanced.spdx.json \
  --uncertain-packages uncertain-packages/uncertain-packages.json \
  --output curation-report-conflicts.html
python ai_missing_licenses_analyzer.py \
  uncertain-packages/uncertain-packages.json \
  curation-report-missing-licenses.html
```

---

## 📖 Usage

### Managing License Curations

#### Add a Single Curation

```bash
python manage_curations.py add \
  --id "NPM::lodash:4.17.21" \
  --license "MIT" \
  --comment "Verified from GitHub LICENSE file on 2025-01-15" \
  --original-license "NOASSERTION" \
  --homepage "https://lodash.com"
```

#### Import Uncertain Packages (Generate Templates)

```bash
python manage_curations.py import-uncertain \
  --file uncertain-packages/uncertain-packages.json
```

This creates templates in `.ort/curations.yml` that you can edit.

#### List All Curations

```bash
python manage_curations.py list
```

#### Validate Curations

```bash
python manage_curations.py validate
```

#### Export for Review

```bash
python manage_curations.py export --output curations-review.csv
```

#### Remove a Curation

```bash
python manage_curations.py remove --id "NPM::lodash:4.17.21"
```

### Running ScanCode Manually

```bash
# Scan a specific package
scancode -clpieu \
  --html output.html \
  --json output.json \
  --yaml output.yml \
  --timeout 120 \
  --max-depth 3 \
  package-directory/

# Flags:
# -c = copyright detection
# -l = license detection
# -p = package info
# -i = file info
# -e = email detection
# -u = url detection
```

### Triggering Workflow Manually

1. Go to **Actions** tab in GitHub
2. Select "Enhanced ORT Analysis with Multi-Tool Curation"
3. Click "Run workflow"
4. Select branch (main/master/develop)
5. Click "Run workflow"

---

## 📊 Generated Reports

### AI-Powered Reports (HTML)

#### 1. Main ORT Curation Report
**File:** `curation-report-main.html`

**Content:**
- Executive summary with Go/No-Go verdict
- Complete license inventory
- Package-by-package analysis
- Risk assessment (high/medium/low)
- Actionable recommendations
- Compliance posture assessment

**Model:** Azure OpenAI `gpt-4.1-mini`

#### 2. License Conflict Analysis
**File:** `curation-report-conflicts.html`

**Content:**
- Conflict-by-conflict comparison (ORT vs ScanCode)
- AI recommendations for each conflict
- Risk levels per package
- Specific resolution steps
- Links to verification sources

**Model:** Azure OpenAI `gpt-4`

#### 3. Missing Licenses Analysis ⭐ NEW
**File:** `curation-report-missing-licenses.html`

**Content:**
- Packages with blank/NOASSERTION licenses
- AI-suggested licenses (SPDX identifiers)
- Confidence levels (High/Medium/Low)
- Verification steps for each package
- Alternative licenses to check
- Risk assessments
- Quick links (registry, homepage, repository)
- Ready-to-use curation commands

**Model:** Azure OpenAI `gpt-4o-mini`

**Limit:** Analyzes up to 15 packages per run

### Standard Reports

#### 4. ScanCode Analysis Report
**File:** `scancode-summary.html`

**Content:**
- Consolidated multi-package summary
- License detections with confidence scores
- File coverage statistics
- Copyright statements

#### 5. ORT WebApp Report
**File:** `scan-report-web-app.html`

**Content:**
- Interactive dependency tree
- License visualization
- Clickable navigation

#### 6. ORT Static HTML Report ⭐ NEW
**File:** `scan-report.html`

**Content:**
- Traditional ORT compliance report
- Complete license details
- Violation summaries

#### 7. Individual ScanCode Reports ⭐ NEW
**Directory:** `scancode-reports/`

**Files per package:**
- `package-1.0.0.html` - Native ScanCode HTML report
- `package-1.0.0.json` - Raw scan data
- `package-1.0.0.yml` - Raw scan data

**Content:**
- File-by-file license detections
- Copyright statements per file
- Package information
- Email addresses and URLs found
- Detailed scan metadata

### Machine-Readable Reports

#### 8. Enhanced SPDX Document
**File:** `bom-enhanced.spdx.json`

**Format:** SPDX 2.3 JSON (ISO/IEC 5962:2021)

**Content:**
- ORT results + ScanCode findings merged
- High-confidence license detections (≥80%)
- License comments with detection sources

#### 9. CycloneDX SBOM
**File:** `bom.cyclonedx.json`

**Format:** CycloneDX 1.4 JSON (OWASP standard)

**Content:**
- Complete software bill of materials
- Component dependencies
- License information
- Vulnerabilities (if ORT Advisor ran)

#### 10. ScanCode YAML Summary
**File:** `scancode-summary.yml`

**Content:**
- Machine-readable scan summary
- Per-package license detections
- Copyright statements
- File counts and coverage

---

## 🛠️ Scripts Reference

### 1. `extract_uncertain_packages.py`
**Purpose:** Identifies packages with missing/uncertain licenses from ORT results

**Usage:**
```bash
python extract_uncertain_packages.py \
  --ort-result ort-results/analyzer/analyzer-result.yml \
  --output-dir uncertain-packages
```

**Outputs:**
- `uncertain-package-ids.txt` - Simple list
- `uncertain-packages.json` - Full details
- `uncertain-packages.csv` - Spreadsheet format
- `report.md` - Human-readable summary
- `extraction-stats.txt` - Statistics
- `download-packages.sh` - Download script

**Detects:**
- NOASSERTION, UNKNOWN, NONE, empty licenses
- Packages with only uncertain declarations

---

### 2. `merge_scancode_to_spdx.py`
**Purpose:** Merges ScanCode license detections into SPDX documents

**Usage:**
```bash
python merge_scancode_to_spdx.py \
  --spdx ort-results/reporter/bom.spdx.yml \
  --scancode scancode-results/ \
  --output enhanced-spdx/bom-enhanced.spdx.json
```

**Features:**
- Fuzzy package name matching
- High-confidence filtering (≥80% score)
- Primary vs secondary license distinction
- Generates merge statistics report

---

### 3. `enhanced_ai_curation.py`
**Purpose:** AI-powered conflict analysis between ORT and ScanCode

**Usage:**
```bash
python enhanced_ai_curation.py \
  --ort-results ort-results/analyzer/analyzer-result.yml \
  --spdx-doc enhanced-spdx/bom-enhanced-fixed.spdx.json \
  --uncertain-packages uncertain-packages/uncertain-packages.json \
  --output curation-report-conflicts.html
```

**Model:** Azure OpenAI `gpt-4`
**Limit:** First 20 conflicts

---

### 4. `ai_missing_licenses_analyzer.py` ⭐ NEW
**Purpose:** AI research and suggestions for packages with blank/missing licenses

**Usage:**
```bash
export AZURE_OPENAI_API_KEY="your-key"
python ai_missing_licenses_analyzer.py \
  uncertain-packages/uncertain-packages.json \
  curation-report-missing-licenses.html
```

**Model:** Azure OpenAI `gpt-4o-mini`
**Limit:** First 15 packages

**Output includes:**
- Suggested license (SPDX identifier)
- Confidence level (High/Medium/Low)
- Reasoning for suggestion
- Verification steps
- Alternative licenses
- Risk assessment
- Quick links to verify
- Copy-paste curation command

---

### 5. `ort_curation_script_html.py`
**Purpose:** Primary AI-powered comprehensive ORT analysis

**Usage:**
```bash
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="your-endpoint"
python ort_curation_script_html.py
```

**Model:** Azure OpenAI `gpt-4.1-mini`
**Output:** `curation-report-YYYYMMDD-HHMMSS.html`

---

### 6. `manage_curations.py`
**Purpose:** CLI tool for managing `.ort/curations.yml`

**Commands:**
```bash
# Add curation
python manage_curations.py add \
  --id "NPM::package:1.0.0" \
  --license "MIT" \
  --comment "Verified from source" \
  --original-license "NOASSERTION"

# List all
python manage_curations.py list

# Validate
python manage_curations.py validate

# Import templates
python manage_curations.py import-uncertain \
  --file uncertain-packages/uncertain-packages.json

# Export to CSV
python manage_curations.py export --output curations.csv

# Remove
python manage_curations.py remove --id "NPM::package:1.0.0"
```

---

### 7. `spdx-validation-fixer.py`
**Purpose:** Fixes common SPDX validation issues

**Usage:**
```bash
python spdx-validation-fixer.py -i broken.spdx.json -o fixed.spdx.json
python spdx-validation-fixer.py -i broken.spdx.json --validate-only
python spdx-validation-fixer.py -i broken.spdx.json -o fixed.spdx.json --create-stubs
```

**Fixes:**
- Broken SPDX ID references
- Invalid package names
- Missing package definitions

---

### 8. `generate_scancode_reports.py`
**Purpose:** Generates consolidated ScanCode HTML and YAML summaries

**Usage:**
```bash
python generate_scancode_reports.py scancode-results/
```

**Outputs:**
- `scancode-summary.html` - Beautiful web report
- `scancode-summary.yml` - Machine-readable summary

---

### 9. `generate_landing_page.py`
**Purpose:** Generates GitHub Pages landing page with all report links

**Usage:**
```bash
python generate_landing_page.py public/
```

**Auto-detects:**
- All available reports
- Individual ScanCode package reports
- Generates `public/index.html`

---

## ⚙️ Workflow Stages

### Stage 1: ORT Analysis
```yaml
- ORT Analyzer: Dependency analysis
- ORT Advisor: Vulnerability scanning (OSV database)
- ORT Reporter: Generate WebApp, StaticHtml, CycloneDx, SpdxDocument
```

### Stage 2: Extract Uncertain Packages
```yaml
- Identifies packages with NOASSERTION/UNKNOWN/blank licenses
- Generates 6 different output formats
- Creates download script for package sources
```

### Stage 3: ScanCode Deep Scan (20 packages)
```yaml
- Downloads package source code
- Runs ScanCode with -clpieu flags
- Generates HTML, JSON, YAML for each package
- Timeout: 120s per file, max depth: 3
```

### Stage 4: Merge & Validate SPDX
```yaml
- Generate consolidated ScanCode reports
- Merge ScanCode findings into SPDX
- Validate enhanced SPDX document
- Fix validation issues
```

### Stage 5: AI-Powered Curation (3 reports)
```yaml
Stage 5a: Main ORT Curation Report
  - Model: gpt-4.1-mini
  - Comprehensive compliance analysis

Stage 5b: Conflict Analysis
  - Model: gpt-4
  - ORT vs ScanCode conflict resolution
  - Limit: 20 conflicts

Stage 5c: Missing Licenses Analysis ⭐ NEW
  - Model: gpt-4o-mini
  - AI suggestions for blank/missing licenses
  - Limit: 15 packages
```

### Stage 6: Prepare & Deploy GitHub Pages
```yaml
- Copy all reports to public/ directory
- Copy individual ScanCode reports to scancode-reports/
- Generate landing page with all links
- Deploy to GitHub Pages (main/master only)
```

### Stage 7: Upload Artifacts
```yaml
- ORT results (30 days retention)
- ScanCode results (30 days retention)
- Enhanced reports (30 days retention)
```

---

## ✅ Best Practices

### 1. Curation Quality

**✅ DO:**
- Always include detailed comments explaining why curation was needed
- Add verification source (GitHub link, LICENSE file URL, maintainer confirmation)
- Include homepage and source URLs
- Date your comments
- Use proper SPDX license identifiers (see https://spdx.org/licenses/)

**❌ DON'T:**
- Leave "REVIEW-REQUIRED" in production
- Guess licenses without verification
- Use custom identifiers without "LicenseRef-" prefix
- Skip comments

**Example Good Curation:**
```yaml
- id: "NPM::axios:1.6.0"
  curations:
    comment: |
      License: MIT
      Verified by: John Doe (john@company.com)
      Date: 2025-01-15
      Source: https://github.com/axios/axios/blob/v1.6.0/LICENSE
      Method: Manual review of LICENSE file in source repository
      AI Suggestion: MIT (High confidence)
      Approved by: Compliance Team (ticket: COMP-123)
    concluded_license: "MIT"
    declared_license_mapping:
      "NOASSERTION": "MIT"
```

---

### 2. AI Usage Guidelines

**⚠️ CRITICAL: AI is Advisory Only**

**AI SHOULD BE USED FOR:**
- Initial research to speed up manual work
- Pattern recognition for common packages
- Generating verification step lists
- Aggregating links to registries/repos
- Suggesting where to look for license information

**AI SHOULD NOT BE USED FOR:**
- Final license decisions without human verification
- Legal advice
- Automated curation without review
- High-risk or legally sensitive packages

**Required Process:**
```
1. AI generates suggestion
2. Human reviews AI reasoning
3. Human verifies from actual source (LICENSE file, package.json, etc.)
4. Human checks package registry for confirmation
5. Compliance team approves (for production)
6. Add curation with evidence trail
```

---

### 3. ScanCode Usage

**✅ DO:**
- Use timeouts to avoid hanging (--timeout 120)
- Limit directory depth for large projects (--max-depth 3)
- Focus on packages with NOASSERTION first
- Review high-confidence detections (≥95%) manually before trusting

**❌ DON'T:**
- Scan entire node_modules or site-packages directories
- Trust low-confidence detections (<80%) without verification
- Skip validation after merging results

---

### 4. Team Workflow

**Recommended Process:**

1. **Developer:** Adds new dependency to project
2. **CI/CD:** Runs enhanced ORT workflow automatically
3. **Report:** Shows uncertain licenses in PR comment
4. **Developer:** Reviews AI recommendations
5. **Developer:** Manually verifies licenses from source
6. **Developer:** Adds curation with evidence
7. **Tech Lead:** Reviews curation in code review
8. **Compliance Officer:** Approves curation (for production)
9. **CI/CD:** Re-runs with curation applied
10. **Merge:** Only if all licenses are clear and approved

---

### 5. Maintenance Schedule

**Weekly:**
```bash
# Review new uncertain packages
python extract_uncertain_packages.py \
  --ort-result ort-results/analyzer/analyzer-result.yml \
  --output-dir uncertain-packages

# Generate curation templates
python manage_curations.py import-uncertain \
  --file uncertain-packages/uncertain-packages.json

# Update and validate curations
python manage_curations.py validate
```

**Monthly:**
```bash
# Export for compliance team review
python manage_curations.py export \
  --output curations-$(date +%Y-%m).csv

# Share with legal/compliance for review
```

**Before Release:**
```bash
# Full validation
python manage_curations.py validate

# Ensure no unresolved licenses
grep -r "REVIEW-REQUIRED" .ort/curations.yml && \
  echo "❌ Unresolved curations!" || \
  echo "✅ All curations resolved"

# Generate final SBOM
ort analyze -i . -o release-ort/analyzer
ort report -i release-ort/analyzer/analyzer-result.yml \
  -o release-ort/reporter -f SpdxDocument,CycloneDx

# Archive for compliance records
tar -czf license-compliance-$(date +%Y-%m-%d).tar.gz \
  release-ort/ .ort/curations.yml
```

---

## 🔧 Troubleshooting

### No AI Curation Reports Generated

**Symptoms:**
```
⚠️  AZURE_OPENAI_API_KEY not set, skipping AI report...
```

**Solution:**
1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Add `AZURE_OPENAI_API_KEY` secret
3. Optionally add `AZURE_OPENAI_ENDPOINT` (or use default)
4. Re-run workflow

---

### ORT Analyzer Failed

**Symptoms:**
```
❌ ORT analyzer results not found!
```

**Solution:**
1. Check earlier workflow steps for ORT errors
2. Verify project has valid package manifest (package.json, requirements.txt, pom.xml, etc.)
3. Check ORT logs in workflow output
4. Try running ORT locally: `ort analyze -i . -o ort-results/analyzer`

---

### ScanCode Not Finding Licenses

**Symptoms:**
- ScanCode completes but no licenses in reports
- Merge report shows 0 packages enhanced

**Solutions:**

**Check if packages were downloaded:**
```bash
ls -la downloaded-packages/
```

**Check if ScanCode results exist:**
```bash
ls -la scancode-results/
cat scancode-results/package-name.json | jq '.files[].licenses'
```

**Common causes:**
- Package source URL not available (no `source_artifact_url`)
- ScanCode timeout (increase with `--timeout 300`)
- Package is binary-only (no source files to scan)
- Network issues downloading packages

---

### SPDX Validation Errors

**Symptoms:**
```
Error: Invalid SPDX document
```

**Solution:**
```bash
# Run the SPDX fixer
python spdx-validation-fixer.py \
  -i enhanced-spdx/bom-enhanced.spdx.json \
  -o enhanced-spdx/bom-enhanced-fixed.spdx.json

# Validate with official tools
pyspdxtools -i enhanced-spdx/bom-enhanced-fixed.spdx.json --validate
```

---

### Curations Not Applied

**Symptoms:**
- Re-running ORT still shows NOASSERTION for curated packages

**Solutions:**

**Check curation file exists:**
```bash
ls -la .ort/curations.yml
```

**Validate curation format:**
```bash
python manage_curations.py validate
```

**Verify package ID format matches exactly:**
```yaml
# Correct format: "TYPE:NAMESPACE:NAME:VERSION"
# Examples:
✅ "NPM::lodash:4.17.21"
✅ "PyPI::requests:2.28.0"
✅ "Maven:org.springframework:spring-core:5.3.0"

❌ "NPM:lodash:4.17.21"  (missing double colon)
❌ "npm::lodash:4.17.21"  (lowercase type)
```

---

### AI Analysis Fails with Rate Limit

**Symptoms:**
```
Error: Rate limit exceeded
```

**Solutions:**

**Reduce batch size in scripts:**

In `enhanced_ai_curation.py` line 286:
```python
# Change from 20 to 10
conflicts_to_analyze = self.conflicts[:10]
```

In `ai_missing_licenses_analyzer.py` line 340:
```python
# Change from 15 to 10
if len(missing_license_packages) > 10:
    missing_license_packages = missing_license_packages[:10]
```

**Or wait and re-run** - Azure OpenAI rate limits reset after time period

---

### GitHub Pages Not Deploying

**Symptoms:**
- Workflow succeeds but no pages deployment
- "Setup Pages" step skipped

**Solutions:**

**Enable GitHub Pages:**
1. Go to repository → Settings → Pages
2. Source: GitHub Actions
3. Save

**Check branch condition:**
```yaml
# Verify you're pushing to main or master
git branch --show-current

# Workflow only deploys from main/master
if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'
```

---

## 💰 Cost Estimation

### Azure OpenAI Costs (per workflow run)

**Main ORT Curation Report:**
- Model: `gpt-4.1-mini`
- Tokens: ~3000-4000 output
- Cost: **~$0.05 USD**

**Conflict Analysis Report:**
- Model: `gpt-4`
- Tokens: ~1000 per conflict × 20 conflicts max
- Cost: **~$0.10-$0.20 USD**

**Missing Licenses Analysis:**
- Model: `gpt-4o-mini`
- Tokens: ~1000 per package × 15 packages max
- Cost: **~$0.05-$0.08 USD**

**Total per run:**
- **With all reports: $0.20-$0.33 USD**
- **Without conflicts/missing: $0.05 USD**

**Monthly estimate (daily runs):**
- **$6-$10 USD per month** per repository

**Cost optimization:**
- Reduce conflict analysis limit (20 → 10 packages)
- Reduce missing licenses limit (15 → 10 packages)
- Run weekly instead of daily
- Only run on main branch pushes

---

## ❓ FAQ

### Q: Is this approach industry standard?

**A: Yes, with important caveats:**

✅ **Industry Standard Components:**
- Multi-tool approach (better than single tool)
- ORT (used by Siemens, SAP, Bosch, etc.)
- ScanCode Toolkit (industry standard)
- SPDX format (ISO/IEC 5962:2021)
- CycloneDX SBOM (OWASP standard)
- Manual curation database (best practice)

⚠️ **AI Component Must Be Used Correctly:**
- AI suggestions are **advisory only**
- **Manual verification is REQUIRED**
- AI cannot replace legal review
- Never automate AI suggestions without human approval

**Recommended for:**
- Internal projects
- Development/testing environments
- License research and discovery

**Requires compliance review for:**
- Production deployments
- Customer-facing products
- Open-source releases
- Regulated industries

---

### Q: Can I trust AI suggestions?

**A: No - Always verify manually.**

AI suggestions are research aids to:
- Speed up finding license information
- Suggest where to look (GitHub, package registry, etc.)
- Provide verification steps
- Identify common patterns

AI can make mistakes:
- Package name similarity doesn't mean same license
- Patterns don't guarantee correctness
- AI doesn't have access to actual files
- Legal nuances require human judgment

**Always:**
1. Read actual LICENSE file in source repository
2. Check package registry metadata
3. Verify with package maintainer if unclear
4. Get compliance team approval for production

---

### Q: What if ScanCode can't download a package?

**A: Multiple options:**

1. **Manual download and scan:**
```bash
# Download from package registry
wget <package-source-url> -O package.tar.gz
tar -xzf package.tar.gz

# Scan manually
scancode -clpieu \
  --html package.html \
  --json package.json \
  package-directory/
```

2. **Check package homepage:**
- Visit package registry (NPM, PyPI, Maven Central)
- Look for license field in metadata
- Check repository link

3. **Add manual curation:**
```bash
python manage_curations.py add \
  --id "TYPE::package:version" \
  --license "LICENSE-ID" \
  --comment "Verified from [source]"
```

---

### Q: How do I handle dual/multi-licensed packages?

**A: Use SPDX expressions:**

```bash
# Dual license (user can choose)
python manage_curations.py add \
  --license "MIT OR Apache-2.0"

# Multi-license (all apply)
python manage_curations.py add \
  --license "MIT AND BSD-3-Clause"

# Complex expression
python manage_curations.py add \
  --license "(MIT OR Apache-2.0) AND BSD-3-Clause"
```

**SPDX License Expression Syntax:**
- `OR` - User can choose either license
- `AND` - Both licenses apply
- `WITH` - License with exception (e.g., `GPL-2.0-only WITH Classpath-exception-2.0`)
- `()` - Grouping

---

### Q: Can I use this for multiple repositories?

**A: Yes!**

See the multi-repository orchestration workflows:
- `trigger-ort-analysis.yml` - Trigger analysis across multiple repos
- `generate-dashboard.yml` - Centralized compliance dashboard

**Setup:**
1. Add this workflow to each repository
2. Use orchestrator repository to trigger all
3. Aggregate results in central dashboard
4. Share curations database across repos

---

### Q: What about packages not in public registries (internal packages)?

**A: Supported with manual curation:**

```bash
# For internal/private packages
python manage_curations.py add \
  --id "NPM:@yourorg:internal-package:1.0.0" \
  --license "Proprietary" \
  --comment "Internal company package, proprietary license" \
  --homepage "https://internal.company.com/packages/internal-package"

# Or use LicenseRef for custom licenses
python manage_curations.py add \
  --license "LicenseRef-CompanyInternal"
```

---

### Q: How long does the workflow take?

**Typical timings:**

- **ORT Analyzer:** 2-5 minutes (depends on project size)
- **ORT Advisor:** 1-2 minutes
- **ScanCode (20 packages):** 10-20 minutes
- **AI Curation (3 reports):** 2-3 minutes
- **Total:** **15-30 minutes**

**Optimization:**
- Reduce ScanCode limit (20 → 10 packages) = saves 5-10 min
- Run only on main branch pushes (not PRs)
- Cache ORT installation (saves 1-2 min)

---

### Q: Can I add custom license detection rules?

**A: Yes, multiple ways:**

**1. Custom ScanCode rules:**
- Add custom license text patterns to ScanCode
- See: https://scancode-toolkit.readthedocs.io/

**2. Add to curation database:**
```bash
python manage_curations.py add \
  --license "LicenseRef-CustomLicense"
```

**3. Policy enforcement:**
- Create `policy_checker.py` to enforce company policies
- Add to workflow to block forbidden licenses

---

## 📚 Additional Documentation

- **`IMPLEMENTATION_GUIDE.md`** - Detailed step-by-step implementation guide
- **`CURATION_REPORTS.md`** - Deep dive into dual AI report system
- **`CLAUDE.md`** - AI assistant instructions for future modifications

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests if applicable
4. Update documentation
5. Submit pull request

---

## 📄 License

This license curation system itself is provided as-is. Individual components:
- **ORT**: Apache-2.0
- **ScanCode Toolkit**: Apache-2.0
- **SPDX Tools**: Apache-2.0

---

## 🆘 Support

**Issues:**
- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)

**Resources:**
- ORT Documentation: https://github.com/oss-review-toolkit/ort
- ScanCode Docs: https://scancode-toolkit.readthedocs.io/
- SPDX Specification: https://spdx.dev/
- Azure OpenAI: https://learn.microsoft.com/azure/ai-services/openai/

---

## 🎯 Success Metrics

Track these to measure effectiveness:

```bash
# License coverage improvement
python extract_uncertain_packages.py \
  --ort-result ort-results/analyzer/analyzer-result.yml \
  --output-dir uncertain-packages
cat uncertain-packages/extraction-stats.txt
```

**Target Goals:**
- ✅ License coverage: **>95%** packages with clear licenses
- ✅ High-risk conflicts: **0**
- ✅ Manual review needed: **<5 packages**
- ✅ Curation accuracy: **100%** (all verified)

---

## 🚀 Roadmap

**Planned Features:**
- [ ] Policy enforcement (block forbidden licenses)
- [ ] License compatibility checker
- [ ] Automated curation approval workflow
- [ ] Integration with JIRA/ServiceNow for compliance tickets
- [ ] Custom license template library
- [ ] Historical compliance tracking
- [ ] Compliance dashboard with trends

---

**Made with ❤️ for open-source compliance**

*Generated by: Enhanced ORT License Curation System*
*Last Updated: 2025-01-15*
