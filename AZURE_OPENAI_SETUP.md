# Azure OpenAI Model Deployment Setup

## Error: DeploymentNotFound

If you're seeing this error:
```
Error code: 404 - {'error': {'code': 'DeploymentNotFound', 'message': 'The API deployment for this resource does not exist.'}}
```

This means the model deployment name in the script doesn't match your actual Azure OpenAI deployment.

## Solution

### Step 1: Find Your Deployment Name

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Azure OpenAI resource
3. Click on **"Model deployments"** or **"Deployments"** in the left sidebar
4. Note the **deployment name** (NOT the model name)

**Example:**
- ❌ Model name: `gpt-4o-mini` (this is what the model is called)
- ✅ Deployment name: `gpt-4-mini-deployment` (this is YOUR deployment name)
- ✅ Or maybe: `my-gpt4-model`
- ✅ Or maybe: `gpt-4.1-mini` (if you're using an older deployment)

### Step 2: Set the Deployment Name in GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Add a new secret:
   - **Name**: `AZURE_OPENAI_MODEL`
   - **Value**: `your-actual-deployment-name` (from Step 1)
5. Click **"Add secret"**

### Step 3: Common Deployment Names

Based on your error, you might be using one of these:

**For ALL AI-powered scripts** (consistency is key):
- Main ORT curation script uses: `gpt-4.1-mini` (line 576 in the script)
- AI Multi-Layer Resolution uses: `gpt-4.1-mini` (default, line 56)
- You should use the SAME deployment name: `gpt-4.1-mini`

**Typical deployment names:**
- `gpt-4.1-mini` (recommended - used by working scripts)
- `gpt-4o-mini` (if you created it recently)
- `gpt-4-mini` (alternative naming)
- `gpt-35-turbo` (if using GPT-3.5)
- Custom names like: `my-compliance-model`, `ort-analysis-model`, etc.

### Step 4: Update Your Secrets

You need these **3 secrets** in GitHub:

| Secret Name | Value | How to Find |
|-------------|-------|-------------|
| `AZURE_OPENAI_API_KEY` | Your API key | Azure Portal → Your OpenAI Resource → Keys and Endpoint → KEY 1 |
| `AZURE_OPENAI_ENDPOINT` | Your endpoint URL | Azure Portal → Your OpenAI Resource → Keys and Endpoint → Endpoint |
| `AZURE_OPENAI_MODEL` | Your deployment name | Azure Portal → Your OpenAI Resource → Model deployments → Deployment name |

**Example values:**
```
AZURE_OPENAI_API_KEY: abc123def456...
AZURE_OPENAI_ENDPOINT: https://ltts-cariad-ddd-mvp-ai-foundry.cognitiveservices.azure.com/
AZURE_OPENAI_MODEL: gpt-4.1-mini
```

**Important Configuration Details:**
- API Version: Scripts use `2025-01-01-preview` (latest stable version)
- Deployment Name: `gpt-4.1-mini` is the default across all AI scripts
- If you have a different deployment name in Azure Portal, set `AZURE_OPENAI_MODEL` to match it

## Testing Locally

To test locally before committing:

```bash
# Set environment variables
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_MODEL="your-deployment-name"

# Test the AI resolution script
python ai_multilayer_resolution.py \
  --ort-result ort-results/analyzer/analyzer-result.yml \
  --pypi-results pypi-licenses/pypi-licenses-full.json \
  --scancode-dir scancode-results \
  --uncertain-packages uncertain-packages/uncertain-packages.json \
  --output test-report.html
```

You should see:
```
✓ Azure OpenAI client initialized
  Using model deployment: your-deployment-name
```

## Common Issues

### Issue 1: Still getting DeploymentNotFound
**Solution**: Double-check the deployment name is EXACT (case-sensitive!)

### Issue 2: Different deployment for different scripts
**Current setup:**
- `ort_curation_script_html.py` uses: `gpt-4.1-mini` (hardcoded in line 576)
- `enhanced_ai_curation.py` uses: `gpt-4` (hardcoded)
- `ai_missing_licenses_analyzer.py` uses: `gpt-4o-mini` (hardcoded)
- `ai_multilayer_resolution.py` uses: `AZURE_OPENAI_MODEL` env var ✅ (configurable)

**Recommendation**: Use the SAME deployment name for all scripts, or update other scripts to also use env var.

### Issue 3: Want to use a different model for different reports
**Solution**: You can create multiple deployments:
- `gpt-4-main` for main reports
- `gpt-4o-mini-quick` for quick analysis
- Set `AZURE_OPENAI_MODEL` to the one you want to use

## Model Recommendations

**For license compliance analysis:**
- ✅ **Best**: `gpt-4o` or `gpt-4o-mini` (latest, most accurate)
- ✅ **Good**: `gpt-4` (reliable, slightly older)
- ⚠️ **Budget**: `gpt-35-turbo` (cheaper but less accurate for compliance)

**Cost considerations:**
- `gpt-4o-mini`: ~$0.10-$0.15 per report (cheapest)
- `gpt-4o`: ~$0.30-$0.50 per report
- `gpt-4`: ~$0.50-$0.80 per report

## After Setup

Once you've set the `AZURE_OPENAI_MODEL` secret:
1. Push a new commit or manually re-run the workflow
2. The AI analysis should work
3. You'll see proper recommendations instead of error messages

## Need Help?

Check the workflow logs:
1. Go to **Actions** tab in GitHub
2. Click on the latest workflow run
3. Expand **"Generate AI multi-layer resolution report"** step
4. Look for:
   ```
   ✓ Azure OpenAI client initialized
     Using model deployment: your-deployment-name
   ```

If you still see errors, verify:
- [ ] Deployment name is correct and exists
- [ ] API key is valid
- [ ] Endpoint URL is correct
- [ ] Deployment has sufficient quota
