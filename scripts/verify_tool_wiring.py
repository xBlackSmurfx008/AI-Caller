#!/usr/bin/env python3
"""Verify all tools are properly wired and connected."""

import sys
import os
import inspect
from typing import Dict, Any, List, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.tools import TOOLS, TOOL_HANDLERS
from src.utils.openai_client import validate_tool_schema


def get_function_signature(func) -> Dict[str, Any]:
    """Extract function signature information."""
    sig = inspect.signature(func)
    params = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        param_info = {
            "name": param_name,
            "default": param.default if param.default != inspect.Parameter.empty else None,
            "annotation": str(param.annotation) if param.annotation != inspect.Parameter.empty else None,
        }
        params[param_name] = param_info
        
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
    
    return {
        "parameters": params,
        "required": required,
    }


def verify_tool_wiring() -> Tuple[bool, List[str]]:
    """Verify all tools are properly wired."""
    errors = []
    warnings = []
    
    print("🔍 Verifying Tool Wiring...\n")
    
    # 1. Check all tools in TOOLS have handlers
    print("1. Checking tool definitions have handlers...")
    tool_names = set()
    for tool in TOOLS:
        tool_name = tool.get("function", {}).get("name")
        if not tool_name:
            errors.append("Tool missing 'name' field")
            continue
        
        tool_names.add(tool_name)
        
        if tool_name not in TOOL_HANDLERS:
            errors.append(f"Tool '{tool_name}' defined in TOOLS but missing from TOOL_HANDLERS")
        else:
            print(f"   ✅ {tool_name}")
    
    # 2. Check all handlers have tool definitions
    print("\n2. Checking handlers have tool definitions...")
    handler_names = set(TOOL_HANDLERS.keys())
    for handler_name in handler_names:
        if handler_name not in tool_names:
            errors.append(f"Handler '{handler_name}' in TOOL_HANDLERS but missing from TOOLS")
        else:
            print(f"   ✅ {handler_name}")
    
    # 3. Check for mismatches
    print("\n3. Checking for mismatches...")
    missing_handlers = tool_names - handler_names
    extra_handlers = handler_names - tool_names
    
    if missing_handlers:
        errors.append(f"Tools without handlers: {missing_handlers}")
    if extra_handlers:
        errors.append(f"Handlers without tools: {extra_handlers}")
    
    if not missing_handlers and not extra_handlers:
        print("   ✅ All tools and handlers match")
    
    # 4. Verify tool schemas match function signatures
    print("\n4. Verifying tool schemas match function signatures...")
    for tool in TOOLS:
        tool_name = tool.get("function", {}).get("name")
        if not tool_name or tool_name not in TOOL_HANDLERS:
            continue
        
        handler = TOOL_HANDLERS[tool_name]
        schema_params = tool.get("function", {}).get("parameters", {}).get("properties", {})
        schema_required = tool.get("function", {}).get("parameters", {}).get("required", [])
        
        # Get function signature
        func_sig = get_function_signature(handler)
        func_params = func_sig["parameters"]
        func_required = func_sig["required"]
        
        # Check parameters match
        schema_param_names = set(schema_params.keys())
        func_param_names = set(func_params.keys())
        
        # Remove 'self' if it's a method (shouldn't be, but check)
        func_param_names.discard("self")
        
        missing_in_schema = func_param_names - schema_param_names
        missing_in_func = schema_param_names - func_param_names
        
        if missing_in_schema:
            warnings.append(f"Tool '{tool_name}': Function parameters not in schema: {missing_in_schema}")
        if missing_in_func:
            warnings.append(f"Tool '{tool_name}': Schema parameters not in function: {missing_in_func}")
        
        # Check required fields match
        schema_required_set = set(schema_required)
        func_required_set = set(func_required)
        
        if schema_required_set != func_required_set:
            warnings.append(
                f"Tool '{tool_name}': Required fields mismatch. "
                f"Schema: {schema_required_set}, Function: {func_required_set}"
            )
        
        if not missing_in_schema and not missing_in_func and schema_required_set == func_required_set:
            print(f"   ✅ {tool_name} - Schema matches function signature")
        else:
            print(f"   ⚠️  {tool_name} - Schema/function mismatch (see warnings)")
    
    # 5. Verify tool schemas are valid
    print("\n5. Validating tool schemas...")
    for tool in TOOLS:
        tool_name = tool.get("function", {}).get("name", "unknown")
        if validate_tool_schema(tool):
            print(f"   ✅ {tool_name}")
        else:
            errors.append(f"Tool '{tool_name}' has invalid schema")
            print(f"   ❌ {tool_name}")
    
    # 6. Check tool descriptions
    print("\n6. Checking tool descriptions...")
    for tool in TOOLS:
        tool_name = tool.get("function", {}).get("name", "unknown")
        description = tool.get("function", {}).get("description", "")
        
        if not description or len(description.strip()) < 10:
            warnings.append(f"Tool '{tool_name}' has short or missing description")
            print(f"   ⚠️  {tool_name} - Description too short")
        else:
            print(f"   ✅ {tool_name}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"   - {error}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"   - {warning}")
    
    if not errors and not warnings:
        print("\n✅ All tool wiring checks passed!")
        print(f"\n📊 Statistics:")
        print(f"   - Total tools: {len(TOOLS)}")
        print(f"   - Total handlers: {len(TOOL_HANDLERS)}")
        print(f"   - All tools wired: ✅")
        print(f"   - All schemas valid: ✅")
        print(f"   - All descriptions present: ✅")
    
    return len(errors) == 0, errors + warnings


def main():
    """Main verification function."""
    success, issues = verify_tool_wiring()
    
    if success:
        return 0
    else:
        print(f"\n❌ Verification failed with {len(issues)} issue(s)")
        return 1


if __name__ == "__main__":
    sys.exit(main())

