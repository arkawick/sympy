# Enhanced License Curation Implementation Guide

## Overview

This guide walks you through implementing a comprehensive multi-tool license detection and curation system that addresses ORT's limitations in detecting licenses for new or poorly-documented packages.

## Problem Statement

**ORT alone may miss licenses because:**
- Packages without proper license declarations in metadata
- New/emerging packages not in ORT's knowledge base
- Non-standard or custom license formats
- Embedded licenses in source files vs. package manifests
- Complex multi-licensed components

**Solution: Multi-Tool Approach**
- **Tier 1**: ORT (fast, package-manager aware)
- **Tier 2**: ScanCode Toolkit (deep file-level scanning)
- **Tier 3**: SPDX Validation & Merging
- **Tier 4**: AI Curation (intelligent recommendations)
- **Tier 5**: Manual Curation Database (team-approved overrides)

---

## Step-by-Step Implementation

### Phase 1: Local Testing (Recommended First)

#### Step 1.1: Install Required Tools

```bash
# Python dependencies
pip install python-inspector openai pyyaml spdx-tools scancode-toolkit

# Verify installations
scancode --version
pyspdxtools --version
```

#### Step 1.2: Run ORT Analysis

```bash
# Clean and create directories
rm -rf ort-results
mkdir -p ort-results

# Run ORT analyzer
ort analyze -i . -o ort-results/analyzer

# Run ORT advisor (optional)
ort advise \
  -i ort-results/analyzer/analyzer-result.yml \
  -o ort-results/advisor \
  --advisors OSV

# Generate SPDX document
ort report \
  -i ort-results/analyzer/analyzer-result.yml \
  -o ort-results/reporter \
  -f SpdxDocument
```

#### Step 1.3: Extract Packages with Uncertain Licenses

```bash
python extract_uncertain_packages.py \
  --ort-result ort-results/analyzer/analyzer-result.yml \
  --output-dir uncertain-packages

# Review the results
cat uncertain-packages/extraction-stats.txt
cat uncertain-packages/report.md
```

**What you'll get:**
- `uncertain-package-ids.txt` - Simple list of package IDs
- `uncertain-packages.json` - Full details in JSON
- `uncertain-packages.csv` - Spreadsheet-friendly format
- `download-packages.sh` - Script to download source code
- `report.md` - Human-readable summary
- `extraction-stats.txt` - Statistics

#### Step 1.4: Run ScanCode on Uncertain Packages

```bash
# Download packages
bash uncertain-packages/download-packages.sh

# Run ScanCode on downloaded packages
mkdir -p scancode-results

for pkg_dir in downloaded-packages/*/; do
  pkg_name=$(basename "$pkg_dir")
  echo "Scanning $pkg_name..."

  scancode \
    -l -c -i \
    --json "scancode-results/${pkg_name}.json" \
    --timeout 120 \
    --max-depth 3 \
    "$pkg_dir"
done
```

**ScanCode Options:**
- `-l` : Detect licenses
- `-c` : Detect copyrights
- `-i` : Get package info
- `--timeout 120` : 2 minutes per file max
- `--max-depth 3` : Limit directory depth

#### Step 1.5: Merge ScanCode Results into SPDX

```bash
python merge_scancode_to_spdx.py \
  --spdx ort-results/reporter/bom.spdx.yml \
  --scancode scancode-results/ \
  --output enhanced-spdx/bom-enhanced.spdx.json

# Validate and fix the enhanced SPDX
python spdx-validation-fixer.py \
  -i enhanced-spdx/bom-enhanced.spdx.json \
  -o enhanced-spdx/bom-enhanced-fixed.spdx.json

# Validate with official SPDX tools
pyspdxtools -i enhanced-spdx/bom-enhanced-fixed.spdx.json --validate
```

**What this does:**
- Matches ScanCode findings to SPDX packages
- Adds high-confidence license detections (≥80% score)
- Updates `licenseConcluded` field
- Adds `licenseComments` with detection details
- Generates merge report

#### Step 1.6: Run Enhanced AI Curation

