#!/usr/bin/env python3
"""
Pulse Application Monitoring Service
Independent monitoring service that runs separately from the Pulse app
"""

import time
import schedule
import os
from datetime import datetime
from independent_code_review_agent import CodeReviewAgent
import json

class PulseMonitoringService:
    def __init__(self, app_directory="/app", monitoring_interval=3600):  # 1 hour default
        self.app_directory = app_directory
        self.monitoring_interval = monitoring_interval
        self.agent = CodeReviewAgent()
        self.output_dir = "monitoring_reports"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def run_monitoring_scan(self):
        """Run a comprehensive monitoring scan"""
        print(f"\n🔍 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting monitoring scan...")
        
        # Clear previous analysis
        self.agent.issues = []
        self.agent.optimizations = []
        self.agent.security_vulnerabilities = []
        self.agent.market_analysis = []
        self.agent.monetization_suggestions = []
        
        # Run the monitoring
        report_path = self.agent.monitor_application(self.app_directory, self.output_dir)
        
        # Generate alerts for critical issues
        self._generate_alerts(report_path)
        
        print(f"✅ Monitoring scan completed. Report: {report_path}")
        
    def _generate_alerts(self, report_path):
        """Generate alerts for critical security issues"""
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        critical_vulns = [v for v in report['security_vulnerabilities'] if v['severity'] == 'critical']
        high_vulns = [v for v in report['security_vulnerabilities'] if v['severity'] == 'high']
        
        if critical_vulns:
            print(f"\n🚨 CRITICAL ALERT: {len(critical_vulns)} critical security vulnerabilities found!")
            for vuln in critical_vulns[:3]:  # Show top 3
                print(f"   • {vuln['type']} in {vuln['file']}:{vuln['line']}")
        
        if high_vulns:
            print(f"\n⚠️  HIGH PRIORITY: {len(high_vulns)} high severity vulnerabilities found!")
        
        # Alert for new features with high market demand
        high_demand_features = [f for f in report['market_analysis'] if f['market_demand'] >= 8.0]
        if high_demand_features:
            print(f"\n📈 MARKET OPPORTUNITY: {len(high_demand_features)} high-demand features identified!")
    
    def start_continuous_monitoring(self):
        """Start continuous monitoring service"""
        print("🤖 Starting Pulse Application Monitoring Service")
        print("="*60)
        print(f"📁 Monitoring Directory: {self.app_directory}")
        print(f"⏰ Monitoring Interval: {self.monitoring_interval} seconds")
        print(f"📊 Reports Directory: {self.output_dir}")
        print("="*60)
        
        # Schedule monitoring
        schedule.every(self.monitoring_interval).seconds.do(self.run_monitoring_scan)
        
        # Run initial scan
        self.run_monitoring_scan()
        
        # Keep running
        print(f"\n🔄 Monitoring service is running. Press Ctrl+C to stop.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n🛑 Monitoring service stopped.")
    
    def run_single_scan(self):
        """Run a single monitoring scan"""
        print("🔍 Running single monitoring scan...")
        self.run_monitoring_scan()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pulse Application Monitoring Service')
    parser.add_argument('--app-dir', default='/app', help='Application directory to monitor')
    parser.add_argument('--interval', type=int, default=3600, help='Monitoring interval in seconds')
    parser.add_argument('--once', action='store_true', help='Run monitoring once and exit')
    
    args = parser.parse_args()
    
    service = PulseMonitoringService(args.app_dir, args.interval)
    
    if args.once:
        service.run_single_scan()
    else:
        service.start_continuous_monitoring()

if __name__ == "__main__":
    main()