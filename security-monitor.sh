#!/bin/bash

# Automated Security Monitoring Script for Pulse App
# Run this daily to monitor for new vulnerabilities

echo "🛡️  PULSE APP - DAILY SECURITY MONITOR"
echo "====================================="
echo "📅 $(date)"
echo ""

cd /app/frontend

echo "🔍 Current Security Status:"
AUDIT_RESULT=$(yarn audit --summary 2>/dev/null)
echo "$AUDIT_RESULT"

# Extract vulnerability counts
CRITICAL=$(echo "$AUDIT_RESULT" | grep -o "Critical" | wc -l)
HIGH=$(echo "$AUDIT_RESULT" | grep -o "High" | wc -l)

echo ""
if [ "$CRITICAL" -gt 0 ] || [ "$HIGH" -gt 0 ]; then
    echo "🚨 SECURITY ALERT: Critical or High vulnerabilities detected!"
    echo "📧 ACTION REQUIRED: Update dependencies immediately"
    
    # List specific critical vulnerabilities
    echo ""
    echo "📋 Critical & High Vulnerabilities:"
    yarn audit --level high --json 2>/dev/null | head -20
    
    exit 1
else
    echo "✅ No critical or high vulnerabilities detected"
    echo "💚 Security status: GOOD"
fi

echo ""
echo "📊 Full audit report saved to: security-audit-$(date +%Y%m%d).log"
yarn audit > "security-audit-$(date +%Y%m%d).log" 2>&1

echo ""
echo "🔄 Next scheduled check: $(date -d '+1 day')"