```bash
# Set Azure OpenAI credentials
export AZURE_OPENAI_API_KEY="your-key-here"
export AZURE_OPENAI_ENDPOINT="your-endpoint-here"

python enhanced_ai_curation.py \
  --ort-results ort-results/analyzer/analyzer-result.yml \
  --spdx-doc enhanced-spdx/bom-enhanced-fixed.spdx.json \
  --uncertain-packages uncertain-packages/uncertain-packages.json \
  --output curation-report-enhanced.html

# Open the report
# Windows: start curation-report-enhanced.html
# Linux: xdg-open curation-report-enhanced.html
# Mac: open curation-report-enhanced.html
```

**AI Analysis provides:**
- Conflict resolution between ORT and ScanCode
- License compatibility analysis
- Compliance risk assessment (low/medium/high)
- Recommended actions for each package
- Natural language explanations

#### Step 1.7: Create Manual Curations

```bash
# Generate curation templates for packages needing review
python manage_curations.py import-uncertain \
  --file uncertain-packages/uncertain-packages.json

# This creates .ort/curations.yml with templates

# Edit .ort/curations.yml and update licenses
# Replace "REVIEW-REQUIRED" with actual SPDX license identifiers

# Validate your curations
python manage_curations.py validate

# List all curations
python manage_curations.py list

# Export for team review
python manage_curations.py export --output curations-review.csv
```

**Manual curation commands:**

```bash
# Add a single curation
python manage_curations.py add \
  --id "NPM::example-package:1.0.0" \
  --license "MIT" \
  --comment "License verified from GitHub repository LICENSE file" \
  --original-license "NOASSERTION" \
  --homepage "https://github.com/example/package"

# Remove a curation
python manage_curations.py remove --id "NPM::example-package:1.0.0"
```

#### Step 1.8: Re-run ORT with Curations

```bash
# ORT automatically loads curations from .ort/curations.yml
ort analyze -i . -o ort-results-curated/analyzer

# Generate final reports
ort report \
  -i ort-results-curated/analyzer/analyzer-result.yml \
  -o ort-results-curated/reporter \
  -f WebApp,StaticHtml,SpdxDocument,CycloneDx
```

---

### Phase 2: GitHub Actions Integration

#### Step 2.1: Update Your Workflow

Replace your current `action_ort_llm_workflow_deploy.yml` with the new `enhanced-ort-workflow.yml`:

```bash
# Backup current workflow
mv .github/workflows/action_ort_llm_workflow_deploy.yml \
   .github/workflows/action_ort_llm_workflow_deploy.yml.backup

# Use new enhanced workflow
cp enhanced-ort-workflow.yml \
   .github/workflows/enhanced-ort-analysis.yml
```

#### Step 2.2: Commit All New Files

```bash
git add \
  extract_uncertain_packages.py \
  merge_scancode_to_spdx.py \
  enhanced_ai_curation.py \
  manage_curations.py \
  .ort/curations.yml \
  .github/workflows/enhanced-ort-analysis.yml

git commit -m "Add enhanced license curation system with ScanCode integration"
git push
```

#### Step 2.3: Trigger Workflow

The workflow will automatically run on:
- Push to `main` or `develop` branches
- Pull requests
- Manual dispatch (Actions tab → Run workflow)

**Workflow stages:**
1. ORT Analyzer + Advisor
2. Extract uncertain packages
3. Download and scan with ScanCode (limited to 10 packages in CI)
4. Merge ScanCode results into SPDX
5. Validate and fix SPDX document
6. Enhanced AI curation with GPT-4
7. Deploy reports to GitHub Pages
8. Upload artifacts (30-day retention)

---

## Usage Scenarios

### Scenario 1: New Package with Missing License

**Problem:** ORT reports `NOASSERTION` for a new npm package.

**Solution:**

1. Extract uncertain packages:
   ```bash
   python extract_uncertain_packages.py \
     --ort-result ort-results/analyzer/analyzer-result.yml \
     --output-dir uncertain-packages
   ```

2. Check if package is in the list:
   ```bash
   grep "my-new-package" uncertain-packages/uncertain-packages.json
   ```

3. Run ScanCode on that package:
   ```bash
   # Download source
   wget <source-url> -O package.tar.gz
   tar -xzf package.tar.gz

   # Scan
   scancode -l -c --json scancode-results/my-new-package.json package/
   ```

4. Review ScanCode findings:
   ```bash
   cat scancode-results/my-new-package.json | grep -A 5 "license"
   ```

