#!/bin/bash
# Daily security health check - automated execution

DATE=$(date +%Y%m%d)
LOG_FILE="/app/security-reports/daily/security-daily-$DATE.log"

echo "🔄 DAILY AUTOMATED SECURITY CHECK - $(date)" | tee "$LOG_FILE"
echo "==============================================" | tee -a "$LOG_FILE"

# Run the continuous monitoring
/app/continuous-security-monitor.sh >> "$LOG_FILE" 2>&1

# Check for any critical alerts
CRITICAL_ALERTS=$(grep -c "CRITICAL" /app/security-reports/alerts/alerts-$DATE.log 2>/dev/null || echo "0")
HIGH_ALERTS=$(grep -c "HIGH" /app/security-reports/alerts/alerts-$DATE.log 2>/dev/null || echo "0")

if [ "$CRITICAL_ALERTS" -gt 0 ]; then
    echo "🚨 CRITICAL ALERTS DETECTED: $CRITICAL_ALERTS" | tee -a "$LOG_FILE"
    # In production, this would trigger immediate notifications
    /app/security-emergency-response.sh
elif [ "$HIGH_ALERTS" -gt 0 ]; then
    echo "⚠️ HIGH Priority alerts: $HIGH_ALERTS" | tee -a "$LOG_FILE"
    # Schedule for immediate review
fi

echo "✅ Daily security check completed: $(date)" | tee -a "$LOG_FILE"
