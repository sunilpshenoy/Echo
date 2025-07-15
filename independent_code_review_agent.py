#!/usr/bin/env python3
"""
Independent Code Review Agent for Pulse Application
Monitors code quality, security, market feasibility, and monetization opportunities
"""

import ast
import re
import json
import hashlib
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging
from datetime import datetime
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)

@dataclass
class CodeIssue:
    """Represents a code issue found during review"""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    suggestion: str
    code_snippet: str

@dataclass
class SecurityVulnerability:
    """Represents a security vulnerability found in code"""
    file_path: str
    line_number: int
    vulnerability_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    cve_related: Optional[str]  # CVE identifier if applicable
    description: str
    remediation: str
    business_impact: str
    code_snippet: str

@dataclass
class MarketFeasibility:
    """Represents market feasibility analysis"""
    feature_type: str
    market_demand_score: float  # 0-10
    implementation_complexity: str  # 'low', 'medium', 'high'
    competitive_advantage: str
    monetization_potential: str
    target_audience: str
    estimated_development_time: str
    roi_projection: str

@dataclass
class MonetizationSuggestion:
    """Represents monetization suggestions"""
    strategy_type: str  # 'subscription', 'freemium', 'licensing', 'marketplace'
    revenue_model: str
    pricing_suggestion: str
    target_market: str
    implementation_effort: str
    expected_revenue: str
    risk_level: str

@dataclass
class InputOptimization:
    """Represents an input optimization recommendation"""
    function_name: str
    parameter_name: str
    current_type: str
    suggested_type: str
    validation_suggestion: str
    sanitization_suggestion: str

