#!/usr/bin/env python3
"""
GenSpark Awesome Startup Tools Finder

A tool to help entrepreneurs discover the perfect tools for their startup stage,
budget, and requirements. Built specifically for the GenSpark ecosystem.

Usage:
    python tools_finder.py --stage growth --budget free
    python tools_finder.py --category ai --integration easy
    python tools_finder.py --search "analytics"
"""

import json
import argparse
from typing import List, Dict, Optional
import sys

class StartupToolsFinder:
    def __init__(self, data_file: str = 'tools-data.json'):
        """Initialize the tools finder with data from JSON file."""
        try:
            with open(data_file, 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            print(f"Error: {data_file} not found. Please ensure it exists in the current directory.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: {data_file} is not valid JSON.")
            sys.exit(1)
    
    def get_tools_by_category(self, category_name: str) -> List[Dict]:
        """Get all tools in a specific category."""
        tools = []
        for category in self.data['categories']:
            if category['name'].lower() == category_name.lower():
                for subcategory in category['subcategories']:
                    tools.extend(subcategory['tools'])
        return tools
    
    def get_tools_by_stage(self, stage: str) -> List[str]:
        """Get recommended tools for a specific startup stage."""
        for stage_data in self.data['startupStages']:
            if stage_data['stage'].lower() == stage.lower():
                return stage_data['recommendedTools']
        return []
    
    def search_tools(self, query: str) -> List[Dict]:
        """Search for tools containing the query in name or description."""
        results = []
        query = query.lower()
        
        for category in self.data['categories']:
            for subcategory in category['subcategories']:
                for tool in subcategory['tools']:
                    if (query in tool['name'].lower() or 
                        query in tool['description'].lower() or
                        query in tool.get('tags', [])):
                        results.append(tool)
        
        return results
    
    def filter_by_budget(self, budget_type: str) -> List[Dict]:
        """Filter tools by budget type (free, freemium, paid)."""
        results = []
        budget_type = budget_type.lower()
        
        for category in self.data['categories']:
            for subcategory in category['subcategories']:
                for tool in subcategory['tools']:
                    pricing = tool.get('pricing', '').lower()
                    if (budget_type == 'free' and pricing == 'free') or \
                       (budget_type == 'freemium' and 'freemium' in pricing) or \
                       (budget_type == 'paid' and pricing not in ['free', 'freemium']):
                        results.append(tool)
        
        return results
    
    def filter_by_integration_difficulty(self, difficulty: str) -> List[Dict]:
        """Filter tools by integration difficulty."""
        results = []
        difficulty = difficulty.lower()
        
        for category in self.data['categories']:
            for subcategory in category['subcategories']:
                for tool in subcategory['tools']:
                    tool_difficulty = tool.get('difficulty', '').lower()
                    if tool_difficulty == difficulty:
                        results.append(tool)
        
        return results
    
    def get_startup_friendly_tools(self) -> List[Dict]:
        """Get all tools marked as startup-friendly."""
        results = []
        
        for category in self.data['categories']:
            for subcategory in category['subcategories']:
                for tool in subcategory['tools']:
                    if tool.get('startupFriendly', False):
                        results.append(tool)
        
        return results
    
    def display_tools(self, tools: List[Dict], title: str = "Tools"):
        """Display tools in a formatted manner."""
        if not tools:
            print(f"\n❌ No tools found for: {title}")
            return
        
        print(f"\n🎯 {title}")
        print("=" * 50)
        
        for i, tool in enumerate(tools, 1):
            print(f"\n{i}. {tool['name']}")
            print(f"   📍 {tool['url']}")
            print(f"   📝 {tool['description']}")
            print(f"   💰 {tool.get('pricing', 'N/A')}")
            print(f"   🔗 GenSpark Integration: {tool.get('genSparkIntegration', 'N/A')}")
            print(f"   📊 Difficulty: {tool.get('difficulty', 'N/A')}")
            
            if tool.get('startupFriendly'):
                print("   ✅ Startup Friendly")
    
    def display_checklist(self, stage: str):
        """Display the getting started checklist for a specific stage."""
        checklist = self.data.get('gettingStartedChecklist', {})
        
        for week, data in checklist.items():
            if data['name'].lower() == stage.lower():
                print(f"\n📋 {data['name']} Stage Checklist")
                print("=" * 40)
                for i, task in enumerate(data['tasks'], 1):
                    print(f"{i}. {task}")
                return
        
        print(f"\n❌ Stage '{stage}' not found in checklist.")


def main():
    parser = argparse.ArgumentParser(
        description="Find the perfect startup tools for your GenSpark journey",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --stage ideation                    # Get tools for ideation stage
  %(prog)s --category ai                       # Get AI/ML tools
  %(prog)s --search analytics                  # Search for analytics tools
  %(prog)s --budget free                       # Get free tools only
  %(prog)s --integration easy                # Get easy-to-integrate tools
  %(prog)s --checklist foundation            # Show foundation stage checklist
        """
    )
    
    # Main filters
    parser.add_argument('--stage', type=str, 
                       help='Get tools for specific startup stage (ideation/growth/scale)')
    parser.add_argument('--category', type=str,
                       help='Get tools for specific category (ai/analytics/marketing/etc)')
    parser.add_argument('--search', type=str,
                       help='Search for tools by keyword')
    parser.add_argument('--budget', type=str, choices=['free', 'freemium', 'paid'],
                       help='Filter by budget type')
    parser.add_argument('--integration', type=str, choices=['easy', 'intermediate', 'hard'],
                       help='Filter by integration difficulty')
    parser.add_argument('--startup-friendly', action='store_true',
                       help='Show only startup-friendly tools')
    parser.add_argument('--checklist', type=str,
                       help='Show getting started checklist for a stage')
    
    # Output options
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    parser.add_argument('--count', action='store_true',
                       help='Only show count of results')
    
    args = parser.parse_args()
    
    # Initialize finder
    finder = StartupToolsFinder()
    
    # Handle checklist request
    if args.checklist:
        finder.display_checklist(args.checklist)
        return
    
    # Collect results based on filters
    results = []
    
    if args.stage:
        tool_names = finder.get_tools_by_stage(args.stage)
        print(f"\n🎯 Recommended tools for {args.stage.upper()} stage:")
        for name in tool_names:
            print(f"  • {name}")
        return
    
    if args.search:
        results = finder.search_tools(args.search)
    elif args.category:
        results = finder.get_tools_by_category(args.category)
    elif args.budget:
        results = finder.filter_by_budget(args.budget)
    elif args.integration:
        results = finder.filter_by_integration_difficulty(args.integration)
    elif args.startup_friendly:
        results = finder.get_startup_friendly_tools()
    else:
        # Show all tools if no filter specified
        for category in finder.data['categories']:
            for subcategory in category['subcategories']:
                results.extend(subcategory['tools'])
    
    # Display results
    if args.count:
        print(f"\n📊 Found {len(results)} tools matching your criteria")
    elif args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        if args.search:
            title = f"Search results for '{args.search}'"
        elif args.category:
            title = f"Tools in {args.category.title()} category"
        elif args.budget:
            title = f"{args.budget.title()} tools"
        elif args.integration:
            title = f"{args.integration.title()} integration tools"
        elif args.startup_friendly:
            title = "Startup-friendly tools"
        else:
            title = "All available tools"
        
        finder.display_tools(results, title)


if __name__ == "__main__":
    main()