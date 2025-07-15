#!/usr/bin/env python3
"""
JARVIS Monitoring Service
Enhanced AI monitoring service for Pulse Application
"""

import time
import schedule
import os
from datetime import datetime
from jarvis_ai import JarvisAI
import json

class JarvisMonitoringService:
    def __init__(self, app_directory="/app", monitoring_interval=3600):  # 1 hour default
        self.app_directory = app_directory
        self.monitoring_interval = monitoring_interval
        self.jarvis = JarvisAI()
        self.output_dir = "jarvis_reports"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def run_monitoring_scan(self):
        """Run a comprehensive JARVIS monitoring scan"""
        print(f"\n🤖 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] JARVIS starting comprehensive analysis...")
        
        # Clear previous analysis
        self.jarvis.issues = []
        self.jarvis.optimizations = []
        self.jarvis.security_vulnerabilities = []
        self.jarvis.ui_design_issues = []
        self.jarvis.design_patterns = []
        self.jarvis.market_analysis = []
        self.jarvis.monetization_suggestions = []
        
        # Run the monitoring
        report_path = self.jarvis.monitor_application(self.app_directory, self.output_dir)
        
        # Generate enhanced alerts
        self._generate_enhanced_alerts(report_path)
        
        print(f"✅ JARVIS analysis completed. Report: {report_path}")
        
    def _generate_enhanced_alerts(self, report_path):
        """Generate enhanced alerts for critical issues"""
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Security alerts
        critical_vulns = [v for v in report['security_vulnerabilities'] if v['severity'] == 'critical']
        high_vulns = [v for v in report['security_vulnerabilities'] if v['severity'] == 'high']
        
        if critical_vulns:
            print(f"\n🚨 CRITICAL SECURITY ALERT: {len(critical_vulns)} critical vulnerabilities!")
            for vuln in critical_vulns[:3]:
                print(f"   • {vuln['type']} in {vuln['file']}:{vuln['line']}")
        
        if high_vulns:
            print(f"\n⚠️  HIGH SECURITY ALERT: {len(high_vulns)} high severity vulnerabilities!")
        
        # UI/Design alerts
        critical_ui = [ui for ui in report['ui_design_issues'] if ui['severity'] == 'critical']
        high_ui = [ui for ui in report['ui_design_issues'] if ui['severity'] == 'high']
        
        if critical_ui:
            print(f"\n🎨 CRITICAL UI/DESIGN ALERT: {len(critical_ui)} critical UI issues!")
            for ui in critical_ui[:3]:
                print(f"   • {ui['type']} in {ui['file']}:{ui['line']} ({ui['category']})")
        
        if high_ui:
            print(f"\n🎨 HIGH UI/DESIGN ALERT: {len(high_ui)} high priority UI issues!")
        
        # Accessibility alerts
        accessibility_issues = [ui for ui in report['ui_design_issues'] if ui['category'] == 'accessibility']
        if accessibility_issues:
            print(f"\n♿ ACCESSIBILITY ALERT: {len(accessibility_issues)} accessibility issues found!")
            for issue in accessibility_issues[:3]:
                print(f"   • {issue['type']}: {issue['description']}")
        
        # Performance alerts
        performance_issues = [ui for ui in report['ui_design_issues'] if ui['category'] == 'performance']
        if performance_issues:
            print(f"\n⚡ PERFORMANCE ALERT: {len(performance_issues)} performance issues found!")
            for issue in performance_issues[:3]:
                print(f"   • {issue['type']}: {issue['description']}")
        
        # Market opportunity alerts
        high_demand_features = [f for f in report['market_analysis'] if f['market_demand'] >= 8.0]
        if high_demand_features:
            print(f"\n📈 MARKET OPPORTUNITY ALERT: {len(high_demand_features)} high-demand features!")
            for feature in high_demand_features[:3]:
                print(f"   • {feature['feature']}: {feature['market_demand']}/10 demand")
        
        # Design pattern alerts
        poor_patterns = [p for p in report['design_patterns'] if p['quality'] in ['poor', 'fair']]
        if poor_patterns:
            print(f"\n🔧 DESIGN PATTERN ALERT: {len(poor_patterns)} patterns need improvement!")
            for pattern in poor_patterns[:3]:
                print(f"   • {pattern['pattern']} in {pattern['file']}: {pattern['quality']}")
    
    def start_continuous_monitoring(self):
        """Start continuous JARVIS monitoring service"""
        print("🤖 Starting JARVIS AI Monitoring Service")
        print("="*80)
        print(f"📁 Monitoring Directory: {self.app_directory}")
        print(f"⏰ Monitoring Interval: {self.monitoring_interval} seconds")
        print(f"📊 Reports Directory: {self.output_dir}")
        print("🎯 Enhanced Analysis: Security, UI/Design, Market, Code Quality")
        print("="*80)
        
        # Schedule monitoring
        schedule.every(self.monitoring_interval).seconds.do(self.run_monitoring_scan)
        
        # Run initial scan
        self.run_monitoring_scan()
        
        # Keep running
        print(f"\n🔄 JARVIS monitoring service is running. Press Ctrl+C to stop.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n🛑 JARVIS monitoring service stopped.")
    
    def run_single_scan(self):
        """Run a single JARVIS monitoring scan"""
        print("🤖 Running single JARVIS analysis...")
        self.run_monitoring_scan()
    
    def get_latest_report(self):
        """Get the latest JARVIS report"""
        report_files = [f for f in os.listdir(self.output_dir) if f.startswith('jarvis_analysis_report_')]
        if not report_files:
            return None
        
        latest_report = max(report_files, key=lambda f: os.path.getctime(os.path.join(self.output_dir, f)))
        report_path = os.path.join(self.output_dir, latest_report)
        
        with open(report_path, 'r') as f:
            return json.load(f)
    
    def get_summary_stats(self):
        """Get summary statistics from latest report"""
        report = self.get_latest_report()
        if not report:
            return None
        
        return {
            'scan_time': report['scan_timestamp'],
            'security_score': self._calculate_security_score(report),
            'ui_design_score': self._calculate_ui_design_score(report),
            'code_quality_score': self._calculate_code_quality_score(report),
            'market_potential_score': self._calculate_market_potential_score(report),
            'overall_score': self._calculate_overall_score(report)
        }
    
    def _calculate_security_score(self, report):
        """Calculate security score out of 100"""
        total_vulns = report['summary']['total_vulnerabilities']
        if total_vulns == 0:
            return 100
        
        critical_vulns = report['summary']['vulnerabilities_by_severity'].get('critical', 0)
        high_vulns = report['summary']['vulnerabilities_by_severity'].get('high', 0)
        medium_vulns = report['summary']['vulnerabilities_by_severity'].get('medium', 0)
        
        # Weight vulnerabilities by severity
        weighted_score = (critical_vulns * 4) + (high_vulns * 2) + (medium_vulns * 1)
        
        # Calculate score (inverse relationship)
        score = max(0, 100 - (weighted_score * 5))
        return round(score, 1)
    
    def _calculate_ui_design_score(self, report):
        """Calculate UI/Design score out of 100"""
        total_issues = report['summary']['total_ui_design_issues']
        if total_issues == 0:
            return 100
        
        # Weight by category importance
        accessibility_issues = report['summary']['ui_issues_by_category'].get('accessibility', 0)
        performance_issues = report['summary']['ui_issues_by_category'].get('performance', 0)
        responsive_issues = report['summary']['ui_issues_by_category'].get('responsive_design', 0)
        ux_issues = report['summary']['ui_issues_by_category'].get('user_experience', 0)
        consistency_issues = report['summary']['ui_issues_by_category'].get('consistency', 0)
        
        weighted_score = (accessibility_issues * 3) + (performance_issues * 2) + (responsive_issues * 2) + (ux_issues * 1.5) + (consistency_issues * 1)
        
        score = max(0, 100 - (weighted_score * 2))
        return round(score, 1)
    
    def _calculate_code_quality_score(self, report):
        """Calculate code quality score out of 100"""
        total_issues = report['summary']['total_issues']
        if total_issues == 0:
            return 100
        
        # Simple inverse relationship
        score = max(0, 100 - (total_issues * 0.5))
        return round(score, 1)
    
    def _calculate_market_potential_score(self, report):
        """Calculate market potential score out of 100"""
        if not report['market_analysis']:
            return 50  # Neutral score
        
        total_demand = sum(analysis['market_demand'] for analysis in report['market_analysis'])
        avg_demand = total_demand / len(report['market_analysis'])
        
        score = (avg_demand / 10) * 100
        return round(score, 1)
    
    def _calculate_overall_score(self, report):
        """Calculate overall application score out of 100"""
        security_score = self._calculate_security_score(report)
        ui_design_score = self._calculate_ui_design_score(report)
        code_quality_score = self._calculate_code_quality_score(report)
        market_potential_score = self._calculate_market_potential_score(report)
        
        # Weighted average
        overall_score = (
            (security_score * 0.3) +
            (ui_design_score * 0.25) +
            (code_quality_score * 0.25) +
            (market_potential_score * 0.2)
        )
        
        return round(overall_score, 1)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='JARVIS AI Monitoring Service')
    parser.add_argument('--app-dir', default='/app', help='Application directory to monitor')
    parser.add_argument('--interval', type=int, default=3600, help='Monitoring interval in seconds')
    parser.add_argument('--once', action='store_true', help='Run monitoring once and exit')
    parser.add_argument('--stats', action='store_true', help='Show summary statistics')
    
    args = parser.parse_args()
    
    service = JarvisMonitoringService(args.app_dir, args.interval)
    
    if args.stats:
        stats = service.get_summary_stats()
        if stats:
            print("🤖 JARVIS Application Health Summary")
            print("="*50)
            print(f"📅 Last Scan: {stats['scan_time']}")
            print(f"🛡️  Security Score: {stats['security_score']}/100")
            print(f"🎨 UI/Design Score: {stats['ui_design_score']}/100")
            print(f"🔍 Code Quality Score: {stats['code_quality_score']}/100")
            print(f"📈 Market Potential Score: {stats['market_potential_score']}/100")
            print(f"⭐ Overall Score: {stats['overall_score']}/100")
        else:
            print("No reports found. Run analysis first.")
    elif args.once:
        service.run_single_scan()
    else:
        service.start_continuous_monitoring()

if __name__ == "__main__":
    main()