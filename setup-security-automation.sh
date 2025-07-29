#!/bin/bash

# PULSE SECURITY AUTOMATION SETUP
# Sets up cron jobs and automated security monitoring

echo "🔧 SETTING UP PULSE SECURITY AUTOMATION"
echo "========================================"

# Create necessary directories
mkdir -p /app/security-reports/{daily,weekly,monthly,alerts,history}
mkdir -p /app/security-incidents
mkdir -p /app/security-backups

# Create the daily security check script
cat > /app/daily-security-check.sh << 'EOF'
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
EOF

chmod +x /app/daily-security-check.sh

# Create weekly security report
cat > /app/weekly-security-report.sh << 'EOF'
#!/bin/bash
# Weekly security summary and trend analysis

WEEK_START=$(date -d '7 days ago' +%Y%m%d)
WEEK_END=$(date +%Y%m%d)
REPORT_FILE="/app/security-reports/weekly/security-weekly-$WEEK_END.log"

echo "📊 WEEKLY SECURITY REPORT ($WEEK_START to $WEEK_END)" | tee "$REPORT_FILE"
echo "====================================================" | tee -a "$REPORT_FILE"

# Aggregate daily reports
TOTAL_ALERTS=0
CRITICAL_TOTAL=0
HIGH_TOTAL=0

for i in $(seq 0 6); do
    CHECK_DATE=$(date -d "$i days ago" +%Y%m%d)
    DAILY_ALERTS="/app/security-reports/alerts/alerts-$CHECK_DATE.log"
    
    if [ -f "$DAILY_ALERTS" ]; then
        DAILY_COUNT=$(wc -l < "$DAILY_ALERTS")
        CRITICAL_COUNT=$(grep -c "CRITICAL" "$DAILY_ALERTS" 2>/dev/null || echo "0")
        HIGH_COUNT=$(grep -c "HIGH" "$DAILY_ALERTS" 2>/dev/null || echo "0")
        
        TOTAL_ALERTS=$((TOTAL_ALERTS + DAILY_COUNT))
        CRITICAL_TOTAL=$((CRITICAL_TOTAL + CRITICAL_COUNT))
        HIGH_TOTAL=$((HIGH_TOTAL + HIGH_COUNT))
        
        echo "📅 $CHECK_DATE: $DAILY_COUNT alerts ($CRITICAL_COUNT critical, $HIGH_COUNT high)" | tee -a "$REPORT_FILE"
    fi
done

echo "" | tee -a "$REPORT_FILE"
echo "📊 WEEKLY SUMMARY:" | tee -a "$REPORT_FILE"
echo "  Total Alerts: $TOTAL_ALERTS" | tee -a "$REPORT_FILE"
echo "  Critical: $CRITICAL_TOTAL" | tee -a "$REPORT_FILE"
echo "  High: $HIGH_TOTAL" | tee -a "$REPORT_FILE"

# Security health score
HEALTH_SCORE=$((100 - CRITICAL_TOTAL * 20 - HIGH_TOTAL * 10))
if [ $HEALTH_SCORE -ge 90 ]; then
    echo "🟢 SECURITY HEALTH: EXCELLENT ($HEALTH_SCORE/100)" | tee -a "$REPORT_FILE"
elif [ $HEALTH_SCORE -ge 70 ]; then
    echo "🟡 SECURITY HEALTH: GOOD ($HEALTH_SCORE/100)" | tee -a "$REPORT_FILE"
else
    echo "🔴 SECURITY HEALTH: NEEDS ATTENTION ($HEALTH_SCORE/100)" | tee -a "$REPORT_FILE"
fi

echo "📋 Weekly report saved to: $REPORT_FILE" | tee -a "$REPORT_FILE"
EOF

chmod +x /app/weekly-security-report.sh

# Create emergency response script
cat > /app/security-emergency-response.sh << 'EOF'
#!/bin/bash
# Emergency security response for critical issues

INCIDENT_ID="PULSE-$(date +%Y%m%d-%H%M%S)"
INCIDENT_DIR="/app/security-incidents/$INCIDENT_ID"

echo "🚨 SECURITY EMERGENCY RESPONSE ACTIVATED"
echo "========================================"
echo "📋 Incident ID: $INCIDENT_ID"