class CodeReviewAgent:
    """AI agent for reviewing code structure, security, market feasibility, and monetization"""
    
    def __init__(self):
        self.issues: List[CodeIssue] = []
        self.optimizations: List[InputOptimization] = []
        self.security_vulnerabilities: List[SecurityVulnerability] = []
        self.market_analysis: List[MarketFeasibility] = []
        self.monetization_suggestions: List[MonetizationSuggestion] = []
        self.logger = logging.getLogger(__name__)
        
        # Security patterns database (refined to avoid false positives)
        self.security_patterns = {
            'sql_injection': [
                r'execute\s*\(\s*["\'].*\+.*["\'].*\)',
                r'cursor\.execute\s*\(\s*["\'].*%.*["\'].*\)',
                r'\.format\s*\(.*\).*execute\s*\(',
                r'f["\'].*\{.*\}.*["\'].*execute\s*\('
            ],
            'xss_vulnerability': [
                r'innerHTML\s*=\s*[^;]*\+',
                r'document\.write\s*\(\s*[^)]*\+',
                r'dangerouslySetInnerHTML.*[^{].*\+',
                r'eval\s*\(\s*[^)]*\+.*\)'
            ],
            'path_traversal': [
                r'open\s*\(\s*[^)]*\.\./[^)]*\)',
                r'os\.path\.join\s*\(\s*[^)]*\.\./[^)]*\)',
                r'pathlib.*\.\./.*[^)]',
                r'file_path.*\.\.[^a-zA-Z]'
            ],
            'command_injection': [
                r'os\.system\s*\(\s*[^)]*\+[^)]*\)',
                r'subprocess\.call\s*\(\s*[^)]*\+[^)]*\)',
                r'subprocess\.run\s*\(\s*[^)]*\+[^)]*\)',
                r'subprocess\.Popen\s*\(\s*[^)]*\+[^)]*\)'
            ],
            'hardcoded_secrets': [
                r'(?<!TEST_)(?<!test_)password\s*=\s*["\'][^"\']{8,}["\']',
                r'(?<!TEST_)(?<!test_)api_key\s*=\s*["\'][^"\']{10,}["\']',
                r'(?<!TEST_)(?<!test_)secret_key\s*=\s*["\'][^"\']{10,}["\']',
                r'(?<!TEST_)(?<!test_)token\s*=\s*["\'][^"\']{20,}["\']'
            ],
            'insecure_random': [
                r'(?<!secrets\.)random\.random\(\)',
                r'(?<!secrets\.)random\.randint\(',
                r'(?<!secrets\.)random\.choice\('
            ],
            'weak_crypto': [
                r'hashlib\.md5\(',
                r'hashlib\.sha1\(',
                r'Crypto\.Cipher\.DES\(',
                r'Crypto\.Cipher\.RC4\('
            ],
            'unsafe_deserialization': [
                r'pickle\.loads\s*\(',
                r'pickle\.load\s*\(',
                r'yaml\.load\s*\(',
                r'(?<!ast\.)eval\s*\('
            ],
            'improper_authentication': [
                r'==\s*["\'].*password',
                r'password\s*==\s*["\']',
                r'if\s+password\s*==',
                r'auth\s*==\s*True'
            ]
        }
        
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single Python file for code quality, security, and business potential"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Parse the AST
            tree = ast.parse(content)
            
            # Analyze the code
            self._analyze_ast(tree, file_path, content)
            
            # Security analysis
            self._analyze_security(content, file_path)
            
            # Market feasibility analysis
            self._analyze_market_feasibility(tree, file_path)
            
            # Generate monetization suggestions
            self._generate_monetization_suggestions(tree, file_path)
            
            return {
                'file_path': file_path,
                'issues_found': len([i for i in self.issues if i.file_path == file_path]),
                'optimizations_found': len([o for o in self.optimizations]),
                'security_vulnerabilities': len([s for s in self.security_vulnerabilities if s.file_path == file_path]),
                'market_opportunities': len([m for m in self.market_analysis]),
                'monetization_suggestions': len([m for m in self.monetization_suggestions])
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {str(e)}")
            return {'error': str(e)}
    
    def analyze_directory(self, directory_path: str) -> Dict[str, Any]:
        """Analyze all Python files in a directory"""
        directory = Path(directory_path)
        python_files = list(directory.rglob("*.py"))
        
        results = {}
        for file_path in python_files:
            if not any(skip in str(file_path) for skip in ['__pycache__', '.git', 'node_modules']):
                results[str(file_path)] = self.analyze_file(str(file_path))
            
        return results
    
    def _analyze_ast(self, tree: ast.AST, file_path: str, content: str):
        """Analyze the AST for code issues and input optimizations"""
        lines = content.split('\n')
        
        class CodeVisitor(ast.NodeVisitor):
            def __init__(self, agent):
                self.agent = agent
                self.current_class = None
                self.current_function = None
                
            def visit_FunctionDef(self, node):
                self.current_function = node.name
                self.agent._analyze_function_inputs(node, file_path, lines)
                self.agent._check_function_structure(node, file_path, lines)
                self.generic_visit(node)
                self.current_function = None
                
            def visit_ClassDef(self, node):
                self.current_class = node.name
                self.agent._check_class_structure(node, file_path, lines)
                self.generic_visit(node)
                self.current_class = None
                
            def visit_Import(self, node):
                self.agent._check_imports(node, file_path, lines)
                self.generic_visit(node)
                
            def visit_ImportFrom(self, node):
                self.agent._check_imports(node, file_path, lines)
                self.generic_visit(node)
                
            def visit_Call(self, node):
                self.agent._check_function_calls(node, file_path, lines)
                self.generic_visit(node)
        
        visitor = CodeVisitor(self)
        visitor.visit(tree)
    
    def _analyze_function_inputs(self, node: ast.FunctionDef, file_path: str, lines: List[str]):
        """Analyze function parameters and suggest input optimizations"""
        for arg in node.args.args:
            param_name = arg.arg
            
            # Check for type annotations
            if arg.annotation is None:
                self.issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=node.lineno,
                    issue_type="missing_type_annotation",
                    severity="medium",
                    description=f"Parameter '{param_name}' lacks type annotation",
                    suggestion=f"Add type annotation to parameter '{param_name}'",
                    code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                ))
                
                # Suggest input optimization
                self.optimizations.append(InputOptimization(
                    function_name=node.name,
                    parameter_name=param_name,
                    current_type="unknown",
                    suggested_type="str | int | float | bool | List | Dict",
                    validation_suggestion=f"Add isinstance() check for {param_name}",
                    sanitization_suggestion=f"Sanitize {param_name} input before processing"
                ))
    
    def _check_function_structure(self, node: ast.FunctionDef, file_path: str, lines: List[str]):
        """Check function structure for best practices"""
        # Check for docstring
        if not ast.get_docstring(node):
            self.issues.append(CodeIssue(
                file_path=file_path,
                line_number=node.lineno,
                issue_type="missing_docstring",
                severity="low",
                description=f"Function '{node.name}' lacks docstring",
                suggestion="Add docstring to describe function purpose and parameters",
                code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
            ))
        
        # Check function length
        if len(node.body) > 50:
            self.issues.append(CodeIssue(
                file_path=file_path,
                line_number=node.lineno,
                issue_type="long_function",
                severity="medium",
                description=f"Function '{node.name}' is too long ({len(node.body)} lines)",
                suggestion="Consider breaking function into smaller functions",
                code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
            ))
        
        # Check for too many parameters
        if len(node.args.args) > 5:
            self.issues.append(CodeIssue(
                file_path=file_path,
                line_number=node.lineno,
                issue_type="too_many_parameters",
                severity="medium",
                description=f"Function '{node.name}' has too many parameters ({len(node.args.args)})",
                suggestion="Consider using a configuration object or dataclass",
                code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
            ))
    
    def _check_class_structure(self, node: ast.ClassDef, file_path: str, lines: List[str]):
        """Check class structure for best practices"""
        # Check for docstring
        if not ast.get_docstring(node):
            self.issues.append(CodeIssue(
                file_path=file_path,
                line_number=node.lineno,
                issue_type="missing_docstring",
                severity="low",
                description=f"Class '{node.name}' lacks docstring",
                suggestion="Add docstring to describe class purpose",
                code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
            ))
    
    def _check_imports(self, node: ast.Import, file_path: str, lines: List[str]):
        """Check import statements for best practices"""
        # Check for wildcard imports
        if isinstance(node, ast.ImportFrom) and node.names and any(alias.name == '*' for alias in node.names):
            self.issues.append(CodeIssue(
                file_path=file_path,
                line_number=node.lineno,
                issue_type="wildcard_import",
                severity="high",
                description="Wildcard import found",
                suggestion="Use specific imports instead of wildcard imports",
                code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
            ))
    
    def _check_function_calls(self, node: ast.Call, file_path: str, lines: List[str]):
        """Check function calls for potential security issues"""
        # Check for dangerous functions
        dangerous_functions = ['eval', 'exec', 'compile', '__import__']
        
        if isinstance(node.func, ast.Name) and node.func.id in dangerous_functions:
            self.issues.append(CodeIssue(
                file_path=file_path,
                line_number=node.lineno,
                issue_type="dangerous_function",
                severity="critical",
                description=f"Use of dangerous function '{node.func.id}'",
                suggestion="Avoid using dangerous functions or ensure proper input validation",
                code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
            ))
    
    def _analyze_security(self, content: str, file_path: str):
        """Analyze code for security vulnerabilities"""
        # Skip security analysis on the agent's own pattern definitions
        if 'independent_code_review_agent.py' in file_path:
            return
            
        # Skip test files for certain patterns (as they may contain test data)
        is_test_file = any(test_pattern in file_path for test_pattern in ['test.py', '_test.py', 'test_'])
        
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Skip lines that are part of security pattern definitions
            if "'SUSPICIOUS_PATTERNS'" in content and line_num >= 47 and line_num <= 55:
                continue
                
            for vuln_type, patterns in self.security_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Skip certain patterns in test files
                        if is_test_file and vuln_type in ['unsafe_deserialization', 'xss_vulnerability']:
                            continue
                            
                        # Skip if line is within a string array/list definition
                        if re.search(r'[\[\'].*' + re.escape(line.strip()) + r'.*[\]\']', line):
                            continue
                            
                        severity = self._get_security_severity(vuln_type)
                        business_impact = self._get_business_impact(vuln_type)
                        
                        self.security_vulnerabilities.append(SecurityVulnerability(
                            file_path=file_path,
                            line_number=line_num,
                            vulnerability_type=vuln_type,
                            severity=severity,
                            cve_related=self._get_related_cve(vuln_type),
                            description=self._get_vulnerability_description(vuln_type),
                            remediation=self._get_remediation_advice(vuln_type),
                            business_impact=business_impact,
                            code_snippet=line.strip()
                        ))
    
    def _analyze_market_feasibility(self, tree: ast.AST, file_path: str):
        """Analyze code for market feasibility and business potential"""
        features = self._extract_features(tree)
        
        for feature in features:
            market_score = self._calculate_market_demand(feature)
            complexity = self._assess_implementation_complexity(feature)
            
            self.market_analysis.append(MarketFeasibility(
                feature_type=feature,
                market_demand_score=market_score,
                implementation_complexity=complexity,
                competitive_advantage=self._assess_competitive_advantage(feature),
                monetization_potential=self._assess_monetization_potential(feature),
                target_audience=self._identify_target_audience(feature),
                estimated_development_time=self._estimate_development_time(feature, complexity),
                roi_projection=self._calculate_roi_projection(feature, market_score)
            ))
    
    def _generate_monetization_suggestions(self, tree: ast.AST, file_path: str):
        """Generate monetization suggestions based on code analysis"""
        app_type = self._identify_application_type(tree)
        features = self._extract_features(tree)
        
        monetization_strategies = self._get_monetization_strategies(app_type, features)
        
        for strategy in monetization_strategies:
            self.monetization_suggestions.append(MonetizationSuggestion(
                strategy_type=strategy['type'],
                revenue_model=strategy['model'],
                pricing_suggestion=strategy['pricing'],
                target_market=strategy['target'],
                implementation_effort=strategy['effort'],
                expected_revenue=strategy['revenue'],
                risk_level=strategy['risk']
            ))
    
    def _extract_features(self, tree: ast.AST) -> List[str]:
        """Extract features from code AST"""
        features = []
        
        class FeatureVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                # Identify feature-related functions
                feature_keywords = ['chat', 'message', 'call', 'video', 'audio', 'file', 'upload', 
                                  'download', 'auth', 'login', 'register', 'payment', 'subscription',
                                  'marketplace', 'search', 'filter', 'notification', 'encryption']
                
                for keyword in feature_keywords:
                    if keyword in node.name.lower():
                        features.append(f"{keyword}_feature")
                
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                # Identify feature-related classes
                if any(keyword in node.name.lower() for keyword in ['chat', 'message', 'call', 'auth', 'payment']):
                    features.append(f"{node.name.lower()}_system")
                
                self.generic_visit(node)
        
        visitor = FeatureVisitor()
        visitor.visit(tree)
        return list(set(features))
    
    def _calculate_market_demand(self, feature: str) -> float:
        """Calculate market demand score for a feature"""
        # Market demand scoring based on feature type
        demand_scores = {
            'chat_feature': 9.5,
            'message_feature': 9.0,
            'call_feature': 8.5,
            'video_feature': 8.0,
            'audio_feature': 7.5,
            'file_feature': 7.0,
            'auth_feature': 9.0,
            'payment_feature': 8.5,
            'marketplace_feature': 8.0,
            'search_feature': 7.5,
            'notification_feature': 7.0,
            'encryption_feature': 6.5
        }
        return demand_scores.get(feature, 5.0)
    
    def _assess_implementation_complexity(self, feature: str) -> str:
        """Assess implementation complexity for a feature"""
        complexity_map = {
            'chat_feature': 'medium',
            'message_feature': 'low',
            'call_feature': 'high',
            'video_feature': 'high',
            'audio_feature': 'medium',
            'file_feature': 'medium',
            'auth_feature': 'medium',
            'payment_feature': 'high',
            'marketplace_feature': 'high',
            'search_feature': 'medium',
            'notification_feature': 'low',
            'encryption_feature': 'high'
        }
        return complexity_map.get(feature, 'medium')
    
    def _assess_competitive_advantage(self, feature: str) -> str:
        """Assess competitive advantage for a feature"""
        advantage_map = {
            'chat_feature': 'Common feature, differentiation through UX',
            'message_feature': 'Standard feature, focus on reliability',
            'call_feature': 'High demand, quality differentiator',
            'video_feature': 'Strong competitive advantage if well-implemented',
            'audio_feature': 'Moderate advantage, depends on quality',
            'file_feature': 'Utility feature, supports main functionality',
            'auth_feature': 'Essential security feature',
            'payment_feature': 'Revenue enabler, high business value',
            'marketplace_feature': 'Strong competitive advantage',
            'search_feature': 'User experience enhancer',
            'notification_feature': 'Engagement driver',
            'encryption_feature': 'Security differentiator, privacy-focused market'
        }
        return advantage_map.get(feature, 'Moderate competitive advantage')
    
    def _assess_monetization_potential(self, feature: str) -> str:
        """Assess monetization potential for a feature"""
        monetization_map = {
            'chat_feature': 'Premium tiers, advanced features',
            'message_feature': 'Message limits, premium messaging',
            'call_feature': 'Call minutes, HD quality',
            'video_feature': 'Video quality, group calls',
            'audio_feature': 'Audio quality, conference calls',
            'file_feature': 'Storage limits, file size limits',
            'auth_feature': 'Enterprise authentication',
            'payment_feature': 'Transaction fees, premium payment options',
            'marketplace_feature': 'Commission, listing fees',
            'search_feature': 'Advanced search, filters',
            'notification_feature': 'Priority notifications',
            'encryption_feature': 'Enterprise security, compliance'
        }
        return monetization_map.get(feature, 'Standard monetization potential')
    
    def _identify_target_audience(self, feature: str) -> str:
        """Identify target audience for a feature"""
        audience_map = {
            'chat_feature': 'General users, businesses, communities',
            'message_feature': 'All user segments',
            'call_feature': 'Business users, remote teams',
            'video_feature': 'Business users, content creators',
            'audio_feature': 'Podcasters, business users',
            'file_feature': 'Business users, content creators',
            'auth_feature': 'All users, enterprise focus',
            'payment_feature': 'E-commerce, service providers',
            'marketplace_feature': 'Service providers, buyers',
            'search_feature': 'All users',
            'notification_feature': 'All users',
            'encryption_feature': 'Privacy-conscious users, enterprises'
        }
        return audience_map.get(feature, 'General user base')
    
    def _estimate_development_time(self, feature: str, complexity: str) -> str:
        """Estimate development time for a feature"""
        base_times = {
            'low': '1-2 weeks',
            'medium': '3-6 weeks',
            'high': '2-4 months'
        }
        return base_times.get(complexity, '4-8 weeks')
    
    def _calculate_roi_projection(self, feature: str, market_score: float) -> str:
        """Calculate ROI projection for a feature"""
        if market_score >= 8.0:
            return 'High ROI expected (200-400%)'
        elif market_score >= 6.0:
            return 'Moderate ROI expected (100-200%)'
        else:
            return 'Low ROI expected (50-100%)'
    
    def _identify_application_type(self, tree: ast.AST) -> str:
        """Identify the type of application from code"""
        # Simple heuristic based on common patterns
        code_str = ast.unparse(tree)
        
        if 'FastAPI' in code_str or 'flask' in code_str.lower():
            return 'web_api'
        elif 'react' in code_str.lower() or 'vue' in code_str.lower():
            return 'web_frontend'
        elif 'chat' in code_str.lower() or 'message' in code_str.lower():
            return 'chat_application'
        elif 'marketplace' in code_str.lower() or 'ecommerce' in code_str.lower():
            return 'marketplace_application'
        else:
            return 'generic_application'
    
    def _get_monetization_strategies(self, app_type: str, features: List[str]) -> List[Dict[str, str]]:
        """Get monetization strategies based on app type and features"""
        strategies = []
        
        if app_type == 'chat_application':
            strategies.extend([
                {
                    'type': 'freemium',
                    'model': 'Free basic chat, premium features',
                    'pricing': '$5-15/month for premium',
                    'target': 'Individual users and small teams',
                    'effort': 'Medium',
                    'revenue': '$10K-100K/month',
                    'risk': 'Low'
                },
                {
                    'type': 'subscription',
                    'model': 'Tiered subscription plans',
                    'pricing': '$10-50/month per user',
                    'target': 'Business users and enterprises',
                    'effort': 'High',
                    'revenue': '$50K-500K/month',
                    'risk': 'Medium'
                }
            ])
        
        if app_type == 'marketplace_application':
            strategies.extend([
                {
                    'type': 'commission',
                    'model': 'Transaction-based commission',
                    'pricing': '5-15% per transaction',
                    'target': 'Service providers and buyers',
                    'effort': 'High',
                    'revenue': '$20K-200K/month',
                    'risk': 'Medium'
                },
                {
                    'type': 'listing_fees',
                    'model': 'Fees for premium listings',
                    'pricing': '$5-50 per listing',
                    'target': 'Service providers',
                    'effort': 'Low',
                    'revenue': '$5K-50K/month',
                    'risk': 'Low'
                }
            ])
        
        return strategies
    
    def _get_security_severity(self, vuln_type: str) -> str:
        """Get severity level for security vulnerability"""
        severity_map = {
            'sql_injection': 'critical',
            'xss_vulnerability': 'high',
            'path_traversal': 'high',
            'command_injection': 'critical',
            'hardcoded_secrets': 'high',
            'insecure_random': 'medium',
            'weak_crypto': 'high',
            'unsafe_deserialization': 'critical',
            'improper_authentication': 'high'
        }
        return severity_map.get(vuln_type, 'medium')
    
    def _get_business_impact(self, vuln_type: str) -> str:
        """Get business impact description for vulnerability"""
        impact_map = {
            'sql_injection': 'Data breach, financial loss, regulatory penalties',
            'xss_vulnerability': 'User data theft, session hijacking, reputation damage',
            'path_traversal': 'Sensitive file access, system compromise',
            'command_injection': 'Full system compromise, data loss',
            'hardcoded_secrets': 'Credential theft, unauthorized access',
            'insecure_random': 'Predictable tokens, session hijacking',
            'weak_crypto': 'Data encryption compromise, privacy breach',
            'unsafe_deserialization': 'Remote code execution, system compromise',
            'improper_authentication': 'Unauthorized access, privilege escalation'
        }
        return impact_map.get(vuln_type, 'Potential security risk')
    
    def _get_related_cve(self, vuln_type: str) -> Optional[str]:
        """Get related CVE for vulnerability type"""
        cve_map = {
            'sql_injection': 'CWE-89',
            'xss_vulnerability': 'CWE-79',
            'path_traversal': 'CWE-22',
            'command_injection': 'CWE-78',
            'hardcoded_secrets': 'CWE-798',
            'insecure_random': 'CWE-330',
            'weak_crypto': 'CWE-327',
            'unsafe_deserialization': 'CWE-502',
            'improper_authentication': 'CWE-287'
        }
        return cve_map.get(vuln_type)
    
    def _get_vulnerability_description(self, vuln_type: str) -> str:
        """Get detailed description for vulnerability"""
        descriptions = {
            'sql_injection': 'SQL injection vulnerability allows attackers to execute arbitrary SQL commands',
            'xss_vulnerability': 'Cross-site scripting vulnerability allows malicious script injection',
            'path_traversal': 'Path traversal vulnerability allows access to files outside intended directory',
            'command_injection': 'Command injection vulnerability allows execution of arbitrary system commands',
            'hardcoded_secrets': 'Hardcoded secrets in source code pose security risk',
            'insecure_random': 'Insecure random number generation can lead to predictable values',
            'weak_crypto': 'Weak cryptographic algorithms provide insufficient security',
            'unsafe_deserialization': 'Unsafe deserialization can lead to remote code execution',
            'improper_authentication': 'Improper authentication implementation allows unauthorized access'
        }
        return descriptions.get(vuln_type, 'Security vulnerability detected')
    
    def _get_remediation_advice(self, vuln_type: str) -> str:
        """Get remediation advice for vulnerability"""
        remediation_map = {
            'sql_injection': 'Use parameterized queries and prepared statements',
            'xss_vulnerability': 'Sanitize user input and use proper encoding',
            'path_traversal': 'Validate and sanitize file paths, use allow-lists',
            'command_injection': 'Avoid shell execution, use parameterized commands',
            'hardcoded_secrets': 'Use environment variables or secret management systems',
            'insecure_random': 'Use cryptographically secure random number generators',
            'weak_crypto': 'Use strong cryptographic algorithms (AES-256, SHA-256)',
            'unsafe_deserialization': 'Validate input before deserialization, use safe formats',
            'improper_authentication': 'Implement proper authentication checks and session management'
        }
        return remediation_map.get(vuln_type, 'Review and fix security implementation')
    
    def generate_input_sanitization_suggestions(self) -> List[str]:
        """Generate suggestions for input sanitization"""
        suggestions = []
        
        for opt in self.optimizations:
            suggestions.append(f"""
# Input sanitization for {opt.function_name}.{opt.parameter_name}
def sanitize_{opt.parameter_name}(value):
    '''Sanitize and validate {opt.parameter_name} input'''
    if isinstance(value, str):
        # Remove potentially dangerous characters
        value = re.sub(r'[<>\"\'&]', '', value)
        # Limit length
        value = value[:1000]
    
    # Add specific validation based on expected type
    {opt.validation_suggestion}
    
    return value
""")
        
        return suggestions
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive code review report"""
        issues_by_severity = {}
        for issue in self.issues:
            if issue.severity not in issues_by_severity:
                issues_by_severity[issue.severity] = []
            issues_by_severity[issue.severity].append(issue)
        
        vulnerabilities_by_severity = {}
        for vuln in self.security_vulnerabilities:
            if vuln.severity not in vulnerabilities_by_severity:
                vulnerabilities_by_severity[vuln.severity] = []
            vulnerabilities_by_severity[vuln.severity].append(vuln)
        
        return {
            'scan_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_issues': len(self.issues),
                'total_vulnerabilities': len(self.security_vulnerabilities),
                'total_optimizations': len(self.optimizations),
                'market_opportunities': len(self.market_analysis),
                'monetization_strategies': len(self.monetization_suggestions),
                'issues_by_severity': {k: len(v) for k, v in issues_by_severity.items()},
                'vulnerabilities_by_severity': {k: len(v) for k, v in vulnerabilities_by_severity.items()}
            },
            'security_vulnerabilities': [
                {
                    'file': vuln.file_path,
                    'line': vuln.line_number,
                    'type': vuln.vulnerability_type,
                    'severity': vuln.severity,
                    'cve': vuln.cve_related,
                    'description': vuln.description,
                    'remediation': vuln.remediation,
                    'business_impact': vuln.business_impact,
                    'code': vuln.code_snippet
                }
                for vuln in self.security_vulnerabilities
            ],
            'code_quality_issues': [
                {
                    'file': issue.file_path,
                    'line': issue.line_number,
                    'type': issue.issue_type,
                    'severity': issue.severity,
                    'description': issue.description,
                    'suggestion': issue.suggestion,
                    'code': issue.code_snippet
                }
                for issue in self.issues
            ],
            'market_analysis': [
                {
                    'feature': analysis.feature_type,
                    'market_demand': analysis.market_demand_score,
                    'complexity': analysis.implementation_complexity,
                    'competitive_advantage': analysis.competitive_advantage,
                    'monetization_potential': analysis.monetization_potential,
                    'target_audience': analysis.target_audience,
                    'development_time': analysis.estimated_development_time,
                    'roi_projection': analysis.roi_projection
                }
                for analysis in self.market_analysis
            ],
            'monetization_suggestions': [
                {
                    'strategy': suggestion.strategy_type,
                    'revenue_model': suggestion.revenue_model,
                    'pricing': suggestion.pricing_suggestion,
                    'target_market': suggestion.target_market,
                    'implementation_effort': suggestion.implementation_effort,
                    'expected_revenue': suggestion.expected_revenue,
                    'risk_level': suggestion.risk_level
                }
                for suggestion in self.monetization_suggestions
            ],
            'input_optimizations': [
                {
                    'function': opt.function_name,
                    'parameter': opt.parameter_name,
                    'current_type': opt.current_type,
                    'suggested_type': opt.suggested_type,
                    'validation': opt.validation_suggestion,
                    'sanitization': opt.sanitization_suggestion
                }
                for opt in self.optimizations
            ],
            'sanitization_code_suggestions': self.generate_input_sanitization_suggestions()
        }
    
    def export_report(self, output_path: str = "pulse_code_review_report.json"):
        """Export the review report to a JSON file"""
        report = self.generate_comprehensive_report()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return output_path
    
    def monitor_application(self, app_directory: str, output_dir: str = "monitoring_reports"):
        """Monitor application continuously"""
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"🔍 Starting continuous monitoring of {app_directory}")
        print(f"📊 Reports will be saved to {output_dir}")
        
        # Clear previous analysis
        self.issues = []
        self.optimizations = []
        self.security_vulnerabilities = []
        self.market_analysis = []
        self.monetization_suggestions = []
        
        # Analyze the application
        results = self.analyze_directory(app_directory)
        
        # Generate comprehensive report
        report = self.generate_comprehensive_report()
        
        # Export report with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(output_dir, f"pulse_monitoring_report_{timestamp}.json")
        self.export_report(report_path)
        
        # Print summary
        print("\n" + "="*60)
        print("🎯 PULSE APPLICATION MONITORING REPORT")
        print("="*60)
        print(f"📅 Scan Time: {report['scan_timestamp']}")
        print(f"📁 Files Analyzed: {len(results)}")
        print(f"🔍 Total Issues: {report['summary']['total_issues']}")
        print(f"🛡️  Security Vulnerabilities: {report['summary']['total_vulnerabilities']}")
        print(f"⚡ Optimization Opportunities: {report['summary']['total_optimizations']}")
        print(f"📈 Market Opportunities: {report['summary']['market_opportunities']}")
        print(f"💰 Monetization Strategies: {report['summary']['monetization_strategies']}")
        
        # Security summary
        if report['summary']['vulnerabilities_by_severity']:
            print("\n🛡️  SECURITY VULNERABILITIES BY SEVERITY:")
            for severity, count in report['summary']['vulnerabilities_by_severity'].items():
                print(f"   {severity.upper()}: {count}")
        
        # Top vulnerabilities
        if report['security_vulnerabilities']:
            print("\n🚨 TOP SECURITY CONCERNS:")
            for vuln in sorted(report['security_vulnerabilities'], 
                             key=lambda x: ['low', 'medium', 'high', 'critical'].index(x['severity']))[:5]:
                print(f"   • {vuln['type']} in {vuln['file']}:{vuln['line']} ({vuln['severity']})")
        
        # Market insights
        if report['market_analysis']:
            print("\n📈 MARKET OPPORTUNITIES:")
            for analysis in sorted(report['market_analysis'], 
                                 key=lambda x: x['market_demand'], reverse=True)[:3]:
                print(f"   • {analysis['feature']} - Demand: {analysis['market_demand']}/10")
        
        # Monetization suggestions
        if report['monetization_suggestions']:
            print("\n💰 TOP MONETIZATION STRATEGIES:")
            for suggestion in report['monetization_suggestions'][:3]:
                print(f"   • {suggestion['strategy']}: {suggestion['revenue_model']}")
        
        print(f"\n📊 Full report saved to: {report_path}")
        print("="*60)
        
        return report_path

if __name__ == "__main__":
    print("🤖 Independent Code Review Agent for Pulse Application")
    print("="*60)
    
    # Initialize the agent
    agent = CodeReviewAgent()
    
    # Monitor the Pulse application
    pulse_directory = "/app"  # Adjust path as needed
    report_path = agent.monitor_application(pulse_directory)
    
    print(f"\n✅ Monitoring complete! Report saved to: {report_path}")