#!/bin/bash
# Pulse Application Monitoring Service Startup Script

echo "🚀 Starting Pulse Application Monitoring Service..."

# Install required packages
pip install schedule > /dev/null 2>&1

# Create monitoring directory
mkdir -p /app/monitoring_reports

# Set execute permissions
chmod +x /app/pulse_monitoring_service.py
chmod +x /app/independent_code_review_agent.py

# Start the monitoring service
echo "🔍 Monitoring service starting..."
echo "📊 Reports will be saved to: /app/monitoring_reports"
echo "⏰ Monitoring interval: Every hour"
echo "🛑 Press Ctrl+C to stop the service"
echo ""

# Run the monitoring service
cd /app
python pulse_monitoring_service.py --interval 3600