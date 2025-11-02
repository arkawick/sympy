# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This repository implements an **ORT (Open Source Review Toolkit) License Curation System** that performs automated open-source license compliance analysis enhanced with AI-powered recommendations. The system analyzes project dependencies, identifies licenses and vulnerabilities, generates standardized reports (SPDX, CycloneDX), and deploys them to GitHub Pages.

## Core Architecture

### Three-Tier Workflow System

1. **Individual Repository Analysis** (`action_ort_llm_workflow_deploy.yml`)
   - Runs ORT Analyzer → Advisor → Reporter pipeline on individual projects
   - Generates AI-powered curation recommendations using Azure OpenAI
   - Deploys interactive reports to GitHub Pages
   - Creates multiple output formats (WebApp, StaticHTML, CycloneDX, SPDX)

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

### ORT Analysis Pipeline Stages

The core analysis follows this sequence:

```
Source Code → ORT Analyzer → ORT Advisor → ORT Reporter → AI Curation → GitHub Pages
                    ↓              ↓              ↓              ↓
           Dependencies    Vulnerabilities   SPDX/CycloneDX   Recommendations
```

**Stage Details:**
- **ORT Analyzer**: Identifies all dependencies and declared licenses → `analyzer-result.yml`
- **ORT Advisor**: Cross-references against OSV vulnerability database → `advise-result.yml`
- **ORT Reporter**: Generates multi-format reports (WebApp, StaticHTML, CycloneDX, SPDX)
- **AI Curation**: Uses Azure OpenAI to provide natural language compliance guidance

### Smart Input Selection

The reporter automatically uses the most complete result file:
1. Prefer scanner results if available
2. Fall back to advisor results
3. Fall back to analyzer results if advisor failed

## Key Components

### SPDX Validation Tool (`spdx-validation-fixer.py`)

Critical utility for fixing ORT-generated SPDX documents. Common issues it resolves:
- **Broken references**: SPDX IDs referenced but not defined
- **Invalid package names**: Dots in package names (e.g., `coverage.toml` → `coverage-toml`)
- **Missing packages**: Creates stub packages or removes broken relationships

**Usage:**
```bash
python spdx-validation-fixer.py -i ort-results/reporter/bom.spdx.yml -o bom-fixed.spdx.yml
python spdx-validation-fixer.py -i bom.spdx.yml -o fixed.spdx.yml --create-stubs
python spdx-validation-fixer.py -i bom.spdx.yml --validate-only  # Check without fixing
```

### AI Curation Integration

