#!/bin/bash

echo "🚨 COMPREHENSIVE SECURITY VULNERABILITY FIX"
echo "============================================"
echo "📅 $(date)"
echo ""

# Fix Backend Vulnerabilities First (CRITICAL priority)
echo "🔧 FIXING BACKEND VULNERABILITIES..."
cd /app

echo "1. Fixing CRITICAL: Pillow < 10.2.0 → 10.3.0"
sed -i 's/Pillow==10.1.0/Pillow>=10.3.0/' backend/requirements.txt

echo "2. Fixing HIGH: python-multipart <= 0.0.6 → 0.0.7"
sed -i 's/python-multipart==0.0.6/python-multipart>=0.0.7/' backend/requirements.txt

echo "✅ Backend requirements.txt updated"
cat backend/requirements.txt

echo ""
echo "📦 Installing updated backend dependencies..."
cd /app && pip install -r backend/requirements.txt --upgrade

echo ""
echo "🔧 FIXING FRONTEND VULNERABILITIES..."
cd /app/frontend

echo "3. Updating HIGH: nth-check → 2.0.1+"
yarn upgrade nth-check@^2.0.1

echo "4. Updating MODERATE: postcss → 8.4.31+"
yarn upgrade postcss@^8.4.31

echo "5. Updating MODERATE: @babel/helpers → 7.26.10+"
yarn upgrade @babel/helpers@^7.26.10

echo "6. Updating MODERATE: @babel/runtime → 7.26.10+"
yarn upgrade @babel/runtime@^7.26.10

echo "7. Updating MODERATE: http-proxy-middleware → 2.0.8+"
yarn upgrade http-proxy-middleware@^2.0.8

echo "8. Updating MODERATE: webpack-dev-server → 5.2.1+"
yarn upgrade webpack-dev-server@^5.2.1

echo "9. Updating LOW: brace-expansion → 2.0.2+"
yarn upgrade brace-expansion@^2.0.2

echo "10. Updating LOW: on-headers → 1.1.0+"
yarn upgrade on-headers@^1.1.0

echo ""
echo "✅ All vulnerability fixes attempted!"
echo ""
echo "🔍 Running security audit to verify fixes..."
yarn audit --summary

echo ""
echo "📊 FINAL VULNERABILITY STATUS:"
yarn audit --level moderate --json 2>/dev/null | head -10

echo ""
echo "🔄 Restarting services to apply security updates..."