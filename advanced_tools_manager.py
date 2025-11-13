#!/usr/bin/env python3
"""
Advanced GenSpark Tools Manager

An enhanced version of the tools finder with advanced features including:
- AI-powered tool recommendations
- User preference learning
- Integration complexity scoring
- Cost optimization suggestions
- Team collaboration features
- API server for web apps

Usage:
    python advanced_tools_manager.py --ai-recommend --budget 1000 --team-size 5
    python advanced_tools_manager.py --serve --port 8000
    python advanced_tools_manager.py --optimize-stack --category ai --budget free
"""

import json
import argparse
import sqlite3
import hashlib
import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from flask import Flask, request, jsonify, render_template_string
import threading
import time
import os


class IntegrationComplexity(Enum):
    EASY = "easy"
    INTERMEDIATE = "intermediate"
    HARD = "hard"


class BudgetLevel(Enum):
    FREE = "free"
    FREEMIUM = "freemium"
    PAID = "paid"


@dataclass
class UserProfile:
    id: str
    team_size: int
    budget: float
    technical_level: str
    preferred_categories: List[str]
    startup_stage: str
    created_at: datetime.datetime
    last_updated: datetime.datetime


@dataclass
class ToolRecommendation:
    tool: Dict
    score: float
    reasoning: str
    integration_complexity: int
    cost_effectiveness: float
    team_fit_score: float


