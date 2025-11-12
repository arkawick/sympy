# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This repository implements an **Enhanced ORT (Open Source Review Toolkit) License Curation System** with multi-tool analysis. The system performs comprehensive open-source license compliance analysis using ORT + ScanCode Toolkit + AI-powered recommendations. It analyzes project dependencies, identifies licenses and vulnerabilities, performs deep source-code scanning for missing licenses, and generates standardized reports (SPDX, CycloneDX) deployed to GitHub Pages.

## Core Architecture

### Three-Tier Workflow System

1. **Enhanced Individual Repository Analysis** (`enhanced-ort-workflow.yml`)
   - **Stage 1**: ORT Analyzer + Advisor (dependency analysis + vulnerabilities)
   - **Stage 2**: Extract packages with uncertain/missing licenses
   - **Stage 3**: ScanCode deep scanning on uncertain packages
   - **Stage 4**: Merge ScanCode findings into SPDX documents
   - **Stage 5**: Dual AI-powered curation reports
   - **Stage 6-7**: Deploy to GitHub Pages with multiple report formats

2. **Multi-Repository Orchestrator** (`trigger-ort-analysis.yml`)
   - Triggers ORT analysis across multiple repositories simultaneously
   - Uses GitHub Actions workflow dispatch with PAT token
   - Scheduled to run daily at 2 AM UTC
   - Supports selective repository analysis via manual dispatch

3. **Centralized Dashboard** (`generate-dashboard.yml`)
   - Aggregates ORT results from multiple repositories
   - Generates unified HTML dashboard showing compliance status
   - Auto-refreshes every 6 hours
   - Deploys to GitHub Pages for stakeholder access

### Enhanced Multi-Tool Analysis Pipeline

The enhanced workflow uses a 6-tier approach to maximize license detection:

```
Source Code → ORT Analyzer → ORT Advisor → ORT Reporter
                    ↓              ↓              ↓
              Dependencies   Vulnerabilities   SPDX/CycloneDX
                                                    ↓
                              Extract Uncertain Packages
                                       ↓
                          PyPI API License Fetch (NEW - Stage 2.5)
                                       ↓
                              Reduces workload for ScanCode
                                       ↓
                      ScanCode Deep Scan (optimized - only remaining packages)
                                       ↓
                              Merge Results → Enhanced SPDX
                                       ↓
                    Triple AI Curation (Main + Conflicts + Missing)
                                       ↓
                              GitHub Pages Deployment
```

**Pipeline Stages:**
1. **ORT Analyzer**: Identifies all dependencies and declared licenses → `analyzer-result.yml`
2. **ORT Advisor**: Cross-references against OSV vulnerability database → `advise-result.yml`
3. **Uncertain Package Extraction**: Finds packages with NOASSERTION/UNKNOWN licenses
4. **PyPI API Fetch** (NEW): Fetches licenses directly from PyPI API for Python packages - fast, no scanning needed
5. **ScanCode Scanning**: Deep file-level license detection on remaining uncertain packages (optimized)
   - Generates native HTML, JSON, YAML reports per package
   - Uses `-clpieu` flags (copyright, license, package, info, email, url)
   - Skips packages with licenses already found via PyPI API
6. **SPDX Enhancement**: Merges ScanCode findings into SPDX document
7. **AI Curation - Main**: Comprehensive compliance analysis with recommendations
8. **AI Curation - Conflicts**: Focused analysis of license conflicts (ORT vs ScanCode)
9. **AI Curation - Missing**: AI suggestions for packages with blank/missing licenses (limit: 15)
10. **GitHub Pages**: Deploy all reports with landing page

## Key Scripts and Components

### License Analysis Scripts

#### 1. `extract_uncertain_packages.py`
Extracts packages with missing or uncertain licenses from ORT results.

**Usage:**
```bash
python extract_uncertain_packages.py \
  --ort-result ort-results/analyzer/analyzer-result.yml \
  --output-dir uncertain-packages
```

**Outputs:**
- `uncertain-package-ids.txt` - Simple list of package IDs
- `uncertain-packages.json` - Full package details with metadata
- `uncertain-packages.csv` - Spreadsheet-friendly format
- `report.md` - Human-readable markdown report
- `extraction-stats.txt` - Coverage statistics
- `download-packages.sh` - Script to download source packages

