# ORT Analysis with AI Curation Deploy - Workflow Documentation

## Overview

This GitHub Actions workflow performs comprehensive open-source license compliance analysis using the Open Source Review Toolkit (ORT) and enhances it with AI-powered curation recommendations. The workflow analyzes project dependencies, identifies licenses and vulnerabilities, generates multiple standardized reports, and deploys them to GitHub Pages.

## Workflow Triggers

The workflow runs automatically on:
- **Push events** to `main` or `develop` branches
- **Pull requests** targeting `main` or `develop` branches
- **Manual dispatch** via GitHub UI

## Required Permissions

The workflow requires specific GitHub permissions:
- `contents: read` - Read repository contents
- `pages: write` - Deploy to GitHub Pages
- `id-token: write` - OIDC token for Pages deployment
- `pull-requests: write` - Comment on pull requests

## Concurrency Control

Prevents concurrent GitHub Pages deployments using a `pages` group with cancel-in-progress disabled to ensure deployment integrity.

## Job Breakdown: `ort-analysis`

### Environment Setup Steps

#### 1. **Checkout Code**
Uses `actions/checkout@v4` to clone the repository for analysis.

#### 2. **Python Setup**
Configures Python 3.11 environment for running Python-based tools and the AI curation script.

#### 3. **Java Setup**
Installs Java 21 (Temurin distribution) required by ORT, which is a Java-based application.

#### 4. **Python Dependencies Installation**
Installs critical Python packages:
- `python-inspector` - Dependency analysis tool
- `openai` - Azure OpenAI API client for AI curation
- `pyyaml` - YAML file parsing for ORT results

#### 5. **ORT Installation**
Downloads and extracts ORT version 70.0.1 from GitHub releases and adds it to the system PATH.

#### 6. **Installation Verification**
Validates that ORT and Java are correctly installed and accessible.

### Analysis Steps

#### 7. **Workspace Preparation**
Cleans previous results directory and creates fresh output directory structure.

#### 8. **ORT Analyzer**
Runs the first ORT stage:
```bash
ort analyze -i . -o ort-results/analyzer
```
- **Input**: Current directory (`.`) containing project files
- **Output**: Dependency tree and license information in `analyzer-result.yml`
- **Purpose**: Identifies all project dependencies and their declared licenses

#### 9. **ORT Advisor**
Executes the advisory stage with OSV (Open Source Vulnerabilities) database:
```bash
ort advise -i analyzer-result.yml -o ort-results/advisor --advisors OSV
```
- **Input**: Analyzer results from previous step
- **Output**: Vulnerability advisories in `advise-result.yml`
- **Purpose**: Cross-references dependencies against known security vulnerabilities
- **Note**: Continues on error to prevent blocking the workflow

#### 10. **AI Curation Report Generation**
Executes `ort_curation_script_html.py` with Azure OpenAI credentials:
- **Environment Variables**: 
  - `AZURE_OPENAI_API_KEY` - Authentication for Azure OpenAI
  - `AZURE_OPENAI_ENDPOINT` - API endpoint URL
- **Purpose**: Generates AI-powered license curation recommendations using LLM analysis
- **Output**: HTML report file with pattern `curation-report-*.html`
- **Note**: Continues on error to allow standard reports even if AI fails

#### 11. **ORT Reporter**
Generates multiple standardized output formats:
```bash
ort report -i [result-file] -o ort-results/reporter -f WebApp,StaticHtml,CycloneDx,SpdxDocument
```
- **Smart Input Selection**: Automatically uses the most complete result file (scanner > advisor > analyzer)
- **Output Formats**:
  - **WebApp**: Interactive HTML application with dependency visualization
  - **StaticHtml**: Traditional static HTML report
  - **CycloneDx**: Industry-standard SBOM (Software Bill of Materials)
  - **SpdxDocument**: SPDX-formatted compliance document

### Deployment Preparation