Uses Azure OpenAI (requires secrets: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`) to:
- Clarify ambiguous licenses
- Identify potential license conflicts
- Suggest alternative packages
- Provide compliance guidance in natural language
- Generate executive summaries

The AI curation script (`ort_curation_script_html.py` - not present in codebase but referenced) generates HTML reports with pattern `curation-report-*.html`.

## Common Development Tasks

### Running ORT Analysis Locally

**Prerequisites:**
```bash
# Install ORT
ORT_VERSION="70.0.1"
wget https://github.com/oss-review-toolkit/ort/releases/download/${ORT_VERSION}/ort-${ORT_VERSION}.tgz
tar -xzf ort-${ORT_VERSION}.tgz
export PATH="${PWD}/ort-${ORT_VERSION}/bin:$PATH"

# Install Python dependencies
pip install python-inspector openai pyyaml spdx-tools
```

**Run Analysis:**
```bash
# Clean previous results
rm -rf ort-results
mkdir -p ort-results

# Run analyzer
ort analyze -i . -o ort-results/analyzer

# Run advisor (optional, continues on error)
ort advise -i ort-results/analyzer/analyzer-result.yml -o ort-results/advisor --advisors OSV

# Generate reports
ort report -i ort-results/analyzer/analyzer-result.yml -o ort-results/reporter -f WebApp,StaticHtml,CycloneDx,SpdxDocument
```

### Fixing SPDX Validation Errors

When ORT generates invalid SPDX documents:
```bash
# Validate and fix
python spdx-validation-fixer.py \
  -i ort-results/reporter/bom.spdx.yml \
  -o ort-results/reporter/bom-fixed.spdx.yml

# Create stub packages instead of removing relationships
python spdx-validation-fixer.py \
  -i bom.spdx.yml \
  -o bom-fixed.spdx.yml \
  --create-stubs
```

### Triggering Multi-Repository Analysis

**Manual trigger for specific repositories:**
```bash
# Via GitHub UI: Actions → Multi-Repo ORT Orchestrator → Run workflow
# Input: "scipy,numpy" (comma-separated)
```

**Via API:**
```bash
gh workflow run trigger-ort-analysis.yml -f repositories="scipy,numpy"
```

### Customizing Repository Lists

**Edit workflow files to add/remove repositories:**

In `trigger-ort-analysis.yml` (lines 24-27):
```yaml
repository:
  - owner/repo1
  - owner/repo2
```

In `generate-dashboard.yml` (lines 40-43):
```javascript
const repos = [
  'owner/repo1',
  'owner/repo2'
];
```

## Important Configuration Details

### Required GitHub Secrets

- `AZURE_OPENAI_API_KEY`: Azure OpenAI authentication
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI service endpoint
- `PAT_TOKEN`: Personal Access Token with `workflow` and `repo` scopes (for multi-repo orchestration)

### GitHub Pages Deployment

**Only deploys on:**
- Push to `main` branch
- Successful completion of ORT analysis

**Deployment structure:**
```
public/
├── index.html              (Landing page with report links)
├── scan-report-web-app.html
├── bom.cyclonedx.json
├── bom.spdx.yml
└── curation-report-*.html
```

### Artifact Retention

- ORT results: 30 days
- AI curation reports: 30 days
- Naming pattern: `{artifact-type}-{branch}-{run_number}`

## Error Handling Strategy

The workflows use `continue-on-error: true` strategically on:
- **ORT Advisor**: OSV database may be unavailable
- **AI Curation**: API may fail or be rate-limited
- **Vulnerability checks**: Parsing may fail on unexpected formats
- **PR comments**: Insufficient permissions

This ensures core analysis completes even if optional features fail.

## Enhanced Curation Strategy (Documentation)

The `enhanced-license-curation.md` describes a **multi-tool approach** for comprehensive license detection:

**Tier 1**: ORT (fast, package-manager aware)
**Tier 2**: ScanCode Toolkit (deep file-level scanning)
**Tier 3**: SPDX Tools (validation, standardization)
**Tier 4**: AI Curation (intelligence layer)

This strategy is documented but not yet fully implemented. When implementing, extract uncertain packages from ORT results, run ScanCode on them, merge results into enhanced SPDX documents.

## File Structure Patterns

- `action_*.yml`: GitHub Actions workflow definitions
- `*-result.yml`: ORT output files (analyzer/advisor/scanner results)
- `bom.*`: Bill of Materials in various formats (SPDX, CycloneDX)
- `curation-report-*.html`: AI-generated curation reports
- `dashboard-data.json`: Aggregated multi-repo status data

## License Detection Challenges

ORT may miss licenses due to:
- Incomplete package metadata
- New/emerging packages not in ORT's knowledge base
- Non-standard license formats
- Embedded licenses in source files
- Multi-licensed components

Use the SPDX validator to identify `NOASSERTION` or `UNKNOWN` licenses that need manual investigation or enhanced tooling (ScanCode).

## Output Format Details

**SPDX Document**: Software Package Data Exchange standard (YAML/JSON)
**CycloneDX**: Industry-standard SBOM format (JSON)
**WebApp Report**: Interactive HTML with dependency tree visualization
**StaticHTML**: Traditional static report with full compliance details

## Development Notes

- Java 21 required for ORT
- Python 3.11 for scripts and tooling
- ORT version pinned to 70.0.1 (update in workflow if needed)
- Dashboard auto-refreshes every 6 hours via scheduled workflow
- Pull request comments include direct links to artifacts and Pages preview
