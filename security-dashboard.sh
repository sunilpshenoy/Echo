#!/bin/bash

# PULSE SECURITY DASHBOARD
# Quick overview of current security status

clear
echo "🛡️  PULSE APPLICATION SECURITY DASHBOARD"
echo "========================================"
echo "📅 $(date)"
echo ""

# Service Status
echo "🔧 SERVICE STATUS:"
echo "------------------"
if sudo supervisorctl status | grep -q "RUNNING"; then
    RUNNING_COUNT=$(sudo supervisorctl status | grep -c "RUNNING")
    echo "✅ Services Running: $RUNNING_COUNT/3"
else
    echo "🔴 Service Issues Detected"
fi

# Application Health
echo ""
echo "🌐 APPLICATION HEALTH:"
echo "----------------------"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000" --max-time 5)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "✅ Frontend: Accessible (HTTP $FRONTEND_STATUS)"
else
    echo "🔴 Frontend: Issue (HTTP $FRONTEND_STATUS)"
fi

BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/" --max-time 5)
if [ "$BACKEND_STATUS" = "200" ] || [ "$BACKEND_STATUS" = "404" ] || [ "$BACKEND_STATUS" = "405" ]; then
    echo "✅ Backend: Accessible (HTTP $BACKEND_STATUS)"
else
    echo "🔴 Backend: Issue (HTTP $BACKEND_STATUS)"
fi

# Security Status
echo ""
echo "🛡️ SECURITY STATUS:"
echo "-------------------"

cd /app/frontend 2>/dev/null || cd /app

# Get vulnerability counts
AUDIT_SUMMARY=$(yarn audit --summary 2>/dev/null | tail -5)
CRITICAL_COUNT=$(echo "$AUDIT_SUMMARY" | grep -o "Critical" | wc -l)
HIGH_COUNT=$(echo "$AUDIT_SUMMARY" | grep -o "High" | wc -l) 
MODERATE_COUNT=$(echo "$AUDIT_SUMMARY" | grep -o "Moderate" | wc -l)

echo "🔴 Critical: ${CRITICAL_COUNT:-0}"
echo "🟠 High: ${HIGH_COUNT:-0}"
echo "🟡 Moderate: ${MODERATE_COUNT:-0}"

# Security Score
SECURITY_SCORE=$((100 - ${CRITICAL_COUNT:-0} * 20 - ${HIGH_COUNT:-0} * 10 - ${MODERATE_COUNT:-0} * 2))

if [ ${SECURITY_SCORE:-0} -ge 95 ]; then
    echo "📊 Security Score: $SECURITY_SCORE/100 🟢 EXCELLENT"
elif [ ${SECURITY_SCORE:-0} -ge 80 ]; then
    echo "📊 Security Score: $SECURITY_SCORE/100 🟡 GOOD"
else
    echo "📊 Security Score: $SECURITY_SCORE/100 🔴 NEEDS ATTENTION"
fi

# Recent Alerts
echo ""
echo "🚨 RECENT ALERTS:"
echo "-----------------"
TODAY=$(date +%Y%m%d)
ALERT_FILE="/app/security-reports/alerts/alerts-$TODAY.log"

if [ -f "$ALERT_FILE" ] && [ -s "$ALERT_FILE" ]; then
    ALERT_COUNT=$(wc -l < "$ALERT_FILE")
    echo "⚠️ Today's Alerts: $ALERT_COUNT"
    echo "📋 Latest alerts:"
    tail -3 "$ALERT_FILE" 2>/dev/null | sed 's/^/   /'
else
    echo "✅ No alerts today"
fi

# System Resources
echo ""
echo "💾 SYSTEM RESOURCES:"
echo "--------------------"
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')

echo "💾 Disk Usage: ${DISK_USAGE:-0}%"
echo "🧠 Memory Usage: ${MEMORY_USAGE:-0}%"

if [ ${DISK_USAGE:-0} -gt 90 ]; then
    echo "⚠️ Disk usage critical"
elif [ ${DISK_USAGE:-0} -gt 80 ]; then
    echo "⚠️ Disk usage warning"
fi

# Quick Actions
echo ""
echo "🔧 QUICK ACTIONS:"
echo "-----------------"
echo "1. Run security scan: /app/security-risk-assessment.sh"
echo "2. View detailed logs: /app/continuous-security-monitor.sh"
echo "3. Weekly report: /app/weekly-security-report.sh"
echo "4. Emergency response: /app/security-emergency-response.sh"

echo ""
echo "📊 Dashboard updated: $(date)"
echo "🔄 Next auto-update: $(date -d '+1 hour')"

cd /app