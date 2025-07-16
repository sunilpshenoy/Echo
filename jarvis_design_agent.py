#!/usr/bin/env python3
"""
ENHANCED JARVIS AI DESIGN AGENT
Integration of AI Design Intelligence into Jarvis
Phases 1-3: Foundation, Intelligence, and Advanced Features
"""

import sqlite3
import json
import re
import os
import asyncio
import aiohttp
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import time
import random


@dataclass
class DesignElement:
    """Represents a design element with its properties"""
    element_type: str
    properties: Dict[str, Any]
    context: str
    effectiveness_score: float
    usage_frequency: int
    source_url: str = ""
    created_at: str = ""


@dataclass
class ColorScheme:
    """Represents a color scheme analysis"""
    primary_colors: List[str]
    secondary_colors: List[str]
    accent_colors: List[str]
    contrast_ratios: Dict[str, float]
    accessibility_score: float
    harmony_score: float


@dataclass
class TypographyAnalysis:
    """Represents typography analysis"""
    font_families: List[str]
    font_sizes: List[str]
    line_heights: List[str]
    font_weights: List[str]
    hierarchy_score: float
    readability_score: float


@dataclass
class LayoutPattern:
    """Represents a layout pattern"""
    pattern_type: str
    grid_system: str
    spacing_system: Dict[str, str]
    responsive_breakpoints: List[str]
    complexity_score: float


@dataclass
class DesignReview:
    """Comprehensive design review"""
    app_name: str
    overall_score: float
    color_scheme: ColorScheme
    typography: TypographyAnalysis
    layout_patterns: List[LayoutPattern]
    accessibility_score: float
    performance_score: float
    suggestions: List[str]
    implementation_priority: List[str]
    generated_code: Dict[str, str]
    competitive_analysis: Dict[str, Any]
    improvement_roadmap: List[Dict[str, Any]]


