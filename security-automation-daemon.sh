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
