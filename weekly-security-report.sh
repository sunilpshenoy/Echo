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