**Detects:**
- Packages with `NOASSERTION`, `UNKNOWN`, `NONE`, or empty licenses
- Packages missing both declared and concluded licenses
- Categorizes by package type (NPM, PyPI, Maven, etc.)

#### 2. `fetch_pypi_licenses.py` ⭐ NEW
Fetches missing license information directly from PyPI API for Python packages.

**Usage:**
```bash
python fetch_pypi_licenses.py \
  ort-results/analyzer/analyzer-result.yml \
  --fetch \
  --json \
  --csv \
  --curations \
  --output-dir pypi-licenses
```

**Outputs:**
- `pypi-licenses-full.json` - Complete report with all packages
- `pypi-licenses-found.json` - Only packages with licenses found in PyPI
- `pypi-licenses.csv` - Spreadsheet-friendly format
- `curation-suggestions.yml` - ORT curation format (requires manual review!)
- `pypi-fetch-stats.txt` - Fetch statistics and workload reduction metrics

**Features:**
- Fast license retrieval from PyPI API (no scanning needed)
- Multiple metadata sources (license field, license_expression, classifiers)
- Generates ready-to-use curation suggestions (manual verification required)
- Reduces ScanCode workload significantly
- Tracks fetch statistics and success rates

**⚠️ IMPORTANT:** Always verify PyPI results manually before applying curations - API data may be incomplete or incorrect.

#### 3. `merge_scancode_to_spdx.py`
Merges ScanCode Toolkit license detections into SPDX documents.

**Usage:**
```bash
python merge_scancode_to_spdx.py \
  --spdx ort-results/reporter/bom.spdx.yml \
  --scancode scancode-results/ \
  --output enhanced-spdx/bom-enhanced.spdx.json
```

**Features:**
- Fuzzy package name matching (handles hyphens, underscores, dots)
- Only includes high-confidence detections (≥80% score)
- Distinguishes primary vs. secondary licenses
- Generates merge report with statistics
- Updates `licenseConcluded` and adds `licenseComments`

#### 4. `enhanced_ai_curation.py`
AI-powered conflict analysis using multi-tool results (ORT + ScanCode + SPDX).

**Usage:**
```bash
python enhanced_ai_curation.py \
  --ort-results ort-results/analyzer/analyzer-result.yml \
  --spdx-doc enhanced-spdx/bom-enhanced-fixed.spdx.json \
  --uncertain-packages uncertain-packages/uncertain-packages.json \
  --output curation-report-conflicts.html
```

**Features:**
- Compares ORT declared vs. ScanCode concluded licenses
- AI analysis of each conflict using Azure OpenAI GPT-4
- Risk assessment (low/medium/high) for each package
- Recommended actions (accept, investigate, contact maintainer)
- Generates beautiful HTML report with conflict details

#### 5. `ort_curation_script_html.py`
Primary AI-powered ORT analysis report generator.

**Usage:**
```bash
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="your-endpoint"
python ort_curation_script_html.py
```

**Generates:**
- Executive summary with overall project status
- Complete license inventory and distribution
- Package-by-package compliance analysis
- Risk assessment (high/medium/low priority)
- Actionable recommendations
- Go/No-Go compliance verdict
- Beautiful gradient UI with LTTS branding

**Model:** `gpt-4.1-mini` with 4000 token limit

#### 6. `spdx-validation-fixer.py`
Fixes common issues in ORT-generated SPDX documents.

**Usage:**
```bash
python spdx-validation-fixer.py -i bom.spdx.yml -o bom-fixed.spdx.yml
python spdx-validation-fixer.py -i bom.spdx.yml -o fixed.spdx.yml --create-stubs
python spdx-validation-fixer.py -i bom.spdx.yml --validate-only
```

**Fixes:**
- Broken SPDX ID references
- Invalid package names (dots → hyphens)
- Missing package definitions
- Creates stub packages or removes broken relationships

#### 7. `manage_curations.py`
CLI tool for managing ORT package license curations.

