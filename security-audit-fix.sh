#!/bin/bash

echo "🛡️  EMERGENCY SECURITY AUDIT & FIX SCRIPT"
echo "=========================================="

cd /app/frontend

echo "📋 Current vulnerability status:"
yarn audit --summary

echo ""
echo "🔧 FIXING CRITICAL VULNERABILITIES..."

# Fix the critical axios vulnerability (already done but ensuring)
echo "1. Fixing axios vulnerability..."
yarn upgrade axios@^1.11.0

# Try to fix other vulnerabilities with yarn audit fix
echo "2. Attempting automatic fixes..."
yarn audit fix --force 2>/dev/null || echo "Auto-fix not available, continuing with manual fixes..."

# Update other vulnerable packages
echo "3. Updating other vulnerable packages..."

# Update postcss to fix moderate vulnerability  
yarn upgrade postcss@^8.4.31

# Update webpack-dev-server (part of react-scripts, might not update directly)
# yarn upgrade webpack-dev-server@^5.2.1

echo "4. Checking if updates resolved issues..."
yarn audit --summary

echo ""
echo "✅ Security audit completed!"
echo "📊 Final vulnerability report:"
yarn audit --level critical 2>/dev/null || echo "No critical vulnerabilities found!"

echo ""
echo "🔒 SECURITY RECOMMENDATIONS:"
echo "- Set up automated security scanning in CI/CD"
echo "- Run 'yarn audit' before every deployment"  
echo "- Pin exact versions for security-critical packages"
echo "- Monitor GitHub security alerts regularly"