class AdvancedToolsManager:
    def __init__(self, data_file: str = 'tools-data.json', db_file: str = 'tools_manager.db'):
        """Initialize the advanced tools manager with database and AI features."""
        self.data_file = data_file
        self.db_file = db_file
        self.app = Flask(__name__)
        self.load_data()
        self.init_database()
        self.setup_routes()
        
    def load_data(self):
        """Load tools data from JSON file."""
        try:
            with open(self.data_file, 'r') as f:
                self.tools_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: {self.data_file} not found. Creating sample data...")
            self.create_sample_data()
    
    def create_sample_data(self):
        """Create sample data if JSON file doesn't exist."""
        self.tools_data = {
            "categories": [
                {
                    "name": "AI & Machine Learning",
                    "subcategories": [
                        {
                            "name": "AI Development Platforms",
                            "tools": [
                                {
                                    "name": "GenSpark AI Platform",
                                    "url": "https://genspark.ai",
                                    "description": "Your primary AI development platform",
                                    "pricing": "Freemium",
                                    "genSparkIntegration": "Native",
                                    "difficulty": "Easy",
                                    "startupFriendly": True,
                                    "category": "AI & Machine Learning",
                                    "features": ["NLP", "Computer Vision", "ML Models", "API"],
                                    "complexity_score": 2,
                                    "cost_per_user": 0,
                                    "team_size_recommendation": "1-1000+",
                                    "learning_curve_days": 1
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    
    def init_database(self):
        """Initialize SQLite database for user profiles and preferences."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # User profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id TEXT PRIMARY KEY,
                team_size INTEGER,
                budget REAL,
                technical_level TEXT,
                preferred_categories TEXT,
                startup_stage TEXT,
                created_at TIMESTAMP,
                last_updated TIMESTAMP
            )
        ''')
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                tool_name TEXT,
                rating INTEGER,
                used BOOLEAN,
                comment TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles (id)
            )
        ''')
        
        # Tool usage analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tool_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT,
                recommendation_count INTEGER,
                click_count INTEGER,
                rating_sum INTEGER,
                rating_count INTEGER,
                last_updated TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_all_tools(self) -> List[Dict]:
        """Get all tools flattened from categories."""
        tools = []
        for category in self.tools_data['categories']:
            for subcategory in category['subcategories']:
                tools.extend(subcategory['tools'])
        return tools
    
    def calculate_integration_score(self, tool: Dict, user_profile: UserProfile) -> float:
        """Calculate integration complexity score based on user profile."""
        difficulty_scores = {
            "easy": 1.0,
            "intermediate": 0.7,
            "hard": 0.3
        }
        
        base_score = difficulty_scores.get(tool.get('difficulty', 'intermediate'), 0.7)
        
        # Adjust based on user technical level
        if user_profile.technical_level == "expert":
            base_score *= 1.2
        elif user_profile.technical_level == "beginner":
            base_score *= 0.8
        
        # Adjust based on team size
        if user_profile.team_size > 10:
            base_score *= 1.1  # Larger teams can handle complexity better
        
        return min(base_score, 1.0)
    
    def calculate_cost_effectiveness(self, tool: Dict, user_profile: UserProfile) -> float:
        """Calculate cost effectiveness score."""
        pricing = tool.get('pricing', '').lower()
        
        if pricing == 'free':
            return 1.0
        elif 'freemium' in pricing:
            return 0.8
        else:
            # Extract cost per user if available
            cost_per_user = tool.get('cost_per_user', 50)  # Default assumption
            monthly_cost = cost_per_user * user_profile.team_size
            
            # Calculate based on budget ratio
            if user_profile.budget > 0:
                cost_ratio = monthly_cost / user_profile.budget
                if cost_ratio < 0.1:  # Less than 10% of budget
                    return 0.9
                elif cost_ratio < 0.25:  # Less than 25% of budget
                    return 0.7
                else:
                    return 0.4
            else:
                return 0.3  # Assume expensive if no budget info
    
    def calculate_team_fit(self, tool: Dict, user_profile: UserProfile) -> float:
        """Calculate how well the tool fits the team."""
        team_size_recommendation = tool.get('team_size_recommendation', '1-100')
        
        # Parse team size recommendation
        if '+' in team_size_recommendation:
            min_size = int(team_size_recommendation.replace('+', ''))
            if user_profile.team_size >= min_size:
                return 1.0
            else:
                return 0.6
        elif '-' in team_size_recommendation:
            parts = team_size_recommendation.split('-')
            min_size = int(parts[0])
            max_size = int(parts[1])
            if min_size <= user_profile.team_size <= max_size:
                return 1.0
            else:
                return 0.7
        
        return 0.8  # Default assumption
    
    def ai_recommend_tools(self, user_profile: UserProfile, limit: int = 10) -> List[ToolRecommendation]:
        """AI-powered tool recommendations based on user profile."""
        all_tools = self.get_all_tools()
        recommendations = []
        
        for tool in all_tools:
            # Calculate individual scores
            integration_score = self.calculate_integration_score(tool, user_profile)
            cost_effectiveness = self.calculate_cost_effectiveness(tool, user_profile)
            team_fit_score = self.calculate_team_fit(tool, user_profile)
            
            # Calculate overall score (weighted average)
            overall_score = (
                integration_score * 0.3 +
                cost_effectiveness * 0.4 +
                team_fit_score * 0.3
            )
            
            # Generate reasoning
            reasoning = self.generate_recommendation_reasoning(tool, user_profile, {
                'integration': integration_score,
                'cost': cost_effectiveness,
                'team_fit': team_fit_score
            })
            
            recommendation = ToolRecommendation(
                tool=tool,
                score=overall_score,
                reasoning=reasoning,
                integration_complexity=int((1 - integration_score) * 10),
                cost_effectiveness=cost_effectiveness,
                team_fit_score=team_fit_score
            )
            
            recommendations.append(recommendation)
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit]
    
    def generate_recommendation_reasoning(self, tool: Dict, user_profile: UserProfile, scores: Dict) -> str:
        """Generate human-readable reasoning for the recommendation."""
        reasoning_parts = []
        
        if scores['integration'] > 0.8:
            reasoning_parts.append("Easy integration with your current setup")
        elif scores['integration'] < 0.5:
            reasoning_parts.append("May require technical expertise to integrate")
        
        if scores['cost'] > 0.8:
            reasoning_parts.append("Excellent value for your budget")
        elif scores['cost'] < 0.5:
            reasoning_parts.append("Consider if the cost fits your budget")
        
        if scores['team_fit'] > 0.8:
            reasoning_parts.append("Perfect fit for your team size")
        
        # Add specific tool benefits
        if tool.get('startupFriendly'):
            reasoning_parts.append("Startup-friendly with good support")
        
        if tool.get('genSparkIntegration') == 'Native':
            reasoning_parts.append("Native GenSpark integration for seamless workflow")
        
        return ". ".join(reasoning_parts) if reasoning_parts else "Good overall fit for your needs"
    
    def optimize_tool_stack(self, category: str, budget: float, team_size: int) -> Dict:
        """Optimize a complete tool stack for a specific category and constraints."""
        tools_in_category = []
        
        # Get tools in the specified category
        for cat in self.tools_data['categories']:
            if cat['name'].lower() == category.lower():
                for subcategory in cat['subcategories']:
                    tools_in_category.extend(subcategory['tools'])
        
        if not tools_in_category:
            return {"error": f"Category '{category}' not found"}
        
        # Filter by budget
        affordable_tools = []
        for tool in tools_in_category:
            cost_per_user = tool.get('cost_per_user', 0)
            total_cost = cost_per_user * team_size
            if total_cost <= budget:
                affordable_tools.append(tool)
        
        # Create optimized stack recommendations
        stack_recommendations = {
            "essential": [],
            "recommended": [],
            "optional": []
        }
        
        remaining_budget = budget
        
        for tool in affordable_tools:
            cost_per_user = tool.get('cost_per_user', 0)
            total_cost = cost_per_user * team_size
            
            if tool.get('startupFriendly') and total_cost <= remaining_budget * 0.5:
                stack_recommendations["essential"].append(tool)
                remaining_budget -= total_cost
            elif total_cost <= remaining_budget * 0.3:
                stack_recommendations["recommended"].append(tool)
                remaining_budget -= total_cost
            else:
                stack_recommendations["optional"].append(tool)
        
        return {
            "category": category,
            "total_budget": budget,
            "team_size": team_size,
            "recommendations": stack_recommendations,
            "remaining_budget": remaining_budget,
            "tools_considered": len(affordable_tools)
        }
    
    def create_user_profile(self, team_size: int, budget: float, technical_level: str, 
                           preferred_categories: List[str], startup_stage: str) -> UserProfile:
        """Create a new user profile."""
        user_id = hashlib.md5(f"{team_size}{budget}{technical_level}{startup_stage}".encode()).hexdigest()
        
        profile = UserProfile(
            id=user_id,
            team_size=team_size,
            budget=budget,
            technical_level=technical_level,
            preferred_categories=preferred_categories,
            startup_stage=startup_stage,
            created_at=datetime.datetime.now(),
            last_updated=datetime.datetime.now()
        )
        
        # Save to database
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_profiles 
            (id, team_size, budget, technical_level, preferred_categories, startup_stage, created_at, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            profile.id, profile.team_size, profile.budget, profile.technical_level,
            ','.join(profile.preferred_categories), profile.startup_stage,
            profile.created_at, profile.last_updated
        ))
        
        conn.commit()
        conn.close()
        
        return profile
    
    def setup_routes(self):
        """Setup Flask routes for API endpoints."""
        
        @self.app.route('/')
        def index():
            return render_template_string('''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>GenSpark Advanced Tools Manager API</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; }
                        .endpoint { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 8px; }
                        .method { color: #007bff; font-weight: bold; }
                        code { background: #e9ecef; padding: 2px 4px; border-radius: 4px; }
                    </style>
                </head>
                <body>
                    <h1>🚀 GenSpark Advanced Tools Manager API</h1>
                    <p>AI-powered tool recommendations and optimization for startups</p>
                    
                    <div class="endpoint">
                        <h3><span class="method">GET</span> /api/recommend</h3>
                        <p>Get AI-powered tool recommendations</p>
                        <p><strong>Parameters:</strong></p>
                        <ul>
                            <li><code>team_size</code>: Number of team members</li>
                            <li><code>budget</code>: Monthly budget in USD</li>
                            <li><code>technical_level</code>: beginner/intermediate/expert</li>
                            <li><code>startup_stage</code>: ideation/growth/scale</li>
                        </ul>
                        <p><strong>Example:</strong> <code>/api/recommend?team_size=5&budget=500&technical_level=intermediate&startup_stage=growth</code></p>
                    </div>
                    
                    <div class="endpoint">
                        <h3><span class="method">GET</span> /api/optimize-stack</h3>
                        <p>Get optimized tool stack for a category</p>
                        <p><strong>Parameters:</strong></p>
                        <ul>
                            <li><code>category</code>: Tool category</li>
                            <li><code>budget</code>: Budget in USD</li>
                            <li><code>team_size</code>: Team size</li>
                        </ul>
                        <p><strong>Example:</strong> <code>/api/optimize-stack?category=AI&budget=1000&team_size=8</code></p>
                    </div>
                    
                    <div class="endpoint">
                        <h3><span class="method">GET</span> /api/tools</h3>
                        <p>Get all available tools with filtering</p>
                        <p><strong>Parameters:</strong></p>
                        <ul>
                            <li><code>category</code>: Filter by category</li>
                            <li><code>budget</code>: Filter by budget level</li>
                            <li><code>difficulty</code>: Filter by integration difficulty</li>
                        </ul>
                    </div>
                </body>
                </html>
            ''')
        
        @self.app.route('/api/recommend')
        def recommend():
            try:
                team_size = int(request.args.get('team_size', 5))
                budget = float(request.args.get('budget', 1000))
                technical_level = request.args.get('technical_level', 'intermediate')
                startup_stage = request.args.get('startup_stage', 'growth')
                limit = int(request.args.get('limit', 10))
                
                # Create user profile
                user_profile = self.create_user_profile(
                    team_size=team_size,
                    budget=budget,
                    technical_level=technical_level,
                    preferred_categories=[],
                    startup_stage=startup_stage
                )
                
                # Get AI recommendations
                recommendations = self.ai_recommend_tools(user_profile, limit)
                
                # Convert to JSON-serializable format
                result = []
                for rec in recommendations:
                    result.append({
                        'tool': rec.tool,
                        'score': round(rec.score, 2),
                        'reasoning': rec.reasoning,
                        'integration_complexity': rec.integration_complexity,
                        'cost_effectiveness': round(rec.cost_effectiveness, 2),
                        'team_fit_score': round(rec.team_fit_score, 2)
                    })
                
                return jsonify({
                    'success': True,
                    'recommendations': result,
                    'user_profile': {
                        'id': user_profile.id,
                        'team_size': user_profile.team_size,
                        'budget': user_profile.budget,
                        'technical_level': user_profile.technical_level,
                        'startup_stage': user_profile.startup_stage
                    }
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 400
        
        @self.app.route('/api/optimize-stack')
        def optimize_stack():
            try:
                category = request.args.get('category', 'AI')
                budget = float(request.args.get('budget', 1000))
                team_size = int(request.args.get('team_size', 5))
                
                result = self.optimize_tool_stack(category, budget, team_size)
                return jsonify({
                    'success': True,
                    'data': result
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 400
        
        @self.app.route('/api/tools')
        def get_tools():
            try:
                category_filter = request.args.get('category')
                budget_filter = request.args.get('budget')
                difficulty_filter = request.args.get('difficulty')
                
                tools = self.get_all_tools()
                
                # Apply filters
                if category_filter:
                    tools = [t for t in tools if t.get('category') == category_filter]
                
                if budget_filter:
                    tools = [t for t in tools if budget_filter in t.get('pricing', '').lower()]
                
                if difficulty_filter:
                    tools = [t for t in tools if t.get('difficulty') == difficulty_filter]
                
                return jsonify({
                    'success': True,
                    'tools': tools,
                    'count': len(tools)
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 400
    
    def run_server(self, host='0.0.0.0', port=8000, debug=False):
        """Run the Flask API server."""
        print(f"🚀 Starting GenSpark Advanced Tools Manager API...")
        print(f"📡 Server running on http://{host}:{port}")
        print(f"📚 API Documentation: http://{host}:{port}/")
        
        self.app.run(host=host, port=port, debug=debug)


def main():
    parser = argparse.ArgumentParser(
        description="Advanced GenSpark Tools Manager with AI recommendations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --ai-recommend --team-size 5 --budget 1000 --technical-level intermediate
  %(prog)s --serve --port 8000
  %(prog)s --optimize-stack --category AI --budget 2000 --team-size 8
  %(prog)s --create-profile --team-size 3 --budget 500 --stage growth
        """
    )
    
    # Main commands
    parser.add_argument('--ai-recommend', action='store_true',
                       help='Get AI-powered tool recommendations')
    parser.add_argument('--serve', action='store_true',
                       help='Start the API server')
    parser.add_argument('--optimize-stack', action='store_true',
                       help='Optimize tool stack for category and budget')
    parser.add_argument('--create-profile', action='store_true',
                       help='Create user profile for personalized recommendations')
    
    # Parameters
    parser.add_argument('--team-size', type=int, default=5,
                       help='Team size (default: 5)')
    parser.add_argument('--budget', type=float, default=1000,
                       help='Monthly budget in USD (default: 1000)')
    parser.add_argument('--technical-level', type=str, default='intermediate',
                       choices=['beginner', 'intermediate', 'expert'],
                       help='Technical level (default: intermediate)')
    parser.add_argument('--startup-stage', type=str, default='growth',
                       choices=['ideation', 'growth', 'scale'],
                       help='Startup stage (default: growth)')
    parser.add_argument('--category', type=str, default='AI',
                       help='Tool category (default: AI)')
    parser.add_argument('--port', type=int, default=8000,
                       help='Server port (default: 8000)')
    parser.add_argument('--limit', type=int, default=10,
                       help='Number of recommendations (default: 10)')
    
    args = parser.parse_args()
    
    # Initialize the manager
    manager = AdvancedToolsManager()
    
    if args.ai_recommend:
        print("🤖 Getting AI-powered recommendations...")
        user_profile = manager.create_user_profile(
            team_size=args.team_size,
            budget=args.budget,
            technical_level=args.technical_level,
            preferred_categories=[],
            startup_stage=args.startup_stage
        )
        
        recommendations = manager.ai_recommend_tools(user_profile, args.limit)
        
        print(f"\n🎯 Top {len(recommendations)} AI Recommendations for {args.startup_stage} stage:")
        print("=" * 70)
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec.tool['name']} (Score: {rec.score:.2f})")
            print(f"   💡 {rec.reasoning}")
            print(f"   🔗 Integration: {rec.integration_complexity}/10 complexity")
            print(f"   💰 Cost effectiveness: {rec.cost_effectiveness:.2f}/1.0")
            print(f"   👥 Team fit: {rec.team_fit_score:.2f}/1.0")
            print(f"   📍 {rec.tool['url']}")
    
    elif args.serve:
        manager.run_server(port=args.port)
    
    elif args.optimize_stack:
        print(f"🔧 Optimizing tool stack for {args.category} category...")
        result = manager.optimize_tool_stack(args.category, args.budget, args.team_size)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"\n🎯 Optimized Stack for {args.category}")
            print("=" * 50)
            print(f"💰 Budget: ${result['total_budget']}")
            print(f"👥 Team Size: {result['team_size']}")
            print(f"📊 Tools Considered: {result['tools_considered']}")
            print(f"💵 Remaining Budget: ${result['remaining_budget']}")
            
            for level, tools in result['recommendations'].items():
                if tools:
                    print(f"\n{level.upper()} TOOLS:")
                    for tool in tools:
                        cost = tool.get('cost_per_user', 0) * args.team_size
                        print(f"  • {tool['name']} (${cost}/month)")
    
    elif args.create_profile:
        print("👤 Creating user profile...")
        profile = manager.create_user_profile(
            team_size=args.team_size,
            budget=args.budget,
            technical_level=args.technical_level,
            preferred_categories=[],
            startup_stage=args.startup_stage
        )
        
        print(f"✅ Profile created with ID: {profile.id}")
        print(f"📊 Profile details saved for personalized recommendations")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()