**Usage:**
```bash
# Add a single curation
python manage_curations.py add \
  --id "NPM::package:1.0.0" \
  --license "MIT" \
  --comment "Verified from GitHub LICENSE file" \
  --original-license "NOASSERTION"

# List all curations
python manage_curations.py list

# Validate curations
python manage_curations.py validate

# Import from uncertain packages
python manage_curations.py import-uncertain \
  --file uncertain-packages/uncertain-packages.json

# Export to CSV for review
python manage_curations.py export --output curations.csv

# Remove a curation
python manage_curations.py remove --id "NPM::package:1.0.0"
```

**Database Location:** `.ort/curations.yml`

#### 8. `ai_missing_licenses_analyzer.py`
AI-powered research and suggestions for packages with blank/missing licenses.

**Usage:**
```bash
export AZURE_OPENAI_API_KEY="your-key"
python ai_missing_licenses_analyzer.py \
  uncertain-packages/uncertain-packages.json \
  curation-report-missing-licenses.html
```

**Features:**
- Identifies packages with completely missing/blank licenses (NOASSERTION, empty)
- Uses Azure OpenAI GPT-4o-mini to research each package
- Generates suggestions based on package type, name patterns, common licenses
- Analyzes repository and homepage URLs

**Output includes:**
- Suggested license (SPDX identifier)
- Confidence level (High/Medium/Low)
- Reasoning for suggestion
- Verification steps (how to manually confirm)
- Alternative licenses to check
- Risk assessment (Low/Medium/High)
- Quick links to package registry, homepage, repository
- Ready-to-use curation command (copy/paste)

**Model:** Azure OpenAI `gpt-4o-mini`
**Limit:** First 15 packages per run to control API costs

**⚠️ IMPORTANT:** AI suggestions are advisory only - always verify manually from actual LICENSE files.

#### 9. `generate_scancode_reports.py`
Generates consolidated ScanCode HTML and YAML summary reports from JSON scan results.

**Usage:**
```bash
python generate_scancode_reports.py scancode-results/
```

**Outputs:**
- `scancode-summary.html` - Beautiful web report with package-by-package analysis
- `scancode-summary.yml` - Machine-readable summary

**Features:**
- Package-by-package license analysis
- License confidence scores (high/medium/low color-coded)
- File coverage statistics
- Copyright statements
- Sample file paths for each license

#### 10. `generate_landing_page.py`
Generates GitHub Pages landing page with links to all reports.

**Usage:**
```bash
python generate_landing_page.py public
```

**Auto-detects:**
- Main AI curation report
- Conflict analysis report
- Missing licenses AI analysis (NEW)
- ORT WebApp report
- ORT Static HTML report (NEW)
- ScanCode summary reports (NEW)
- Individual ScanCode package reports (HTML/JSON/YAML) (NEW)
- Enhanced SPDX document
- CycloneDX SBOM
- Uncertain packages report

## Common Development Tasks

### Running Enhanced Analysis Locally

**Prerequisites:**
```bash
# Install ORT
ORT_VERSION="70.0.1"
wget https://github.com/oss-review-toolkit/ort/releases/download/${ORT_VERSION}/ort-${ORT_VERSION}.tgz
tar -xzf ort-${ORT_VERSION}.tgz
export PATH="${PWD}/ort-${ORT_VERSION}/bin:$PATH"

# Install Python dependencies
pip install python-inspector openai pyyaml spdx-tools scancode-toolkit
```

