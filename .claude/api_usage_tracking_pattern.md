# Global Pattern: API Usage Tracking by Project

## Standard Practice for All Projects

When using Anthropic Claude API (or any AI API) in projects, always include project-specific tracking:

### 1. Environment Configuration (.env file)
```bash
# Anthropic API Configuration
ANTHROPIC_API_KEY=sk-ant-...
PROJECT_ID=<project-name>  # Use kebab-case, descriptive name
```

### 2. API Client Configuration
```python
import anthropic
import os

PROJECT_ID = os.getenv("PROJECT_ID", "default-project")

client = anthropic.Anthropic(
    api_key=api_key,
    default_headers={
        "anthropic-client-id": PROJECT_ID,
    }
)

# Add metadata to API calls
response = client.messages.create(
    model=model,
    metadata={
        "user_id": PROJECT_ID,
    },
    messages=[...]
)
```

### 3. Benefits
- Track API usage by project in Anthropic dashboard
- Separate costs and usage metrics across different projects
- Easier debugging and monitoring
- Better budget management

### 4. Project ID Naming Convention
Use descriptive, kebab-case names:
- `utility-meter-monitor` (this project)
- `document-analyzer`
- `chatbot-backend`
- `image-classifier-prod`

## Apply This Pattern To:
- All new projects using Claude API
- Existing projects during next refactor
- Scripts and tools that make API calls
- Production and development environments (use different IDs)

---
Created: 2025-11-18
Location: .claude/api_usage_tracking_pattern.md
