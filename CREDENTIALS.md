# Credentials Management Guide

This document explains how credentials are securely managed in this project.

## Security Best Practices

### ✅ DO
- Store all credentials in `.env.local` (git-ignored)
- Use environment variables in scripts
- Rotate credentials periodically
- Keep `.env.local` private and secure
- Use strong, unique passwords

### ❌ DON'T
- Commit `.env` or `.env.local` to git
- Share credentials in chat, email, or tickets
- Use default passwords in production
- Store credentials in code comments
- Log sensitive data

---

## Files and Their Purpose

### `.env` (Git-Tracked)
- **Purpose:** Template for non-sensitive config
- **Content:** IP addresses, intervals, API endpoints
- **Safety:** Safe to commit, no secrets
- **Example:**
  ```
  WYZE_CAM_IP=10.10.10.207
  READING_INTERVAL=600
  ```

### `.env.local` (Git-Ignored)
- **Purpose:** Store sensitive credentials locally
- **Content:** Passwords, API keys, tokens
- **Safety:** NEVER committed to git
- **Example:**
  ```
  GRAFANA_USER=sean@ecoworks.ca
  GRAFANA_PASSWORD=***REMOVED***
  ANTHROPIC_API_KEY=sk-ant-...
  ```

---

## Current Credentials

### Camera Access
- **IP:** 10.10.10.207
- **User:** root
- **Password:** ***REMOVED***
- **Location:** `.env`

### Grafana Dashboard
- **URL:** http://localhost:3000
- **User:** sean@ecoworks.ca
- **Password:** ***REMOVED***
- **Location:** `.env.local`

### Anthropic API
- **Key:** ***REMOVED***...
- **Location:** `.env`
- **Note:** Only this summary shown; full key in `.env.local`

---

## Loading Credentials in Scripts

### Option 1: Environment Variables (Recommended)
```bash
# Load before running script
set -a && source .env && source .env.local && set +a
python3 wyze_cam_monitor.py
```

### Option 2: In Python Code
```python
import os
from pathlib import Path

# Load .env files
env_file = Path(".env")
local_file = Path(".env.local")

for line in env_file.read_text().split('\n'):
    if line.strip() and not line.startswith('#'):
        key, value = line.split('=', 1)
        os.environ[key.strip()] = value.strip()

# Load local credentials
if local_file.exists():
    for line in local_file.read_text().split('\n'):
        if line.strip() and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()
```

---

## Git Safety Verification

### Check What's Ignored
```bash
# Verify .env files are ignored
git check-ignore .env
git check-ignore .env.local

# Should output: .env and .env.local respectively
```

### Prevent Accidental Commits
```bash
# Configure git to warn about credentials
git config core.safecrlf true

# Add pre-commit hook (optional)
echo "#!/bin/bash
if git diff --cached | grep -E 'password|token|key|secret' > /dev/null; then
  echo 'ERROR: Possible credentials in commit!'
  exit 1
fi" > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## Rotating Credentials

When you change a password:

1. **Update locally:**
   ```bash
   # Edit .env.local with new credentials
   nano .env.local
   ```

2. **Verify git ignores it:**
   ```bash
   git status
   # Should NOT show .env.local
   ```

3. **Test the change:**
   ```bash
   set -a && source .env.local && set +a
   # Verify login works
   ```

4. **Document the change** (without including password):
   ```markdown
   - Updated Grafana user password (2025-11-15)
   - Changed camera root password (2025-11-15)
   ```

---

## Emergency: Leaked Credentials

If you accidentally commit credentials:

1. **Stop using those credentials immediately**
2. **Change the passwords/keys**
3. **Remove from git history:**
   ```bash
   git filter-branch --tree-filter 'rm -f .env .env.local' -- --all
   git push --force-with-lease
   ```
4. **Notify team** (if applicable)
5. **Regenerate credentials** from scratch

---

## Credential Storage Comparison

| Method | Security | Convenience | Recommended |
|--------|----------|-------------|-------------|
| Hardcoded | ❌ Worst | ✅ Easy | NO |
| `.env` in git | ❌ Bad | ✅ Easy | NO |
| `.env.local` (git-ignored) | ✅ Good | ✅ Easy | **YES** |
| Environment variables | ✅ Good | ⚠️ Hard | For CI/CD |
| Secret manager | ✅✅ Best | ⚠️ Complex | Enterprise |

---

## Tools for Credential Management

### Local Development
- **Use:** `.env.local` (git-ignored)
- **Tool:** None needed
- **Security:** File permissions (chmod 600)

### CI/CD Pipeline
- **Use:** GitHub Secrets, GitLab Variables
- **Tool:** CI/CD platform native
- **Security:** Platform-managed encryption

### Production Deployment
- **Use:** HashiCorp Vault, AWS Secrets Manager
- **Tool:** Professional secret manager
- **Security:** Enterprise-grade encryption

---

## File Permissions

Make credentials file readable only by you:

```bash
# Set restrictive permissions on .env.local
chmod 600 .env.local

# Verify
ls -la .env.local
# Should show: -rw------- (600)
```

---

## Summary

✅ **Your project is secure because:**
- `.env.local` is git-ignored
- `.gitignore` includes all credential patterns
- Sensitive data is isolated
- Clear documentation for safe practices

🔒 **Remember:**
- Never share `.env.local`
- Never commit credentials to git
- Rotate credentials periodically
- Use strong, unique passwords

