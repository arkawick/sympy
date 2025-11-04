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

The enhanced workflow uses a 5-tier approach to maximize license detection:

```
Source Code → ORT Analyzer → ORT Advisor → ORT Reporter
                    ↓              ↓              ↓
              Dependencies   Vulnerabilities   SPDX/CycloneDX
                                                    ↓
                              Extract Uncertain Packages
                                       ↓
                              ScanCode Deep Scan (file-level)
                                       ↓
                              Merge Results → Enhanced SPDX
                                       ↓
                         Dual AI Curation (Main + Conflicts)
                                       ↓
                              GitHub Pages Deployment
```

**Pipeline Stages:**
1. **ORT Analyzer**: Identifies all dependencies and declared licenses → `analyzer-result.yml`
2. **ORT Advisor**: Cross-references against OSV vulnerability database → `advise-result.yml`
3. **Uncertain Package Extraction**: Finds packages with NOASSERTION/UNKNOWN licenses
4. **ScanCode Scanning**: Deep file-level license detection on uncertain packages
5. **SPDX Enhancement**: Merges ScanCode findings into SPDX document
6. **AI Curation - Main**: Comprehensive compliance analysis with recommendations
7. **AI Curation - Conflicts**: Focused analysis of license conflicts and uncertainties
8. **GitHub Pages**: Deploy all reports with landing page

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

#### 2. `merge_scancode_to_spdx.py`
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

#### 3. `enhanced_ai_curation.py`
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

#### 4. `ort_curation_script_html.py`
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

#### 5. `spdx-validation-fixer.py`
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

#### 6. `manage_curations.py`
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

#### 7. `generate_landing_page.py`
Generates GitHub Pages landing page with links to all reports.

**Usage:**
```bash
python generate_landing_page.py public
```

**Auto-detects:**
- Main AI curation report
- Conflict analysis report
- ORT WebApp report
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

# Stage 3: ScanCode scanning (on top 10 uncertain packages)
head -n 10 uncertain-packages/uncertain-package-ids.txt > scan-list.txt
# Download and scan packages manually or use workflow automation

# Stage 4: Merge ScanCode results
python merge_scancode_to_spdx.py \
  --spdx ort-results/reporter/bom.spdx.yml \
  --scancode scancode-results/ \
  --output enhanced-spdx/bom-enhanced.spdx.json

# Validate and fix SPDX
python spdx-validation-fixer.py \
  -i enhanced-spdx/bom-enhanced.spdx.json \
  -o enhanced-spdx/bom-enhanced-fixed.spdx.json

# Stage 5: AI Curation Reports
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="your-endpoint"

# Main ORT curation report
python ort_curation_script_html.py

# Conflict analysis report (if uncertain packages exist)
python enhanced_ai_curation.py \
  --ort-results ort-results/analyzer/analyzer-result.yml \
  --spdx-doc enhanced-spdx/bom-enhanced-fixed.spdx.json \
  --uncertain-packages uncertain-packages/uncertain-packages.json \
  --output curation-report-conflicts.html
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

# Run ScanCode
scancode -l -c -i \
  --json scancode-results/package-1.0.0.json \
  --timeout 120 \
  --max-depth 3 \
  package/

# Review results
cat scancode-results/package-1.0.0.json | jq '.files[] | select(.licenses | length > 0) | {path, licenses}'
```

## Important Configuration Details

### Required GitHub Secrets

**For Main ORT Curation Report:**
- `AZURE_OPENAI_API_KEY` - Azure OpenAI authentication key

**For Full Enhanced Analysis (Recommended):**
- `AZURE_OPENAI_API_KEY` - Azure OpenAI authentication key
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI service endpoint

**For Multi-Repository Orchestration:**
- `PAT_TOKEN` - Personal Access Token with `workflow` and `repo` scopes

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

### GitHub Pages Deployment

**Triggers:**
- Push to `main` or `master` branch
- Successful completion of ORT analysis

**Deployment structure:**
```
public/
├── index.html                        (Landing page with all report links)
├── curation-report-main.html         (Primary AI ORT analysis)
├── curation-report-conflicts.html    (Conflict analysis, if needed)
├── scan-report-web-app.html          (ORT interactive WebApp)
├── scan-report.html                  (ORT static HTML)
├── bom.cyclonedx.json               (CycloneDX SBOM)
├── bom.spdx.yml                     (Original SPDX from ORT)
├── bom-enhanced.spdx.json           (Enhanced with ScanCode findings)
├── uncertain-packages-report.md     (Packages needing review)
└── merge-report.md                  (ScanCode merge statistics)
```

### Artifact Retention

- ORT results: 30 days (`ort-results-{branch}-{run_number}`)
- ScanCode results: 30 days (`scancode-results-{branch}-{run_number}`)
- Enhanced reports: 30 days (`enhanced-reports-{branch}-{run_number}`)

## Dual AI Curation Report System

The system generates TWO types of AI-powered reports:

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

See `CURATION_REPORTS.md` for complete documentation on the dual-report system.

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

The system implements a **5-tier multi-tool approach** for maximum license detection:

1. **ORT**: Fast package-manager aware analysis (primary)
2. **Uncertain Package Extraction**: Identifies gaps in ORT coverage
3. **ScanCode**: Deep file-level license detection (secondary)
4. **SPDX Enhancement**: Merges and validates findings
5. **AI Curation**: Intelligent conflict resolution and recommendations

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

**Per Workflow Run (with AI):**
- Main curation report: ~$0.05-$0.10 USD (gpt-4.1-mini)
- Conflict analysis: ~$0.10-$0.20 USD (gpt-4, max 20 conflicts)
- Total: ~$0.15-$0.30 USD per run

**Without conflicts:** ~$0.05-$0.10 USD (main report only)

**ScanCode:** Free and open-source, but time-intensive (limit to uncertain packages)

## Best Practices

1. **Always commit curations** to `.ort/curations.yml` for team consistency
2. **Validate curations** before committing: `python manage_curations.py validate`
3. **Review AI recommendations** - don't blindly accept, verify from official sources
4. **Limit ScanCode scope** - only scan packages with NOASSERTION to save time
5. **Use high-confidence detections** - ScanCode scores ≥80% are reliable
6. **Document curation reasons** - include verification source in comments
7. **Export for legal review** - use CSV export for compliance team review
8. **Archive compliance records** - download artifacts before 30-day expiration
