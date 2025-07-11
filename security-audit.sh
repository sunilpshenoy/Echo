#!/bin/bash
# Security Audit Script for Pulse App
# Run this before each GitHub push

echo "🛡️  PULSE APP SECURITY AUDIT"
echo "================================"

# Check for accidentally staged sensitive files
echo "1. Checking for sensitive files..."
if git ls-files | grep -E '\.(env|key|pem|secret|token|credentials)$'; then
    echo "❌ WARNING: Sensitive files found in git!"
    exit 1
else
    echo "✅ No sensitive files in git"
fi

# Check for hardcoded secrets in code
echo "2. Scanning for hardcoded secrets..."
if grep -r "password\s*=" --include="*.js" --include="*.py" --exclude-dir="node_modules" --exclude-dir="__pycache__" frontend/ backend/ 2>/dev/null | grep -v "password_hash"; then
    echo "❌ WARNING: Possible hardcoded passwords found!"
    exit 1
else
    echo "✅ No hardcoded passwords detected"
fi

# Check for API keys
echo "3. Scanning for API keys..."
if grep -r "api[_-]key\s*=" --include="*.js" --include="*.py" --exclude-dir="node_modules" --exclude-dir="__pycache__" frontend/ backend/ 2>/dev/null; then
    echo "❌ WARNING: Possible hardcoded API keys found!"
    exit 1
else
    echo "✅ No hardcoded API keys detected"
fi

# Check environment files are ignored
echo "4. Verifying .env files are ignored..."
if git check-ignore frontend/.env backend/.env >/dev/null 2>&1; then
    echo "✅ Environment files properly ignored"
else
    echo "❌ WARNING: Environment files not properly ignored!"
    exit 1
fi

# Check obfuscation config is present
echo "5. Verifying security configurations..."
if [ -f "frontend/craco.config.js" ]; then
    echo "✅ Frontend obfuscation config present"
else
    echo "❌ WARNING: Frontend obfuscation config missing!"
    exit 1
fi

# Check build directory is ignored
echo "6. Verifying build files are ignored..."
mkdir -p frontend/build
echo "test" > frontend/build/test.js
if git check-ignore frontend/build/test.js >/dev/null 2>&1; then
    echo "✅ Build files properly ignored"
    rm -f frontend/build/test.js
    rmdir frontend/build 2>/dev/null || true
else
    echo "❌ WARNING: Build files not ignored!"
    rm -f frontend/build/test.js
    rmdir frontend/build 2>/dev/null || true
    exit 1
fi

echo ""
echo "🎉 SECURITY AUDIT PASSED!"
echo "✅ Repository is ready for secure GitHub push"
echo ""
echo "Remember:"
echo "- Make repository PRIVATE on GitHub"
echo "- Enable two-factor authentication"
echo "- Limit collaborator access"
echo "- Review commits before pushing"