**Complete Enhanced Pipeline:**
```bash
# Stage 1: ORT Analysis
ort analyze -i . -o ort-results/analyzer
ort advise -i ort-results/analyzer/analyzer-result.yml -o ort-results/advisor --advisors OSV
ort report -i ort-results/analyzer/analyzer-result.yml -o ort-results/reporter -f WebApp,StaticHtml,CycloneDx,SpdxDocument

# Stage 2: Extract uncertain packages
python extract_uncertain_packages.py \
  --ort-result ort-results/analyzer/analyzer-result.yml \
  --output-dir uncertain-packages

# Stage 2.5: Fetch PyPI licenses (NEW - reduces ScanCode workload)
python fetch_pypi_licenses.py \
  ort-results/analyzer/analyzer-result.yml \
  --fetch \
  --json \
  --csv \
  --curations \
  --output-dir pypi-licenses

# Stage 3: ScanCode scanning (optimized - only packages without PyPI licenses)
head -n 20 uncertain-packages/uncertain-package-ids.txt > scan-list.txt
# Download packages and scan with ScanCode
# For each package:
scancode -clpieu \
  --html package-1.0.0.html \
  --json package-1.0.0.json \
  --yaml package-1.0.0.yml \
  --timeout 120 \
  --max-depth 3 \
  package-directory/

# Generate consolidated summary
python generate_scancode_reports.py scancode-results/

# Stage 4: Merge ScanCode results
python merge_scancode_to_spdx.py \
  --spdx ort-results/reporter/bom.spdx.yml \
  --scancode scancode-results/ \
  --output enhanced-spdx/bom-enhanced.spdx.json

# Validate and fix SPDX
python spdx-validation-fixer.py \
  -i enhanced-spdx/bom-enhanced.spdx.json \
  -o enhanced-spdx/bom-enhanced-fixed.spdx.json

# Stage 5: Triple AI Curation Reports
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="your-endpoint"

# 5a. Main ORT curation report
python ort_curation_script_html.py

# 5b. Conflict analysis report (if uncertain packages exist)
python enhanced_ai_curation.py \
  --ort-results ort-results/analyzer/analyzer-result.yml \
  --spdx-doc enhanced-spdx/bom-enhanced-fixed.spdx.json \
  --uncertain-packages uncertain-packages/uncertain-packages.json \
  --output curation-report-conflicts.html

# 5c. Missing licenses AI analysis (NEW)
python ai_missing_licenses_analyzer.py \
  uncertain-packages/uncertain-packages.json \
  curation-report-missing-licenses.html
```

### Managing License Curations

**Workflow for new package with missing license:**

```bash
# 1. Run analysis and extract uncertain packages
python extract_uncertain_packages.py --ort-result ort-results/analyzer/analyzer-result.yml --output-dir uncertain-packages

# 2. Check which packages need curation
cat uncertain-packages/report.md

# 3. Manually verify license (check GitHub repo, LICENSE file, package metadata)

# 4. Add curation
python manage_curations.py add \
  --id "NPM::new-package:1.0.0" \
  --license "MIT" \
  --comment "License verified from GitHub repository LICENSE file on 2025-01-02" \
  --original-license "NOASSERTION" \
  --homepage "https://github.com/org/new-package"

# 5. Validate
python manage_curations.py validate

# 6. Re-run ORT (curations are automatically applied from .ort/curations.yml)
ort analyze -i . -o ort-results-curated/analyzer
```

**Bulk curation workflow:**

```bash
# Generate curation templates for all uncertain packages
python manage_curations.py import-uncertain --file uncertain-packages/uncertain-packages.json

# Edit .ort/curations.yml and replace "REVIEW-REQUIRED" with actual licenses

# Validate all curations
python manage_curations.py validate

# Export for team review
python manage_curations.py export --output curations-review.csv
```

### Running ScanCode on Specific Packages

```bash
# Download package source
wget https://registry.npmjs.org/package/-/package-1.0.0.tgz
tar -xzf package-1.0.0.tgz

# Run ScanCode with all output formats (HTML, JSON, YAML)
scancode -clpieu \
  --html scancode-results/package-1.0.0.html \
  --json scancode-results/package-1.0.0.json \
  --yaml scancode-results/package-1.0.0.yml \
  --timeout 120 \
  --max-depth 3 \
  package/

# Flags:
# -c = copyright detection
# -l = license detection
# -p = package info
# -i = file info
# -e = email detection
# -u = url detection

# Review results
cat scancode-results/package-1.0.0.json | jq '.files[] | select(.licenses | length > 0) | {path, licenses}'

# Or open the native HTML report
# Windows: start scancode-results/package-1.0.0.html
# Linux: xdg-open scancode-results/package-1.0.0.html
# Mac: open scancode-results/package-1.0.0.html
```

## Important Configuration Details

### Required GitHub Secrets

**For Main ORT Curation Report:**
- `AZURE_OPENAI_API_KEY` - Azure OpenAI authentication key

