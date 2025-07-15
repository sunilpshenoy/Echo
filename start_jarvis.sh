#!/bin/bash
# JARVIS AI Assistant Startup Script

echo "🤖 Starting JARVIS - Just A Rather Very Intelligent System..."
echo "="*80

# Install required packages
pip install schedule > /dev/null 2>&1

# Create JARVIS reports directory
mkdir -p /app/jarvis_reports

# Set execute permissions
chmod +x /app/jarvis_ai.py
chmod +x /app/jarvis_monitoring_service.py

# Display JARVIS capabilities
echo "🎯 JARVIS Enhanced Capabilities:"
echo "   ⚡ Security Analysis - Comprehensive vulnerability scanning"
echo "   🎨 UI/Design Analysis - Accessibility, responsive design, UX"
echo "   📊 Market Analysis - Feature demand and ROI projections"
echo "   🔍 Code Quality - Best practices and optimizations"
echo "   📱 Performance Analysis - Frontend and backend optimization"
echo "   ♿ Accessibility Analysis - WCAG compliance checking"
echo "   🚀 Design Patterns - Architecture and pattern analysis"
echo ""

# Start JARVIS monitoring service
echo "🔍 JARVIS monitoring service starting..."
echo "📊 Enhanced reports will be saved to: /app/jarvis_reports"
echo "⏰ Monitoring interval: Every hour"
echo "🛑 Press Ctrl+C to stop JARVIS"
echo ""

# Run JARVIS monitoring service
cd /app
python jarvis_monitoring_service.py --interval 3600