5. Add manual curation:
   ```bash
   python manage_curations.py add \
     --id "NPM::my-new-package:1.0.0" \
     --license "MIT" \
     --comment "License detected by ScanCode from LICENSE file in source repository" \
     --original-license "NOASSERTION"
   ```

6. Re-run ORT (curations are automatically applied).

### Scenario 2: License Conflict Between Tools

**Problem:** ORT says "Apache-2.0", but ScanCode detects "MIT".

**Solution:**

1. Run enhanced AI curation:
   ```bash
   python enhanced_ai_curation.py \
     --ort-results ort-results/analyzer/analyzer-result.yml \
     --spdx-doc enhanced-spdx/bom-enhanced-fixed.spdx.json \
     --uncertain-packages uncertain-packages/uncertain-packages.json \
     --output curation-report-enhanced.html
   ```

2. Open HTML report and find the package - AI will provide:
   - Analysis of the conflict
   - Most likely correct license
   - Recommended action
   - Risk level

3. Manually verify:
   - Check package homepage
   - Review LICENSE file in source repository
   - Check package.json or setup.py
   - Search GitHub issues for license discussions

4. Add definitive curation:
   ```bash
   python manage_curations.py add \
     --id "PyPI::conflicted-package:2.0.0" \
     --license "MIT" \
     --comment "Confirmed MIT from LICENSE file in repository. Package metadata was incorrect. Notified maintainer via issue #123." \
     --original-license "Apache-2.0" \
     --homepage "https://github.com/example/conflicted-package"
   ```

### Scenario 3: Bulk Processing for New Project

**Problem:** Starting compliance checks for a large project with many packages.

**Solution:**

```bash
# 1. Run full pipeline locally first
bash << 'SCRIPT'
set -e

echo "Stage 1: ORT Analysis..."
ort analyze -i . -o ort-results/analyzer
ort report -i ort-results/analyzer/analyzer-result.yml -o ort-results/reporter -f SpdxDocument

echo "Stage 2: Extract uncertain packages..."
python extract_uncertain_packages.py --ort-result ort-results/analyzer/analyzer-result.yml --output-dir uncertain-packages

echo "Stage 3: ScanCode (limited to top 20)..."
head -n 20 uncertain-packages/uncertain-package-ids.txt > scan-list.txt
# Download and scan...
# (See Step 1.4 above)

echo "Stage 4: Merge results..."
python merge_scancode_to_spdx.py --spdx ort-results/reporter/bom.spdx.yml --scancode scancode-results/ --output enhanced-spdx/bom-enhanced.spdx.json
python spdx-validation-fixer.py -i enhanced-spdx/bom-enhanced.spdx.json -o enhanced-spdx/bom-enhanced-fixed.spdx.json

echo "Stage 5: AI Curation..."
python enhanced_ai_curation.py --ort-results ort-results/analyzer/analyzer-result.yml --spdx-doc enhanced-spdx/bom-enhanced-fixed.spdx.json --uncertain-packages uncertain-packages/uncertain-packages.json --output curation-report.html

echo "Stage 6: Generate curation templates..."
python manage_curations.py import-uncertain --file uncertain-packages/uncertain-packages.json

echo "✅ Pipeline complete! Review curation-report.html and update .ort/curations.yml"
SCRIPT

# 2. Review AI recommendations in curation-report.html
# 3. Update .ort/curations.yml with correct licenses
# 4. Validate curations
python manage_curations.py validate

# 5. Re-run ORT with curations
ort analyze -i . -o ort-results-final/analyzer
ort report -i ort-results-final/analyzer/analyzer-result.yml -o ort-results-final/reporter -f WebApp,SpdxDocument,CycloneDx

# 6. Commit curations for team
git add .ort/curations.yml
git commit -m "Add license curations for all dependencies"
```

---

## Best Practices

### 1. Curation Quality

✅ **DO:**
- Always include detailed comments explaining why the curation was needed
- Add verification source (GitHub issue, LICENSE file, maintainer confirmation)
- Include homepage and source URLs
- Date your comments
- Use proper SPDX license identifiers

❌ **DON'T:**
- Leave "REVIEW-REQUIRED" in production
- Guess licenses without verification
- Use custom identifiers without "LicenseRef-" prefix
- Skip comments

### 2. ScanCode Usage

✅ **DO:**
- Use timeouts to avoid hanging on large packages
- Limit directory depth for large monorepos
- Focus on packages with NOASSERTION first
- Review high-confidence detections (≥95%) manually