**For Full Enhanced Analysis (Recommended):**
- `AZURE_OPENAI_API_KEY` - Azure OpenAI authentication key
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI service endpoint (e.g., `https://your-resource.openai.azure.com/`)
- `AZURE_OPENAI_MODEL` - Your Azure OpenAI deployment name (e.g., `gpt-4o-mini`, `gpt-4.1-mini`) ⚠️ **Important!**

**For Multi-Repository Orchestration:**
- `PAT_TOKEN` - Personal Access Token with `workflow` and `repo` scopes

**⚠️ Important: Azure OpenAI Deployment Name**

The `AZURE_OPENAI_MODEL` secret should contain your **deployment name**, NOT the model name:
- ❌ Wrong: `gpt-4o-mini` (model name)
- ✅ Correct: `your-actual-deployment-name` (what you named it in Azure Portal)

To find your deployment name:
1. Go to Azure Portal → Your OpenAI Resource → **Model deployments**
2. Copy the **deployment name** (the name in the list, not the base model)
3. Add it as `AZURE_OPENAI_MODEL` secret in GitHub

See `AZURE_OPENAI_SETUP.md` for detailed setup instructions.

### Azure OpenAI Model Configuration

**Main Curation Report (`ort_curation_script_html.py`):**
- Model: `gpt-4.1-mini`
- Deployment: Configured in script line 576
- Endpoint: Default or from `AZURE_OPENAI_ENDPOINT`
- Temperature: 0.3 (deterministic)
- Max tokens: 4000

**Conflict Analysis (`enhanced_ai_curation.py`):**
- Model: `gpt-4`
- Temperature: 0.3 (deterministic)
- Max tokens: 1000 per conflict
- Limit: First 20 conflicts to avoid token/cost limits

**Missing Licenses Analysis (`ai_missing_licenses_analyzer.py`):**
- Model: `gpt-4o-mini`
- Temperature: 0.3 (deterministic)
- Max tokens: 1000 per package
- Limit: First 15 packages to avoid token/cost limits

**AI Multi-Layer Resolution (`ai_multilayer_resolution.py`):**
- Model: `gpt-4.1-mini` (default, configurable via `AZURE_OPENAI_MODEL`)
- API Version: `2025-01-01-preview` (matches `ort_curation_script_html.py`)
- Temperature: 0.3 (deterministic)
- Max tokens: 800 per analysis
- Limit: 15 conflicts + 10 missing packages per run

### GitHub Pages Deployment

**Triggers:**
- Push to `main` or `master` branch
- Successful completion of ORT analysis

**Deployment structure:**
```
public/
├── index.html                             (Landing page with all report links)
├── curation-report-main.html              (Primary AI ORT analysis)
├── curation-report-conflicts.html         (Conflict analysis, if needed)
├── curation-report-missing-licenses.html  (AI missing licenses analysis)
├── scan-report-web-app.html               (ORT interactive WebApp)
├── scan-report.html                       (ORT static HTML)
├── scancode-summary.html                  (Consolidated ScanCode summary)
├── scancode-summary.yml                   (Machine-readable summary)
├── scancode-reports/                      (Individual package reports)
│   ├── package-1.0.0.html                 (Native ScanCode HTML)
│   ├── package-1.0.0.json                 (Raw scan data)
│   └── package-1.0.0.yml                  (Raw scan data)
├── pypi-licenses/                         (PyPI license fetch results) NEW
│   ├── pypi-licenses-full.json            (Complete fetch report)
│   ├── pypi-licenses-found.json           (Only packages with licenses found)
│   ├── pypi-licenses.csv                  (Spreadsheet format)
│   ├── curation-suggestions.yml           (Suggested curations)
│   └── pypi-fetch-stats.txt               (Statistics summary)
├── bom.cyclonedx.json                     (CycloneDX SBOM)
├── bom.spdx.yml                           (Original SPDX from ORT)
├── bom-enhanced.spdx.json                 (Enhanced with ScanCode findings)
├── uncertain-packages-report.md           (Packages needing review)
└── merge-report.md                        (ScanCode merge statistics)
```

### Artifact Retention

- ORT results: 30 days (`ort-results-{branch}-{run_number}`)
- ScanCode results: 30 days (`scancode-results-{branch}-{run_number}`)
- Enhanced reports: 30 days (`enhanced-reports-{branch}-{run_number}`)