mkdir -p "$INCIDENT_DIR"

# Log incident details
echo "Incident ID: $INCIDENT_ID" > "$INCIDENT_DIR/incident.log"
echo "Timestamp: $(date)" >> "$INCIDENT_DIR/incident.log"
echo "Triggered by: Critical security alert detection" >> "$INCIDENT_DIR/incident.log"

# Backup current configuration
cp /app/frontend/package.json "$INCIDENT_DIR/package.json.backup" 2>/dev/null
cp /app/backend/requirements.txt "$INCIDENT_DIR/requirements.txt.backup" 2>/dev/null

# Check service status
echo "" >> "$INCIDENT_DIR/incident.log"
echo "Service Status at time of incident:" >> "$INCIDENT_DIR/incident.log"
sudo supervisorctl status >> "$INCIDENT_DIR/incident.log" 2>&1

# System health snapshot
echo "" >> "$INCIDENT_DIR/incident.log"
echo "System Health:" >> "$INCIDENT_DIR/incident.log"
echo "Memory: $(free -h | head -2 | tail -1)" >> "$INCIDENT_DIR/incident.log"
echo "Disk: $(df -h / | tail -1)" >> "$INCIDENT_DIR/incident.log"
echo "Load: $(uptime)" >> "$INCIDENT_DIR/incident.log"

# Check for known critical vulnerabilities and attempt automatic fix
echo "🔧 Attempting automatic remediation..." >> "$INCIDENT_DIR/incident.log"

cd /app/frontend
CRITICAL_VULN=$(yarn audit --level critical --summary 2>&1)
echo "Critical vulnerabilities found:" >> "$INCIDENT_DIR/incident.log"
echo "$CRITICAL_VULN" >> "$INCIDENT_DIR/incident.log"

# In a real emergency, this might:
# 1. Take services offline temporarily
# 2. Apply emergency patches
# 3. Restore from known-good backup
# 4. Notify operations team

echo "🚨 Emergency response logged in: $INCIDENT_DIR"
echo "📞 Manual intervention may be required"
EOF

chmod +x /app/security-emergency-response.sh

# Setup automated execution (using a simple background process instead of cron)
cat > /app/security-automation-daemon.sh << 'EOF'
#!/bin/bash
# Security automation daemon - runs security checks on schedule

echo "🤖 PULSE SECURITY AUTOMATION DAEMON STARTED"
echo "============================================"
echo "📅 Started at: $(date)"
echo "🔄 Running daily security checks at 02:00 UTC"
echo "📊 Running weekly reports on Mondays"
echo ""

while true; do
    current_hour=$(date +%H)
    current_day=$(date +%u)  # 1=Monday, 7=Sunday
    
    # Daily check at 02:00 UTC
    if [ "$current_hour" = "02" ]; then
        echo "🔄 $(date): Running daily security check..."
        /app/daily-security-check.sh
        
        # Wait an hour to avoid running multiple times
        sleep 3600
    fi
    
    # Weekly report on Monday at 03:00 UTC
    if [ "$current_day" = "1" ] && [ "$current_hour" = "03" ]; then
        echo "📊 $(date): Running weekly security report..."
        /app/weekly-security-report.sh
        
        # Wait an hour to avoid running multiple times
        sleep 3600
    fi
    
    # Check every 30 minutes
    sleep 1800
done
EOF

chmod +x /app/security-automation-daemon.sh

echo "✅ Security automation setup completed!"
echo ""
echo "📋 Created Scripts:"
echo "  • /app/daily-security-check.sh - Daily automated security checks"
echo "  • /app/weekly-security-report.sh - Weekly security summaries"  
echo "  • /app/security-emergency-response.sh - Critical incident response"
echo "  • /app/security-automation-daemon.sh - Automation scheduler"
echo ""
echo "🔄 To start automated monitoring:"
echo "  nohup /app/security-automation-daemon.sh > /app/security-automation.log 2>&1 &"
echo ""
echo "📊 Reports will be saved to:"
echo "  • Daily: /app/security-reports/daily/"
echo "  • Weekly: /app/security-reports/weekly/"
echo "  • Alerts: /app/security-reports/alerts/"
echo "  • Incidents: /app/security-incidents/"