❌ **DON'T:**
- Scan entire node_modules or site-packages
- Trust low-confidence detections without review
- Skip validation after merging

### 3. AI Curation

✅ **DO:**
- Use AI as a recommendation tool, not final authority
- Verify high-risk recommendations manually
- Limit batch size to avoid token limits (max 20 packages)
- Review all AI suggestions before accepting

❌ **DON'T:**
- Blindly accept AI recommendations
- Use AI for legal advice
- Skip manual verification for critical packages

### 4. Team Workflow

1. **Developer**: Adds new dependency
2. **CI/CD**: Runs enhanced ORT workflow
3. **Report**: Shows uncertain licenses in PR comment
4. **Developer**: Reviews AI recommendations
5. **Developer**: Adds curation if needed
6. **Lead**: Approves curation in code review
7. **CI/CD**: Re-runs with curation applied
8. **Merge**: Only if all licenses are clear

---

## Troubleshooting

### Issue: ScanCode times out

**Solution:**
```bash
# Increase timeout
scancode --timeout 300 ...

# Or reduce scope
scancode --max-depth 2 ...
```

### Issue: SPDX validation fails

**Solution:**
```bash
# Use our fixer
python spdx-validation-fixer.py -i broken.spdx.json -o fixed.spdx.json

# Create stub packages instead of removing relationships
python spdx-validation-fixer.py -i broken.spdx.json -o fixed.spdx.json --create-stubs
```

### Issue: AI curation fails with rate limit

**Solution:**
```bash
# Reduce batch size in enhanced_ai_curation.py (line 286)
# Change from 20 to 10:
conflicts_to_analyze = self.conflicts[:10]
```

### Issue: Package name mismatch between ORT and ScanCode

**Solution:**
The merge script handles fuzzy matching, but you can check:
```python
# In merge_scancode_to_spdx.py, the normalize_package_name function
# handles common variations (hyphens, underscores, dots)

# If still failing, rename ScanCode output file to match ORT package name:
mv scancode-results/wrong-name.json scancode-results/correct-name.json
```

---

## Maintenance

### Weekly

```bash
# Review new uncertain packages
python extract_uncertain_packages.py --ort-result ort-results/analyzer/analyzer-result.yml --output-dir uncertain-packages
python manage_curations.py import-uncertain --file uncertain-packages/uncertain-packages.json

# Update curations.yml
# Validate
python manage_curations.py validate
```

### Monthly

```bash
# Export curations for team review
python manage_curations.py export --output curations-$(date +%Y-%m).csv

# Share with legal/compliance team
# Update based on feedback
```

### Before Release

```bash
# Full validation
python manage_curations.py validate

# Ensure no REVIEW-REQUIRED licenses
grep -r "REVIEW-REQUIRED" .ort/curations.yml && echo "❌ Unresolved curations!" || echo "✅ All curations resolved"

# Generate final SBOM
ort analyze -i . -o release-ort/analyzer
ort report -i release-ort/analyzer/analyzer-result.yml -o release-ort/reporter -f SpdxDocument,CycloneDx

# Archive for compliance records
tar -czf license-compliance-$(date +%Y-%m-%d).tar.gz release-ort/ .ort/curations.yml
```

---

## Success Metrics

Track these metrics to measure effectiveness:

```bash
# License coverage improvement
python extract_uncertain_packages.py --ort-result ort-results/analyzer/analyzer-result.yml --output-dir uncertain-packages
cat uncertain-packages/extraction-stats.txt

# Before curation: "Coverage: 75.3% packages have clear licenses"
# After curation:  "Coverage: 98.1% packages have clear licenses"
```

**Target Goals:**
- License coverage: >95%
- High-risk conflicts: 0
- Manual review needed: <5 packages
- Curation accuracy: 100% (verified)

---

## Support and Resources

**SPDX License List**: https://spdx.org/licenses/
**ORT Documentation**: https://github.com/oss-review-toolkit/ort
**ScanCode**: https://github.com/nexB/scancode-toolkit
**Azure OpenAI**: https://learn.microsoft.com/en-us/azure/ai-services/openai/

**Questions?**
1. Check the AI curation report for recommendations
2. Review package homepage and repository
3. Search for similar packages in your curation database
4. Consult with legal/compliance team for uncertain cases