## Triple AI Curation Report System

The system generates THREE types of AI-powered reports:

### 1. Main ORT Curation Report (`curation-report-main.html`)
**Purpose:** Comprehensive compliance analysis of entire project

**Generated when:** ORT analyzer completes successfully + Azure OpenAI configured

**Includes:**
- Executive summary with Go/No-Go verdict
- License distribution analysis
- Complete package inventory
- Risk assessment (high/medium/low)
- Actionable recommendations
- Compliance posture assessment

**Script:** `ort_curation_script_html.py`
**Model:** `gpt-4.1-mini`

### 2. License Conflict Analysis (`curation-report-conflicts.html`)
**Purpose:** Deep-dive resolution of license conflicts

**Generated when:** Uncertain packages detected + Multi-tool analysis completes

**Includes:**
- Conflict-by-conflict analysis (ORT vs. ScanCode)
- AI recommendations for each conflict
- Risk levels per package
- Specific resolution steps
- Links to verification sources

**Script:** `enhanced_ai_curation.py`
**Model:** `gpt-4`

### 3. Missing Licenses Analysis (`curation-report-missing-licenses.html`) ⭐ NEW
**Purpose:** AI research and suggestions for packages with blank/missing licenses

**Generated when:** Packages with NOASSERTION/blank licenses detected + Azure OpenAI configured

**Includes:**
- Suggested license (SPDX identifier) for each package
- Confidence level (High/Medium/Low)
- Reasoning for suggestion
- Step-by-step verification guide
- Alternative licenses to check
- Risk assessment (Low/Medium/High)
- Quick links to verify (registry, homepage, repository)
- Ready-to-use curation commands (copy/paste)

**Script:** `ai_missing_licenses_analyzer.py`
**Model:** `gpt-4o-mini`
**Limit:** First 15 packages per run

**⚠️ CRITICAL:** AI suggestions are advisory only. Always verify manually from actual LICENSE files in source repositories before adding curations.

See `CURATION_REPORTS.md` for complete documentation on the AI report system.

## Troubleshooting

### No AI Curation Reports Generated

**Check workflow step:** "Check AI curation prerequisites"

Look for:
```
✗ API key missing
```
**Solution:** Add `AZURE_OPENAI_API_KEY` in GitHub Settings → Secrets

**Check for:**
```
❌ ORT analyzer results not found!
```
**Solution:** Verify ORT analyzer step completed successfully

### ScanCode Not Finding Licenses

**Issue:** ScanCode completes but no licenses merged

**Check:**
```bash
# Verify ScanCode output
ls -lh scancode-results/
cat scancode-results/package-name.json | jq '.files[].licenses'
```

**Common causes:**
- Package source not downloaded (check `source_artifact_url` in uncertain packages)
- ScanCode timeout (increase with `--timeout 300`)
- Package is binary-only (no source files to scan)

### SPDX Validation Errors

**Issue:** Enhanced SPDX fails validation

**Solution:**
```bash
python spdx-validation-fixer.py \
  -i enhanced-spdx/bom-enhanced.spdx.json \
  -o enhanced-spdx/bom-enhanced-fixed.spdx.json

# Validate with official tools
pyspdxtools -i enhanced-spdx/bom-enhanced-fixed.spdx.json --validate
```

### Curations Not Applied

**Issue:** Re-running ORT still shows NOASSERTION for curated packages

**Check:**
```bash
# Verify curation file exists and is valid
cat .ort/curations.yml
python manage_curations.py validate

# Ensure package ID format matches exactly
# Format: "TYPE:NAMESPACE:NAME:VERSION"
# Example: "NPM::lodash:4.17.21" or "PyPI::requests:2.28.0"
```

## Enhanced Curation Strategy

The system implements a **6-tier multi-tool approach** for maximum license detection:

1. **ORT**: Fast package-manager aware analysis (primary)
2. **Uncertain Package Extraction**: Identifies gaps in ORT coverage
3. **PyPI API Fetch** (NEW): Fast license retrieval from package registries (no scanning needed)
4. **ScanCode**: Deep file-level license detection (optimized - only remaining packages)
5. **SPDX Enhancement**: Merges and validates findings
6. **AI Curation**: Intelligent conflict resolution and recommendations

