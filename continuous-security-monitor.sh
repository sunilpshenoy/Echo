#!/bin/bash

# PULSE APP - CONTINUOUS SECURITY MONITORING
# Daily automated security health checks with intelligent alerting

echo "🔄 PULSE CONTINUOUS SECURITY MONITOR"
echo "===================================="
echo "📅 $(date)"
echo ""

# Create monitoring directories
mkdir -p /app/security-reports/daily
mkdir -p /app/security-reports/alerts
mkdir -p /app/security-reports/history

LOG_FILE="/app/security-reports/daily/security-monitor-$(date +%Y%m%d).log"
ALERT_FILE="/app/security-reports/alerts/alerts-$(date +%Y%m%d).log"

echo "🔍 DAILY SECURITY HEALTH CHECK" | tee -a "$LOG_FILE"
echo "==============================" | tee -a "$LOG_FILE"

# Function to send alert
send_alert() {
    local severity=$1
    local message=$2
    local timestamp=$(date)
    
    echo "[$timestamp] $severity: $message" | tee -a "$ALERT_FILE"
    
    # In production, this would integrate with Slack, email, etc.
    case $severity in
        "CRITICAL")
            echo "🚨 CRITICAL ALERT: $message" >&2
            ;;
        "HIGH")
            echo "⚠️ HIGH ALERT: $message" >&2
            ;;
        "MEDIUM")
            echo "🟡 MEDIUM ALERT: $message" >&2
            ;;
        *)
            echo "ℹ️ INFO: $message"
            ;;
    esac
}

# Check service health
echo "" | tee -a "$LOG_FILE"
echo "🔧 SERVICE HEALTH CHECK:" | tee -a "$LOG_FILE"
echo "------------------------" | tee -a "$LOG_FILE"

# Check if services are running
SERVICES=("backend" "frontend" "mongodb")
for service in "${SERVICES[@]}"; do
    if sudo supervisorctl status $service | grep -q "RUNNING"; then
        echo "✅ $service: RUNNING" | tee -a "$LOG_FILE"
    else
        send_alert "CRITICAL" "$service service is not running"
        echo "🔴 $service: NOT RUNNING" | tee -a "$LOG_FILE"
    fi
done

# Check application accessibility
echo "" | tee -a "$LOG_FILE"
echo "🌐 APPLICATION ACCESSIBILITY:" | tee -a "$LOG_FILE"
echo "-----------------------------" | tee -a "$LOG_FILE"

# Test frontend
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000" --max-time 10)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "✅ Frontend accessible (HTTP $FRONTEND_STATUS)" | tee -a "$LOG_FILE"
else
    send_alert "HIGH" "Frontend not accessible (HTTP $FRONTEND_STATUS)"
    echo "🔴 Frontend not accessible (HTTP $FRONTEND_STATUS)" | tee -a "$LOG_FILE"
fi

# Test backend API
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/api/health" --max-time 10 2>/dev/null || echo "000")
if [ "$BACKEND_STATUS" = "200" ]; then
    echo "✅ Backend API accessible (HTTP $BACKEND_STATUS)" | tee -a "$LOG_FILE"
elif [ "$BACKEND_STATUS" = "405" ]; then
    echo "✅ Backend API accessible (HTTP $BACKEND_STATUS - Method not allowed is expected)" | tee -a "$LOG_FILE"
else
    # Try a different endpoint
    BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/" --max-time 10 2>/dev/null || echo "000")
    if [ "$BACKEND_STATUS" = "200" ] || [ "$BACKEND_STATUS" = "404" ]; then
        echo "✅ Backend service accessible (HTTP $BACKEND_STATUS)" | tee -a "$LOG_FILE"
    else
        send_alert "HIGH" "Backend API not accessible (HTTP $BACKEND_STATUS)"
        echo "🔴 Backend API not accessible (HTTP $BACKEND_STATUS)" | tee -a "$LOG_FILE"
    fi
fi

# Security vulnerability monitoring
echo "" | tee -a "$LOG_FILE"
echo "🛡️ VULNERABILITY MONITORING:" | tee -a "$LOG_FILE"
echo "----------------------------" | tee -a "$LOG_FILE"

cd /app/frontend

# Get current vulnerability counts
CURRENT_AUDIT=$(yarn audit --summary 2>&1)
CRITICAL_NOW=$(echo "$CURRENT_AUDIT" | grep -o "Critical" | wc -l)
HIGH_NOW=$(echo "$CURRENT_AUDIT" | grep -o "High" | wc -l)
MODERATE_NOW=$(echo "$CURRENT_AUDIT" | grep -o "Moderate" | wc -l)