#### 12. **GitHub Pages Preparation**
Complex step that:
1. Creates `public/` directory for Pages deployment
2. Copies all ORT reporter outputs
3. Copies background image (if present) for landing page styling
4. Copies AI curation report (if generated)
5. Auto-detects actual filenames of generated reports
6. Generates a beautiful landing page (`index.html`) with:
   - Gradient background overlay
   - Responsive card-based layout
   - Links to all available reports
   - Highlighted AI curation report with "NEW" badge
   - Icons and descriptions for each report type

**Landing Page Features**:
- Modern, responsive design
- Hover animations on report cards
- Auto-detection of available reports
- Branded with "LTTS ORT Curation Report Generator"

### GitHub Pages Deployment (Main Branch Only)

#### 13-15. **Pages Deployment Steps**
Only executes on push to `main` branch:
- **Setup Pages**: Configures GitHub Pages settings
- **Upload Artifact**: Packages the `public/` directory
- **Deploy**: Publishes to GitHub Pages at `https://[owner].github.io/[repo]/`

### Artifact Management

#### 16. **Upload ORT Results**
Archives complete ORT output directory:
- **Name Pattern**: `ort-results-[branch]-[run_number]`
- **Retention**: 30 days
- **Always Runs**: Even if previous steps fail

#### 17. **Upload AI Curation Report**
Separately archives AI-generated reports:
- **Name Pattern**: `ai-curation-report-[branch]-[run_number]`
- **Pattern Match**: `curation-report-*.html`
- **Retention**: 30 days

### Reporting & Feedback

#### 18. **Vulnerability Check Summary**
Analyzes results and creates GitHub Actions summary:
- Counts vulnerabilities found
- Reports branch name
- Confirms AI report generation
- Notes Pages deployment status
- Outputs vulnerability count for PR comments

#### 19. **Pull Request Comment**
Automatically comments on PRs with:
- Success status
- Direct links to:
  - GitHub Pages preview (for merged PRs)
  - Workflow run artifacts
- List of generated artifacts
- AI curation summary excerpt (if available)
- Helpful tip about Pages deployment after merge

## Key Features

### Package License Curation
The workflow's primary purpose is **license curation** - the process of:
1. **Identifying** all software dependencies and their licenses
2. **Analyzing** license compatibility and compliance requirements
3. **Curating** recommendations using AI to:
   - Clarify ambiguous licenses
   - Identify potential conflicts
   - Suggest alternative packages
   - Provide compliance guidance

### AI Enhancement
The Azure OpenAI integration provides:
- Natural language explanations of licensing issues
- Context-aware curation recommendations
- Automated compliance documentation
- Human-readable summaries for non-legal teams

### Multi-Format Output
Generates reports in formats suitable for:
- **Developers**: Interactive WebApp for exploration
- **Legal Teams**: Static HTML with full details
- **Security Tools**: CycloneDX and SPDX for automated processing
- **Management**: AI-generated executive summaries

### Developer Experience
- Automatic PR comments with quick access links
- GitHub Pages deployment for easy sharing
- Persistent artifacts for compliance records
- Continue-on-error approach prevents blocking on non-critical failures

## Required Secrets

Must be configured in GitHub repository settings:
- `AZURE_OPENAI_API_KEY` - Azure OpenAI authentication key
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI service endpoint URL

## Output Locations

- **GitHub Pages**: `https://[owner].github.io/[repo]/` (main branch only)
- **Workflow Artifacts**: Available for 30 days in Actions tab
- **PR Comments**: Inline feedback with direct links

## Error Handling

The workflow uses strategic `continue-on-error: true` on:
- ORT Advisor (OSV database may be unavailable)
- AI Curation (API may fail or be unavailable)
- Vulnerability checks (parsing may fail on unexpected formats)
- PR comments (permissions may be insufficient)

This ensures that core analysis completes even if optional features fail.

## Best Practices

1. **Run on every PR** to catch licensing issues early
2. **Review AI curation suggestions** before accepting recommendations
3. **Archive artifacts** for compliance audit trails
4. **Monitor vulnerability counts** in workflow summaries
5. **Use GitHub Pages deployment** for stakeholder reviews