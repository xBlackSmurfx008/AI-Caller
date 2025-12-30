#!/usr/bin/env python3
"""Verify OpenAI integration compliance and tool schemas."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.openai_client import validate_tools, validate_tool_schema
from src.agent.tools import TOOLS


def main():
    """Verify OpenAI compliance."""
    print("🔍 Verifying OpenAI Integration Compliance...\n")
    
    # Validate all tools
    print("1. Validating tool schemas...")
    is_valid, error_msg = validate_tools(TOOLS)
    if is_valid:
        print(f"   ✅ All {len(TOOLS)} tools validated successfully")
    else:
        print(f"   ❌ Tool validation failed: {error_msg}")
        return 1
    
    # Validate individual tools
    print("\n2. Validating individual tool schemas...")
    for i, tool in enumerate(TOOLS):
        tool_name = tool.get("function", {}).get("name", f"tool_{i}")
        is_valid = validate_tool_schema(tool)
        if is_valid:
            print(f"   ✅ {tool_name}")
        else:
            print(f"   ❌ {tool_name} - Invalid schema")
            return 1
    
    # Check for required fields
    print("\n3. Checking required fields...")
    all_valid = True
    for tool in TOOLS:
        function = tool.get("function", {})
        name = function.get("name")
        description = function.get("description")
        parameters = function.get("parameters", {})
        
        if not name:
            print(f"   ❌ Tool missing 'name': {tool}")
            all_valid = False
        if not description:
            print(f"   ⚠️  Tool '{name}' missing description")
        if parameters.get("type") != "object":
            print(f"   ❌ Tool '{name}' parameters type must be 'object'")
            all_valid = False
    
    if all_valid:
        print("   ✅ All required fields present")
    else:
        return 1
    
    # Check for duplicate names
    print("\n4. Checking for duplicate tool names...")
    names = [tool.get("function", {}).get("name") for tool in TOOLS]
    duplicates = [name for name in names if names.count(name) > 1]
    if duplicates:
        print(f"   ❌ Duplicate tool names: {duplicates}")
        return 1
    else:
        print("   ✅ No duplicate tool names")
    
    print("\n✅ All compliance checks passed!")
    print(f"\n📊 Summary:")
    print(f"   - Total tools: {len(TOOLS)}")
    print(f"   - All schemas valid: ✅")
    print(f"   - All required fields present: ✅")
    print(f"   - No duplicates: ✅")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