# Compare with yesterday's report if available
YESTERDAY_FILE="/app/security-reports/daily/security-monitor-$(date -d '1 day ago' +%Y%m%d).log"
if [ -f "$YESTERDAY_FILE" ]; then
    CRITICAL_YESTERDAY=$(grep "CRITICAL:" "$YESTERDAY_FILE" | tail -1 | grep -o "[0-9]*" | head -1 || echo "0")
    HIGH_YESTERDAY=$(grep "HIGH:" "$YESTERDAY_FILE" | tail -1 | grep -o "[0-9]*" | head -1 || echo "0")
    MODERATE_YESTERDAY=$(grep "MODERATE:" "$YESTERDAY_FILE" | tail -1 | grep -o "[0-9]*" | head -1 || echo "0")
    
    # Alert on any increase in critical or high vulnerabilities
    if [ ${CRITICAL_NOW:-0} -gt ${CRITICAL_YESTERDAY:-0} ]; then
        send_alert "CRITICAL" "Critical vulnerabilities increased from $CRITICAL_YESTERDAY to $CRITICAL_NOW"
    fi
    
    if [ ${HIGH_NOW:-0} -gt ${HIGH_YESTERDAY:-0} ]; then
        send_alert "HIGH" "High vulnerabilities increased from $HIGH_YESTERDAY to $HIGH_NOW"
    fi
    
    if [ ${MODERATE_NOW:-0} -gt ${MODERATE_YESTERDAY:-0} ]; then
        send_alert "MEDIUM" "Moderate vulnerabilities increased from $MODERATE_YESTERDAY to $MODERATE_NOW"
    fi
fi

echo "📊 Current vulnerability status:" | tee -a "$LOG_FILE"
echo "   CRITICAL: ${CRITICAL_NOW:-0}" | tee -a "$LOG_FILE"
echo "   HIGH: ${HIGH_NOW:-0}" | tee -a "$LOG_FILE"
echo "   MODERATE: ${MODERATE_NOW:-0}" | tee -a "$LOG_FILE"

# Performance monitoring
echo "" | tee -a "$LOG_FILE"
echo "⚡ PERFORMANCE MONITORING:" | tee -a "$LOG_FILE"
echo "-------------------------" | tee -a "$LOG_FILE"

# Test response times
FRONTEND_TIME=$(curl -o /dev/null -s -w '%{time_total}' "http://localhost:3000" --max-time 10 2>/dev/null || echo "timeout")
if [ "$FRONTEND_TIME" != "timeout" ]; then
    FRONTEND_MS=$(echo "$FRONTEND_TIME * 1000" | bc 2>/dev/null || echo "unknown")
    echo "✅ Frontend response time: ${FRONTEND_MS}ms" | tee -a "$LOG_FILE"
    
    # Alert if response time is too slow
    if (( $(echo "$FRONTEND_TIME > 3.0" | bc -l 2>/dev/null || echo 0) )); then
        send_alert "MEDIUM" "Frontend response time slow: ${FRONTEND_MS}ms"
    fi
else
    send_alert "HIGH" "Frontend response timeout"
    echo "🔴 Frontend response timeout" | tee -a "$LOG_FILE"
fi

# Check disk space
echo "" | tee -a "$LOG_FILE"
echo "💾 SYSTEM HEALTH:" | tee -a "$LOG_FILE"
echo "-----------------" | tee -a "$LOG_FILE"

DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
echo "💾 Disk usage: $DISK_USAGE%" | tee -a "$LOG_FILE"

if [ ${DISK_USAGE:-0} -gt 90 ]; then
    send_alert "HIGH" "Disk usage critical: $DISK_USAGE%"
elif [ ${DISK_USAGE:-0} -gt 80 ]; then
    send_alert "MEDIUM" "Disk usage warning: $DISK_USAGE%"
fi

# Memory usage
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
echo "🧠 Memory usage: $MEMORY_USAGE%" | tee -a "$LOG_FILE"

# Generate daily summary
echo "" | tee -a "$LOG_FILE"
echo "📋 DAILY SECURITY SUMMARY:" | tee -a "$LOG_FILE"
echo "===========================" | tee -a "$LOG_FILE"

ALERT_COUNT=$(wc -l < "$ALERT_FILE" 2>/dev/null || echo "0")
if [ ${ALERT_COUNT:-0} -eq 0 ]; then
    echo "🟢 SECURITY STATUS: EXCELLENT" | tee -a "$LOG_FILE"
    echo "   ✅ No security alerts today" | tee -a "$LOG_FILE"
    echo "   ✅ All services operational" | tee -a "$LOG_FILE"
    echo "   ✅ Performance within acceptable limits" | tee -a "$LOG_FILE"
elif [ ${ALERT_COUNT:-0} -lt 3 ]; then
    echo "🟡 SECURITY STATUS: GOOD" | tee -a "$LOG_FILE"
    echo "   ⚠️ $ALERT_COUNT minor alerts generated" | tee -a "$LOG_FILE"
else
    echo "🟠 SECURITY STATUS: ATTENTION NEEDED" | tee -a "$LOG_FILE"
    echo "   🚨 $ALERT_COUNT alerts generated today" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "📊 Report saved to: $LOG_FILE" | tee -a "$LOG_FILE"
echo "🚨 Alerts logged to: $ALERT_FILE" | tee -a "$LOG_FILE"
echo "🔄 Next check: $(date -d '+1 day')" | tee -a "$LOG_FILE"

cd /app