This approach addresses ORT limitations:
- Incomplete package metadata
- New/emerging packages
- Non-standard license formats
- Embedded licenses in source files
- Complex multi-license scenarios

## File Structure Patterns

- `enhanced-ort-workflow.yml` - Main enhanced analysis workflow
- `ort_curation_script_html.py` - Primary AI report generator
- `enhanced_ai_curation.py` - Conflict analysis generator
- `extract_uncertain_packages.py` - License gap detection
- `merge_scancode_to_spdx.py` - Multi-tool result merger
- `manage_curations.py` - Curation database manager
- `spdx-validation-fixer.py` - SPDX validator and fixer
- `generate_landing_page.py` - GitHub Pages landing page
- `.ort/curations.yml` - Manual license curation database
- `*-result.yml` - ORT output files
- `bom.*` - Bill of Materials in various formats
- `curation-report-*.html` - AI-generated reports
- `uncertain-packages/` - Uncertain package analysis results
- `scancode-results/` - ScanCode JSON outputs
- `enhanced-spdx/` - Enhanced SPDX documents

## Output Format Details

- **SPDX Document**: Software Package Data Exchange (YAML/JSON) - official compliance format
- **Enhanced SPDX**: SPDX + ScanCode findings merged
- **CycloneDX**: Industry-standard SBOM (JSON)
- **ORT WebApp**: Interactive HTML with dependency visualization
- **StaticHTML**: Traditional static compliance report
- **AI Reports**: Beautiful HTML with gradient styling and actionable insights

## Development Notes

- Java 21 required for ORT
- Python 3.11 for all scripts
- ORT version: 70.0.1 (configured in workflow)
- ScanCode Toolkit: Installed via pip
- Azure OpenAI: API version `2025-01-01-preview`
- GitHub Pages deploys on push to `main` or `master` branch
- All workflows use `continue-on-error: true` for optional features
- Curation database (`.ort/curations.yml`) is version-controlled
- Landing page auto-detects and links all available reports

## Cost Optimization

**Per Workflow Run (with all AI features):**
- Main curation report: ~$0.05 USD (gpt-4.1-mini)
- Conflict analysis: ~$0.10-$0.20 USD (gpt-4, max 20 conflicts)
- Missing licenses analysis: ~$0.05-$0.08 USD (gpt-4o-mini, max 15 packages)
- **Total: ~$0.20-$0.33 USD per run**

**Without conflicts/missing:** ~$0.05 USD (main report only)

**Monthly estimate (daily runs):** ~$6-$10 USD per repository

**ScanCode:** Free and open-source, but time-intensive (limited to 20 uncertain packages in CI)

## Best Practices

### Curation Management
1. **Always commit curations** to `.ort/curations.yml` for team consistency
2. **Validate before committing:** `python manage_curations.py validate`
3. **Document curation reasons** - include verification source, date, and approver in comments
4. **Export for legal review** - use CSV export for compliance team review: `python manage_curations.py export --output review.csv`
5. **Archive compliance records** - download artifacts before 30-day expiration

### AI Usage (CRITICAL)
6. **AI is advisory only** - NEVER use AI suggestions without manual verification
7. **Always verify from source** - Check actual LICENSE files in GitHub repositories
8. **Check package registries** - Verify license declarations in NPM, PyPI, Maven Central
9. **Get compliance approval** - High-risk or production packages need legal/compliance team sign-off
10. **Document AI assistance** - Note in curation comments when AI suggestion was used and how it was verified

### ScanCode Optimization
11. **Limit ScanCode scope** - Workflow scans 20 packages max to save time (adjustable)
12. **Use high-confidence detections** - ScanCode scores ≥80% are reliable, ≥95% are very reliable
13. **Review native reports** - Individual package HTML reports provide detailed file-by-file analysis
14. **Check multiple formats** - Use JSON for automation, HTML for human review, YAML for git-friendly diffs

### Workflow Efficiency
15. **Run locally first** - Test on small projects before enabling for all repos
16. **Monitor costs** - Check Azure OpenAI usage dashboard monthly
17. **Adjust limits** - Reduce conflict/missing analysis limits if costs are too high
18. **Cache results** - Download artifacts for offline analysis when needed