class DesignDatabase:
    """Advanced design pattern database with learning capabilities"""
    
    def __init__(self, db_path: str = "jarvis_design_intelligence.db"):
        self.db_path = db_path
        self.init_database()
        self.pattern_cache = {}
        self.learning_metrics = {}
    
    def init_database(self):
        """Initialize the enhanced design database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Design patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS design_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                description TEXT,
                properties TEXT,
                css_implementation TEXT,
                react_implementation TEXT,
                effectiveness_score REAL,
                usage_frequency INTEGER DEFAULT 0,
                source_url TEXT,
                competitive_score REAL DEFAULT 0.0,
                trend_score REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Color schemes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS color_schemes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheme_name TEXT NOT NULL,
                primary_colors TEXT,
                secondary_colors TEXT,
                accent_colors TEXT,
                contrast_score REAL,
                accessibility_score REAL,
                harmony_score REAL,
                usage_context TEXT,
                source_url TEXT,
                effectiveness_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Typography patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS typography_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT NOT NULL,
                font_families TEXT,
                font_sizes TEXT,
                line_heights TEXT,
                font_weights TEXT,
                hierarchy_score REAL,
                readability_score REAL,
                css_implementation TEXT,
                usage_context TEXT,
                source_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Layout patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS layout_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                grid_system TEXT,
                spacing_system TEXT,
                responsive_breakpoints TEXT,
                complexity_score REAL,
                css_implementation TEXT,
                react_implementation TEXT,
                usage_context TEXT,
                source_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Design reviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS design_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL,
                app_url TEXT,
                overall_score REAL,
                review_data TEXT,
                suggestions TEXT,
                implementation_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Competitive analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitive_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_name TEXT NOT NULL,
                competitor_url TEXT,
                analysis_data TEXT,
                design_score REAL,
                feature_analysis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Learning metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER,
                implementation_success REAL,
                user_feedback REAL,
                effectiveness_change REAL,
                usage_increase REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pattern_id) REFERENCES design_patterns (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_design_pattern(self, pattern: DesignElement, css_impl: str = "", react_impl: str = ""):
        """Store a design pattern with implementations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO design_patterns 
            (pattern_name, category, subcategory, description, properties, 
             css_implementation, react_implementation, effectiveness_score, 
             usage_frequency, source_url, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pattern.element_type,
            pattern.context,
            pattern.properties.get('subcategory', ''),
            f"Design pattern for {pattern.element_type}",
            json.dumps(pattern.properties),
            css_impl,
            react_impl,
            pattern.effectiveness_score,
            pattern.usage_frequency,
            pattern.source_url,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def store_color_scheme(self, scheme: ColorScheme, source_url: str = "", name: str = ""):
        """Store a color scheme"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO color_schemes 
            (scheme_name, primary_colors, secondary_colors, accent_colors,
             contrast_score, accessibility_score, harmony_score, source_url, effectiveness_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name or f"scheme_{int(time.time())}",
            json.dumps(scheme.primary_colors),
            json.dumps(scheme.secondary_colors),
            json.dumps(scheme.accent_colors),
            scheme.contrast_ratios.get('average', 0.0),
            scheme.accessibility_score,
            scheme.harmony_score,
            source_url,
            (scheme.accessibility_score + scheme.harmony_score) / 2
        ))
        
        conn.commit()
        conn.close()
    
    def get_top_patterns(self, category: str = None, limit: int = 10) -> List[DesignElement]:
        """Retrieve top design patterns by effectiveness"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT pattern_name, category, properties, effectiveness_score, 
                   usage_frequency, source_url, created_at
            FROM design_patterns
        '''
        
        if category:
            query += ' WHERE category = ?'
            cursor.execute(query + ' ORDER BY effectiveness_score DESC, usage_frequency DESC LIMIT ?', 
                         (category, limit))
        else:
            cursor.execute(query + ' ORDER BY effectiveness_score DESC, usage_frequency DESC LIMIT ?', 
                         (limit,))
        
        patterns = []
        for row in cursor.fetchall():
            patterns.append(DesignElement(
                element_type=row[0],
                properties=json.loads(row[2]),
                context=row[1],
                effectiveness_score=row[3],
                usage_frequency=row[4],
                source_url=row[5],
                created_at=row[6]
            ))
        
        conn.close()
        return patterns
    
    def get_best_color_schemes(self, limit: int = 5) -> List[ColorScheme]:
        """Get best performing color schemes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT primary_colors, secondary_colors, accent_colors, 
                   contrast_score, accessibility_score, harmony_score
            FROM color_schemes
            ORDER BY effectiveness_score DESC
            LIMIT ?
        ''', (limit,))
        
        schemes = []
        for row in cursor.fetchall():
            schemes.append(ColorScheme(
                primary_colors=json.loads(row[0]),
                secondary_colors=json.loads(row[1]),
                accent_colors=json.loads(row[2]),
                contrast_ratios={'average': row[3]},
                accessibility_score=row[4],
                harmony_score=row[5]
            ))
        
        conn.close()
        return schemes
    
    def update_pattern_effectiveness(self, pattern_name: str, new_score: float):
        """Update pattern effectiveness based on learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE design_patterns 
            SET effectiveness_score = ?, updated_at = ?
            WHERE pattern_name = ?
        ''', (new_score, datetime.now().isoformat(), pattern_name))
        
        conn.commit()
        conn.close()


class DesignPatternAnalyzer:
    """Advanced pattern analysis with AI capabilities"""
    
    def __init__(self, db: DesignDatabase):
        self.db = db
        self.color_analyzer = ColorSchemeAnalyzer()
        self.typography_analyzer = TypographyAnalyzer()
        self.layout_analyzer = LayoutAnalyzer()
    
    def analyze_file_patterns(self, file_path: str, file_content: str) -> List[DesignElement]:
        """Analyze design patterns in a file"""
        patterns = []
        
        # Analyze different file types
        if file_path.endswith('.css'):
            patterns.extend(self._analyze_css_patterns(file_content))
        elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
            patterns.extend(self._analyze_react_patterns(file_content))
        elif file_path.endswith('.html'):
            patterns.extend(self._analyze_html_patterns(file_content))
        
        return patterns
    
    def _analyze_css_patterns(self, css_content: str) -> List[DesignElement]:
        """Analyze CSS patterns"""
        patterns = []
        
        # Color patterns
        color_patterns = self.color_analyzer.extract_css_colors(css_content)
        if color_patterns:
            patterns.append(DesignElement(
                element_type="color_scheme",
                properties={"colors": color_patterns, "source": "css"},
                context="visual_design",
                effectiveness_score=0.7,
                usage_frequency=1
            ))
        
        # Typography patterns
        typography_patterns = self.typography_analyzer.extract_css_typography(css_content)
        if typography_patterns:
            patterns.append(DesignElement(
                element_type="typography",
                properties=typography_patterns,
                context="visual_design",
                effectiveness_score=0.75,
                usage_frequency=1
            ))
        
        # Layout patterns
        layout_patterns = self.layout_analyzer.extract_css_layouts(css_content)
        for layout in layout_patterns:
            patterns.append(DesignElement(
                element_type="layout_pattern",
                properties=layout,
                context="structure",
                effectiveness_score=0.8,
                usage_frequency=1
            ))
        
        return patterns
    
    def _analyze_react_patterns(self, react_content: str) -> List[DesignElement]:
        """Analyze React component patterns"""
        patterns = []
        
        # Component structure patterns
        component_patterns = self._extract_component_patterns(react_content)
        for pattern in component_patterns:
            patterns.append(DesignElement(
                element_type="component_pattern",
                properties=pattern,
                context="react_component",
                effectiveness_score=0.85,
                usage_frequency=1
            ))
        
        # State management patterns
        state_patterns = self._extract_state_patterns(react_content)
        for pattern in state_patterns:
            patterns.append(DesignElement(
                element_type="state_pattern",
                properties=pattern,
                context="react_state",
                effectiveness_score=0.8,
                usage_frequency=1
            ))
        
        return patterns
    
    def _extract_component_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Extract React component patterns"""
        patterns = []
        
        # Find component definitions
        component_regex = r'(?:const|function|class)\s+(\w+)\s*(?:\(|\=)'
        components = re.findall(component_regex, content)
        
        for component in components:
            pattern = {
                "component_name": component,
                "type": "functional" if "const" in content else "class",
                "has_hooks": "useState" in content or "useEffect" in content,
                "has_props": "props" in content,
                "complexity": self._calculate_component_complexity(content)
            }
            patterns.append(pattern)
        
        return patterns
    
    def _extract_state_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Extract state management patterns"""
        patterns = []
        
        # Find useState patterns
        use_state_pattern = r'const\s*\[(\w+),\s*set\w+\]\s*=\s*useState\(([^)]*)\)'
        state_matches = re.findall(use_state_pattern, content)
        
        for state_var, initial_value in state_matches:
            pattern = {
                "state_variable": state_var,
                "initial_value": initial_value,
                "pattern_type": "useState",
                "complexity": len(initial_value) if initial_value else 0
            }
            patterns.append(pattern)
        
        return patterns
    
    def _calculate_component_complexity(self, content: str) -> float:
        """Calculate component complexity score"""
        # Simple complexity metrics
        lines = content.split('\n')
        jsx_elements = len(re.findall(r'<\w+', content))
        hooks = len(re.findall(r'use\w+', content))
        
        complexity = (len(lines) * 0.1) + (jsx_elements * 0.2) + (hooks * 0.3)
        return min(complexity / 10, 1.0)  # Normalize to 0-1


class ColorSchemeAnalyzer:
    """Advanced color scheme analysis"""
    
    def extract_css_colors(self, css_content: str) -> Dict[str, List[str]]:
        """Extract color scheme from CSS"""
        colors = {
            "primary": [],
            "secondary": [],
            "accent": [],
            "background": [],
            "text": []
        }
        
        # Extract color values
        color_regex = r'(?:color|background-color|border-color|fill|stroke):\s*([^;]+)'
        color_matches = re.findall(color_regex, css_content)
        
        for color_value in color_matches:
            color_value = color_value.strip()
            
            # Categorize colors
            if self._is_primary_color(color_value):
                colors["primary"].append(color_value)
            elif self._is_background_color(color_value):
                colors["background"].append(color_value)
            elif self._is_text_color(color_value):
                colors["text"].append(color_value)
            else:
                colors["accent"].append(color_value)
        
        # Remove duplicates and limit
        for category in colors:
            colors[category] = list(set(colors[category]))[:5]
        
        return colors
    
    def _is_primary_color(self, color: str) -> bool:
        """Check if color is likely a primary color"""
        primary_keywords = ['primary', 'main', 'brand']
        return any(keyword in color.lower() for keyword in primary_keywords)
    
    def _is_background_color(self, color: str) -> bool:
        """Check if color is likely a background color"""
        bg_keywords = ['background', 'bg', 'surface']
        return any(keyword in color.lower() for keyword in bg_keywords)
    
    def _is_text_color(self, color: str) -> bool:
        """Check if color is likely a text color"""
        text_keywords = ['text', 'color', 'font']
        return any(keyword in color.lower() for keyword in text_keywords)
    
    def analyze_color_harmony(self, colors: List[str]) -> float:
        """Analyze color harmony score"""
        if not colors:
            return 0.0
        
        # Simple harmony analysis (can be enhanced with color theory)
        unique_colors = set(colors)
        
        # More unique colors generally means better palette
        diversity_score = min(len(unique_colors) / 5, 1.0)
        
        # Check for common good combinations
        harmony_bonus = 0.0
        if any('#' in color for color in colors):
            harmony_bonus += 0.2
        if any('rgb' in color for color in colors):
            harmony_bonus += 0.1
        
        return min(diversity_score + harmony_bonus, 1.0)


class TypographyAnalyzer:
    """Advanced typography analysis"""
    
    def extract_css_typography(self, css_content: str) -> Dict[str, Any]:
        """Extract typography patterns from CSS"""
        typography = {
            "font_families": [],
            "font_sizes": [],
            "line_heights": [],
            "font_weights": [],
            "text_properties": []
        }
        
        # Extract font families
        font_family_regex = r'font-family:\s*([^;]+)'
        font_families = re.findall(font_family_regex, css_content)
        typography["font_families"] = list(set(font_families))[:5]
        
        # Extract font sizes
        font_size_regex = r'font-size:\s*([^;]+)'
        font_sizes = re.findall(font_size_regex, css_content)
        typography["font_sizes"] = list(set(font_sizes))[:10]
        
        # Extract line heights
        line_height_regex = r'line-height:\s*([^;]+)'
        line_heights = re.findall(line_height_regex, css_content)
        typography["line_heights"] = list(set(line_heights))[:5]
        
        # Extract font weights
        font_weight_regex = r'font-weight:\s*([^;]+)'
        font_weights = re.findall(font_weight_regex, css_content)
        typography["font_weights"] = list(set(font_weights))[:5]
        
        return typography
    
    def calculate_hierarchy_score(self, typography: Dict[str, Any]) -> float:
        """Calculate typography hierarchy score"""
        font_sizes = typography.get("font_sizes", [])
        font_weights = typography.get("font_weights", [])
        
        # Good hierarchy has multiple font sizes and weights
        size_variety = min(len(font_sizes) / 6, 1.0)
        weight_variety = min(len(font_weights) / 4, 1.0)
        
        return (size_variety + weight_variety) / 2


class LayoutAnalyzer:
    """Advanced layout analysis"""
    
    def extract_css_layouts(self, css_content: str) -> List[Dict[str, Any]]:
        """Extract layout patterns from CSS"""
        layouts = []
        
        # Grid patterns
        if 'display: grid' in css_content or 'grid-template' in css_content:
            grid_pattern = self._analyze_grid_pattern(css_content)
            layouts.append(grid_pattern)
        
        # Flexbox patterns
        if 'display: flex' in css_content or 'flex-direction' in css_content:
            flex_pattern = self._analyze_flex_pattern(css_content)
            layouts.append(flex_pattern)
        
        # Container patterns
        container_pattern = self._analyze_container_pattern(css_content)
        if container_pattern:
            layouts.append(container_pattern)
        
        return layouts
    
    def _analyze_grid_pattern(self, css_content: str) -> Dict[str, Any]:
        """Analyze CSS Grid patterns"""
        return {
            "type": "grid",
            "has_template_columns": "grid-template-columns" in css_content,
            "has_template_rows": "grid-template-rows" in css_content,
            "has_gap": "gap" in css_content or "grid-gap" in css_content,
            "is_responsive": "minmax" in css_content or "auto-fit" in css_content,
            "complexity": self._calculate_grid_complexity(css_content)
        }
    
    def _analyze_flex_pattern(self, css_content: str) -> Dict[str, Any]:
        """Analyze Flexbox patterns"""
        return {
            "type": "flexbox",
            "has_direction": "flex-direction" in css_content,
            "has_wrap": "flex-wrap" in css_content,
            "has_justify": "justify-content" in css_content,
            "has_align": "align-items" in css_content,
            "complexity": self._calculate_flex_complexity(css_content)
        }
    
    def _analyze_container_pattern(self, css_content: str) -> Dict[str, Any]:
        """Analyze container patterns"""
        has_max_width = "max-width" in css_content
        has_margin_auto = "margin: 0 auto" in css_content or "margin: auto" in css_content
        has_padding = "padding" in css_content
        
        if has_max_width or has_margin_auto or has_padding:
            return {
                "type": "container",
                "has_max_width": has_max_width,
                "has_centering": has_margin_auto,
                "has_padding": has_padding,
                "complexity": 0.6
            }
        return None
    
    def _calculate_grid_complexity(self, css_content: str) -> float:
        """Calculate grid complexity"""
        complexity = 0.0
        if "grid-template-columns" in css_content:
            complexity += 0.3
        if "grid-template-rows" in css_content:
            complexity += 0.3
        if "grid-area" in css_content:
            complexity += 0.2
        if "minmax" in css_content:
            complexity += 0.2
        return min(complexity, 1.0)
    
    def _calculate_flex_complexity(self, css_content: str) -> float:
        """Calculate flexbox complexity"""
        complexity = 0.0
        if "flex-direction" in css_content:
            complexity += 0.2
        if "flex-wrap" in css_content:
            complexity += 0.2
        if "justify-content" in css_content:
            complexity += 0.2
        if "align-items" in css_content:
            complexity += 0.2
        if "flex-grow" in css_content or "flex-shrink" in css_content:
            complexity += 0.2
        return min(complexity, 1.0)


# Continue with the rest of the implementation...

class WebDesignScraper:
    """Advanced web design scraper with intelligence"""
    
    def __init__(self, db: DesignDatabase):
        self.db = db
        self.session = None
        self.scrape_delay = 2  # Respectful scraping delay
        self.max_concurrent = 3  # Limit concurrent requests
    
    async def scrape_design_inspiration(self, sources: List[str]) -> List[DesignElement]:
        """Scrape design inspiration from multiple sources"""
        design_elements = []
        
        # Create session with proper headers
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
            self.session = session
            
            # Process sources concurrently but respectfully
            semaphore = asyncio.Semaphore(self.max_concurrent)
            tasks = []
            
            for source in sources:
                task = self._scrape_single_source(semaphore, source)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    design_elements.extend(result)
                elif isinstance(result, Exception):
                    print(f"Scraping error: {result}")
        
        return design_elements
    
    async def _scrape_single_source(self, semaphore: asyncio.Semaphore, source: str) -> List[DesignElement]:
        """Scrape a single source with rate limiting"""
        async with semaphore:
            try:
                await asyncio.sleep(self.scrape_delay)  # Respectful delay
                
                async with self.session.get(source, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._analyze_scraped_content(html, source)
                    else:
                        print(f"Failed to scrape {source}: {response.status}")
                        return []
                        
            except Exception as e:
                print(f"Error scraping {source}: {e}")
                return []
    
    def _analyze_scraped_content(self, html: str, source_url: str) -> List[DesignElement]:
        """Analyze scraped HTML content"""
        elements = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract design elements
            color_elements = self._extract_color_schemes(soup, source_url)
            typography_elements = self._extract_typography_patterns(soup, source_url)
            layout_elements = self._extract_layout_patterns(soup, source_url)
            component_elements = self._extract_component_patterns(soup, source_url)
            
            elements.extend(color_elements)
            elements.extend(typography_elements)
            elements.extend(layout_elements)
            elements.extend(component_elements)
            
        except Exception as e:
            print(f"Error analyzing content from {source_url}: {e}")
        
        return elements
    
    def _extract_color_schemes(self, soup: BeautifulSoup, source_url: str) -> List[DesignElement]:
        """Extract color schemes from HTML"""
        elements = []
        
        # Extract colors from CSS
        colors = self._extract_colors_from_css(soup)
        
        if colors:
            # Analyze color harmony
            harmony_score = self._calculate_color_harmony(colors)
            accessibility_score = self._calculate_color_accessibility(colors)
            
            color_scheme = ColorScheme(
                primary_colors=colors[:3],
                secondary_colors=colors[3:6],
                accent_colors=colors[6:9],
                contrast_ratios={'average': accessibility_score},
                accessibility_score=accessibility_score,
                harmony_score=harmony_score
            )
            
            # Store in database
            self.db.store_color_scheme(color_scheme, source_url)
            
            elements.append(DesignElement(
                element_type="color_scheme",
                properties={
                    "colors": colors,
                    "harmony_score": harmony_score,
                    "accessibility_score": accessibility_score
                },
                context="visual_design",
                effectiveness_score=(harmony_score + accessibility_score) / 2,
                usage_frequency=1,
                source_url=source_url
            ))
        
        return elements
    
    def _extract_colors_from_css(self, soup: BeautifulSoup) -> List[str]:
        """Extract colors from CSS in HTML"""
        colors = []
        
        # Extract from style tags
        for style_tag in soup.find_all('style'):
            css_text = style_tag.get_text()
            color_matches = re.findall(r'(?:color|background-color|border-color|fill|stroke):\s*([^;]+)', css_text)
            colors.extend(color_matches)
        
        # Extract from inline styles
        for element in soup.find_all(style=True):
            style = element.get('style', '')
            color_matches = re.findall(r'(?:color|background-color|border-color):\s*([^;]+)', style)
            colors.extend(color_matches)
        
        # Clean and filter colors
        cleaned_colors = []
        for color in colors:
            color = color.strip()
            if self._is_valid_color(color):
                cleaned_colors.append(color)
        
        return list(set(cleaned_colors))[:12]  # Limit to 12 unique colors
    
    def _is_valid_color(self, color: str) -> bool:
        """Check if color value is valid"""
        color = color.strip().lower()
        
        # Check for common color formats
        if color.startswith('#') and len(color) in [4, 7]:
            return True
        if color.startswith('rgb') or color.startswith('rgba'):
            return True
        if color.startswith('hsl') or color.startswith('hsla'):
            return True
        if color in ['black', 'white', 'red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink', 'gray', 'brown']:
            return True
        
        return False
    
    def _calculate_color_harmony(self, colors: List[str]) -> float:
        """Calculate color harmony score"""
        if not colors:
            return 0.0
        
        # Simple harmony calculation (can be enhanced with color theory)
        unique_colors = set(colors)
        diversity_score = min(len(unique_colors) / 8, 1.0)
        
        # Bonus for having both light and dark colors
        has_light = any('white' in color.lower() or '#f' in color.lower() for color in colors)
        has_dark = any('black' in color.lower() or '#0' in color.lower() for color in colors)
        contrast_bonus = 0.2 if has_light and has_dark else 0.0
        
        return min(diversity_score + contrast_bonus, 1.0)
    
    def _calculate_color_accessibility(self, colors: List[str]) -> float:
        """Calculate color accessibility score"""
        if not colors:
            return 0.0
        
        # Simple accessibility check
        accessibility_score = 0.8  # Base score
        
        # Penalty for too many similar colors
        if len(set(colors)) < len(colors) * 0.6:
            accessibility_score -= 0.2
        
        # Bonus for high contrast indicators
        if any('#000' in color or 'black' in color for color in colors) and \
           any('#fff' in color or 'white' in color for color in colors):
            accessibility_score += 0.1
        
        return min(accessibility_score, 1.0)
    
    def _extract_typography_patterns(self, soup: BeautifulSoup, source_url: str) -> List[DesignElement]:
        """Extract typography patterns"""
        elements = []
        
        # Extract font information
        font_families = self._extract_font_families(soup)
        font_sizes = self._extract_font_sizes(soup)
        
        if font_families or font_sizes:
            typography = TypographyAnalysis(
                font_families=font_families,
                font_sizes=font_sizes,
                line_heights=[],
                font_weights=[],
                hierarchy_score=self._calculate_typography_hierarchy(font_sizes),
                readability_score=self._calculate_typography_readability(font_families, font_sizes)
            )
            
            elements.append(DesignElement(
                element_type="typography",
                properties={
                    "font_families": font_families,
                    "font_sizes": font_sizes,
                    "hierarchy_score": typography.hierarchy_score,
                    "readability_score": typography.readability_score
                },
                context="visual_design",
                effectiveness_score=(typography.hierarchy_score + typography.readability_score) / 2,
                usage_frequency=1,
                source_url=source_url
            ))
        
        return elements
    
    def _extract_font_families(self, soup: BeautifulSoup) -> List[str]:
        """Extract font families from HTML"""
        font_families = []
        
        # Extract from style tags
        for style_tag in soup.find_all('style'):
            css_text = style_tag.get_text()
            font_matches = re.findall(r'font-family:\s*([^;]+)', css_text)
            font_families.extend(font_matches)
        
        # Clean and filter
        cleaned_fonts = []
        for font in font_families:
            font = font.strip().replace('"', '').replace("'", '')
            if font and font not in cleaned_fonts:
                cleaned_fonts.append(font)
        
        return cleaned_fonts[:5]  # Limit to 5 fonts
    
    def _extract_font_sizes(self, soup: BeautifulSoup) -> List[str]:
        """Extract font sizes from HTML"""
        font_sizes = []
        
        # Extract from style tags
        for style_tag in soup.find_all('style'):
            css_text = style_tag.get_text()
            size_matches = re.findall(r'font-size:\s*([^;]+)', css_text)
            font_sizes.extend(size_matches)
        
        # Clean and filter
        cleaned_sizes = []
        for size in font_sizes:
            size = size.strip()
            if size and size not in cleaned_sizes:
                cleaned_sizes.append(size)
        
        return cleaned_sizes[:8]  # Limit to 8 sizes
    
    def _calculate_typography_hierarchy(self, font_sizes: List[str]) -> float:
        """Calculate typography hierarchy score"""
        if not font_sizes:
            return 0.0
        
        # Good hierarchy has variety in sizes
        unique_sizes = set(font_sizes)
        variety_score = min(len(unique_sizes) / 6, 1.0)
        
        # Bonus for having rem/em units (better for responsive design)
        responsive_bonus = 0.0
        if any('rem' in size or 'em' in size for size in font_sizes):
            responsive_bonus = 0.2
        
        return min(variety_score + responsive_bonus, 1.0)
    
    def _calculate_typography_readability(self, font_families: List[str], font_sizes: List[str]) -> float:
        """Calculate typography readability score"""
        readability_score = 0.7  # Base score
        
        # Bonus for web-safe fonts
        web_safe_fonts = ['Arial', 'Helvetica', 'Georgia', 'Times', 'Verdana', 'Trebuchet']
        if any(font in ' '.join(font_families) for font in web_safe_fonts):
            readability_score += 0.1
        
        # Bonus for reasonable font sizes
        if any('px' in size for size in font_sizes):
            try:
                pixel_sizes = [int(re.search(r'(\d+)px', size).group(1)) for size in font_sizes if 'px' in size]
                if any(14 <= size <= 18 for size in pixel_sizes):  # Good reading size
                    readability_score += 0.2
            except:
                pass
        
        return min(readability_score, 1.0)
    
    def _extract_layout_patterns(self, soup: BeautifulSoup, source_url: str) -> List[DesignElement]:
        """Extract layout patterns"""
        elements = []
        
        # Look for grid and flex layouts
        grid_elements = soup.find_all(class_=re.compile(r'grid|row|col'))
        flex_elements = soup.find_all(class_=re.compile(r'flex|d-flex'))
        
        if grid_elements:
            grid_pattern = LayoutPattern(
                pattern_type="grid",
                grid_system="css_grid",
                spacing_system={"gap": "variable"},
                responsive_breakpoints=["sm", "md", "lg"],
                complexity_score=0.8
            )
            
            elements.append(DesignElement(
                element_type="layout_grid",
                properties={
                    "type": "grid",
                    "elements_count": len(grid_elements),
                    "complexity": grid_pattern.complexity_score
                },
                context="layout",
                effectiveness_score=0.85,
                usage_frequency=len(grid_elements),
                source_url=source_url
            ))
        
        if flex_elements:
            flex_pattern = LayoutPattern(
                pattern_type="flexbox",
                grid_system="flexbox",
                spacing_system={"gap": "variable"},
                responsive_breakpoints=["sm", "md", "lg"],
                complexity_score=0.7
            )
            
            elements.append(DesignElement(
                element_type="layout_flex",
                properties={
                    "type": "flexbox",
                    "elements_count": len(flex_elements),
                    "complexity": flex_pattern.complexity_score
                },
                context="layout",
                effectiveness_score=0.8,
                usage_frequency=len(flex_elements),
                source_url=source_url
            ))
        
        return elements
    
    def _extract_component_patterns(self, soup: BeautifulSoup, source_url: str) -> List[DesignElement]:
        """Extract UI component patterns"""
        elements = []
        
        # Look for common UI components
        buttons = soup.find_all(['button', 'a'], class_=re.compile(r'btn|button'))
        cards = soup.find_all(class_=re.compile(r'card|panel|tile'))
        forms = soup.find_all('form')
        navs = soup.find_all(['nav', 'header'])
        
        if buttons:
            elements.append(DesignElement(
                element_type="button_component",
                properties={
                    "count": len(buttons),
                    "types": self._analyze_button_types(buttons),
                    "has_states": self._check_button_states(buttons)
                },
                context="ui_component",
                effectiveness_score=0.9,
                usage_frequency=len(buttons),
                source_url=source_url
            ))
        
        if cards:
            elements.append(DesignElement(
                element_type="card_component",
                properties={
                    "count": len(cards),
                    "layout": "grid" if len(cards) > 1 else "single",
                    "has_images": bool(soup.find_all('img'))
                },
                context="ui_component",
                effectiveness_score=0.85,
                usage_frequency=len(cards),
                source_url=source_url
            ))
        
        if forms:
            elements.append(DesignElement(
                element_type="form_component",
                properties={
                    "count": len(forms),
                    "input_types": self._analyze_form_inputs(forms),
                    "has_validation": self._check_form_validation(forms)
                },
                context="ui_component",
                effectiveness_score=0.8,
                usage_frequency=len(forms),
                source_url=source_url
            ))
        
        if navs:
            elements.append(DesignElement(
                element_type="navigation_component",
                properties={
                    "count": len(navs),
                    "type": "header" if navs[0].name == 'header' else "nav",
                    "has_dropdown": bool(soup.find_all(class_=re.compile(r'dropdown|submenu')))
                },
                context="ui_component",
                effectiveness_score=0.9,
                usage_frequency=len(navs),
                source_url=source_url
            ))
        
        return elements
    
    def _analyze_button_types(self, buttons: List) -> List[str]:
        """Analyze button types"""
        types = []
        for button in buttons:
            classes = button.get('class', [])
            class_str = ' '.join(classes) if classes else ''
            
            if 'primary' in class_str:
                types.append('primary')
            elif 'secondary' in class_str:
                types.append('secondary')
            elif 'danger' in class_str or 'delete' in class_str:
                types.append('danger')
            else:
                types.append('default')
        
        return list(set(types))
    
    def _check_button_states(self, buttons: List) -> bool:
        """Check if buttons have state variations"""
        for button in buttons:
            classes = button.get('class', [])
            class_str = ' '.join(classes) if classes else ''
            
            if any(state in class_str for state in ['hover', 'active', 'disabled', 'focus']):
                return True
        
        return False
    
    def _analyze_form_inputs(self, forms: List) -> List[str]:
        """Analyze form input types"""
        input_types = []
        
        for form in forms:
            inputs = form.find_all(['input', 'textarea', 'select'])
            for input_elem in inputs:
                input_type = input_elem.get('type', 'text')
                if input_type not in input_types:
                    input_types.append(input_type)
        
        return input_types
    
    def _check_form_validation(self, forms: List) -> bool:
        """Check if forms have validation"""
        for form in forms:
            inputs = form.find_all(['input', 'textarea', 'select'])
            for input_elem in inputs:
                if input_elem.get('required') or input_elem.get('pattern'):
                    return True
        
        return False


class CompetitiveAnalyzer:
    """Analyze competitor designs for insights"""
    
    def __init__(self, db: DesignDatabase):
        self.db = db
        self.scraper = WebDesignScraper(db)
    
    async def analyze_competitors(self, competitor_urls: List[str]) -> Dict[str, Any]:
        """Analyze competitor designs"""
        competitive_analysis = {
            "competitors": [],
            "best_practices": [],
            "improvement_opportunities": [],
            "design_trends": []
        }
        
        for url in competitor_urls:
            try:
                competitor_data = await self._analyze_single_competitor(url)
                competitive_analysis["competitors"].append(competitor_data)
            except Exception as e:
                print(f"Error analyzing competitor {url}: {e}")
        
        # Extract best practices
        competitive_analysis["best_practices"] = self._extract_best_practices(
            competitive_analysis["competitors"]
        )
        
        # Identify improvement opportunities
        competitive_analysis["improvement_opportunities"] = self._identify_opportunities(
            competitive_analysis["competitors"]
        )
        
        # Analyze design trends
        competitive_analysis["design_trends"] = self._analyze_design_trends(
            competitive_analysis["competitors"]
        )
        
        # Store in database
        self._store_competitive_analysis(competitive_analysis)
        
        return competitive_analysis
    
    async def _analyze_single_competitor(self, url: str) -> Dict[str, Any]:
        """Analyze a single competitor"""
        competitor_name = urlparse(url).netloc
        
        # Scrape design elements
        design_elements = await self.scraper.scrape_design_inspiration([url])
        
        # Calculate design score
        design_score = self._calculate_design_score(design_elements)
        
        # Analyze features
        feature_analysis = self._analyze_features(design_elements)
        
        return {
            "name": competitor_name,
            "url": url,
            "design_score": design_score,
            "design_elements": [asdict(elem) for elem in design_elements],
            "feature_analysis": feature_analysis,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def _calculate_design_score(self, design_elements: List[DesignElement]) -> float:
        """Calculate overall design score for competitor"""
        if not design_elements:
            return 0.0
        
        total_score = sum(elem.effectiveness_score for elem in design_elements)
        average_score = total_score / len(design_elements)
        
        # Bonus for having diverse design elements
        diversity_bonus = min(len(design_elements) / 10, 0.2)
        
        return min(average_score + diversity_bonus, 1.0)
    
    def _analyze_features(self, design_elements: List[DesignElement]) -> Dict[str, Any]:
        """Analyze competitor features"""
        features = {
            "has_responsive_design": False,
            "has_modern_typography": False,
            "has_consistent_colors": False,
            "has_advanced_layouts": False,
            "ui_components": []
        }
        
        for element in design_elements:
            if element.element_type == "layout_grid" or element.element_type == "layout_flex":
                features["has_advanced_layouts"] = True
            elif element.element_type == "typography":
                features["has_modern_typography"] = element.effectiveness_score > 0.7
            elif element.element_type == "color_scheme":
                features["has_consistent_colors"] = element.effectiveness_score > 0.7
            elif element.context == "ui_component":
                features["ui_components"].append(element.element_type)
        
        return features
    
    def _extract_best_practices(self, competitors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract best practices from competitors"""
        best_practices = []
        
        # Find highest scoring design elements
        all_elements = []
        for competitor in competitors:
            for element_dict in competitor["design_elements"]:
                element_dict["competitor"] = competitor["name"]
                all_elements.append(element_dict)
        
        # Sort by effectiveness score
        all_elements.sort(key=lambda x: x["effectiveness_score"], reverse=True)
        
        # Extract top practices
        for element in all_elements[:10]:  # Top 10 practices
            best_practices.append({
                "practice": element["element_type"],
                "effectiveness": element["effectiveness_score"],
                "source": element["competitor"],
                "properties": element["properties"]
            })
        
        return best_practices
    
    def _identify_opportunities(self, competitors: List[Dict[str, Any]]) -> List[str]:
        """Identify improvement opportunities"""
        opportunities = []
        
        # Common patterns across competitors
        common_patterns = {}
        for competitor in competitors:
            for element_dict in competitor["design_elements"]:
                pattern = element_dict["element_type"]
                if pattern not in common_patterns:
                    common_patterns[pattern] = 0
                common_patterns[pattern] += 1
        
        # Identify most common patterns
        for pattern, count in common_patterns.items():
            if count >= len(competitors) * 0.6:  # Used by 60% of competitors
                opportunities.append(f"Implement {pattern} - used by {count}/{len(competitors)} competitors")
        
        return opportunities
    
    def _analyze_design_trends(self, competitors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze design trends from competitors"""
        trends = []
        
        # Analyze color trends
        color_trends = self._analyze_color_trends(competitors)
        if color_trends:
            trends.append(color_trends)
        
        # Analyze layout trends
        layout_trends = self._analyze_layout_trends(competitors)
        if layout_trends:
            trends.append(layout_trends)
        
        # Analyze component trends
        component_trends = self._analyze_component_trends(competitors)
        if component_trends:
            trends.append(component_trends)
        
        return trends
    
    def _analyze_color_trends(self, competitors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze color trends"""
        all_colors = []
        
        for competitor in competitors:
            for element_dict in competitor["design_elements"]:
                if element_dict["element_type"] == "color_scheme":
                    colors = element_dict["properties"].get("colors", [])
                    all_colors.extend(colors)
        
        if not all_colors:
            return {}
        
        # Find most common colors
        color_frequency = {}
        for color in all_colors:
            color_frequency[color] = color_frequency.get(color, 0) + 1
        
        popular_colors = sorted(color_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "trend_type": "color_scheme",
            "popular_colors": [color for color, freq in popular_colors],
            "usage_frequency": dict(popular_colors),
            "trend_strength": len(popular_colors) / len(set(all_colors))
        }
    
    def _analyze_layout_trends(self, competitors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze layout trends"""
        layout_types = []
        
        for competitor in competitors:
            for element_dict in competitor["design_elements"]:
                if element_dict["element_type"].startswith("layout_"):
                    layout_types.append(element_dict["element_type"])
        
        if not layout_types:
            return {}
        
        # Find most common layout types
        layout_frequency = {}
        for layout in layout_types:
            layout_frequency[layout] = layout_frequency.get(layout, 0) + 1
        
        popular_layouts = sorted(layout_frequency.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "trend_type": "layout_patterns",
            "popular_layouts": [layout for layout, freq in popular_layouts],
            "usage_frequency": dict(popular_layouts),
            "trend_strength": len(popular_layouts) / len(competitors)
        }
    
    def _analyze_component_trends(self, competitors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze UI component trends"""
        components = []
        
        for competitor in competitors:
            for element_dict in competitor["design_elements"]:
                if element_dict["context"] == "ui_component":
                    components.append(element_dict["element_type"])
        
        if not components:
            return {}
        
        # Find most common components
        component_frequency = {}
        for component in components:
            component_frequency[component] = component_frequency.get(component, 0) + 1
        
        popular_components = sorted(component_frequency.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "trend_type": "ui_components",
            "popular_components": [comp for comp, freq in popular_components],
            "usage_frequency": dict(popular_components),
            "trend_strength": len(popular_components) / len(competitors)
        }
    
    def _store_competitive_analysis(self, analysis: Dict[str, Any]):
        """Store competitive analysis in database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        for competitor in analysis["competitors"]:
            cursor.execute('''
                INSERT OR REPLACE INTO competitive_analysis 
                (competitor_name, competitor_url, analysis_data, design_score, feature_analysis)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                competitor["name"],
                competitor["url"],
                json.dumps(competitor),
                competitor["design_score"],
                json.dumps(competitor["feature_analysis"])
            ))
        
        conn.commit()
        conn.close()


# Continue with Phase 3...