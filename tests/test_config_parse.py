#!/usr/bin/env python3
"""
Simple config parsing test that verifies precedence order without 
hardcoding expected values.

Tests:
1. Empty hardcoded → uses .env value
2. Non-empty hardcoded → uses hardcoded value
3. CLI argument → uses CLI value (highest priority)
"""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent / "src"))

from configParsing import build_config


def test_empty_vs_nonempty():
    """Test that empty hardcoded values are skipped, non-empty are used"""
    print("\n" + "="*70)
    print("TEST 1: Empty hardcoded vs non-empty hardcoded")
    print("="*70)
    
    env_content = "EMPTY_VAR=env_value_here\nNONEMPTY_VAR=will_be_overridden\n"
    tmp_env = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
    tmp_env.write(env_content)
    tmp_env.close()
    
    try:
        test_globals = {
            "EMPTY_VAR": "",               # Empty → should use .env
            "NONEMPTY_VAR": "hardcoded",  # Non-empty → should use hardcoded
        }
        
        with patch('sys.argv', ['test.py', '--env-file', tmp_env.name]):
            cfg = build_config(test_globals)
        
        print(f"\nScript declares:")
        print(f"  EMPTY_VAR = ''")
        print(f"  NONEMPTY_VAR = 'hardcoded'")
        print(f"\n.env provides:")
        print(f"  EMPTY_VAR=env_value_here")
        print(f"  NONEMPTY_VAR=will_be_overridden")
        
        # Test 1: Empty var should use .env
        r1 = cfg.get("EMPTY_VAR") == "env_value_here"
        print(f"\n✓ EMPTY_VAR uses .env value: {cfg.get('EMPTY_VAR')}" if r1 else f"✗ EMPTY_VAR should use .env, got: {cfg.get('EMPTY_VAR')}")
        
        # Test 2: Non-empty var should use hardcoded
        r2 = cfg.get("NONEMPTY_VAR") == "hardcoded"
        print(f"✓ NONEMPTY_VAR uses hardcoded: {cfg.get('NONEMPTY_VAR')}" if r2 else f"✗ NONEMPTY_VAR should use hardcoded, got: {cfg.get('NONEMPTY_VAR')}")
        
        return r1 and r2
    finally:
        Path(tmp_env.name).unlink()


def test_cli_overrides():
    """Test that CLI arguments override everything"""
    print("\n" + "="*70)
    print("TEST 2: CLI arguments override hardcoded")
    print("="*70)
    
    env_content = "SCOPES=scope_from_env\n"
    tmp_env = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
    tmp_env.write(env_content)
    tmp_env.close()
    
    try:
        test_globals = {
            "SCOPES": ["hard", "coded"],  # Non-empty hardcoded
        }
        
        # With CLI args
        with patch('sys.argv', ['test.py', '--scopes', 'from_cli_1', 'from_cli_2', '--env-file', tmp_env.name]):
            cfg = build_config(test_globals)
        
        print(f"\nScript has: SCOPES = ['hard', 'coded']")
        print(f".env has: SCOPES=scope_from_env")
        print(f"CLI has: --scopes from_cli_1 from_cli_2")
        print(f"\nActual result: {cfg.get('SCOPES')}")
        
        r = cfg.get("SCOPES") == ["from_cli_1", "from_cli_2"]
        print(f"✓ CLI arguments won (highest priority)" if r else f"✗ CLI should win over hardcoded and .env")
        return r
    finally:
        Path(tmp_env.name).unlink()


def test_list_types():
    """Test that empty and non-empty lists behave correctly"""
    print("\n" + "="*70)
    print("TEST 3: List type handling")
    print("="*70)
    
    env_content = "SCOPES=scope1 scope2 scope3\n"
    tmp_env = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
    tmp_env.write(env_content)
    tmp_env.close()
    
    try:
        test_globals = {
            "SCOPES": [],  # Empty list → should use .env
        }
        
        with patch('sys.argv', ['test.py', '--env-file', tmp_env.name]):
            cfg = build_config(test_globals)
        
        result = cfg.get("SCOPES")
        print(f"\nScript has: SCOPES = []")
        print(f".env has: SCOPES=scope1 scope2 scope3")
        print(f"Result: {result}")
        
        r = isinstance(result, list) and len(result) == 3 and result[0] == "scope1"
        print(f"✓ Empty list falls through to .env (parsed as list)" if r else f"✗ Should parse .env as list of scopes")
        return r
    finally:
        Path(tmp_env.name).unlink()


def test_bool_values():
    """Test that boolean values are handled correctly"""
    print("\n" + "="*70)
    print("TEST 4: Boolean value handling")
    print("="*70)
    
    env_content = "DEBUG=true\n"
    tmp_env = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
    tmp_env.write(env_content)
    tmp_env.close()
    
    try:
        test_globals = {
            "DEBUG": False,  # Boolean False is meaningful
        }
        
        with patch('sys.argv', ['test.py', '--env-file', tmp_env.name]):
            cfg = build_config(test_globals)
        
        result = cfg.get("DEBUG")
        print(f"\nScript has: DEBUG = False")
        print(f".env has: DEBUG=true")
        print(f"Result: {result}")
        
        r = result is False
        print(f"✓ Boolean False is respected (not overridden by .env)" if r else f"✗ Boolean False should be meaningful/respected")
        return r
    finally:
        Path(tmp_env.name).unlink()


if __name__ == "__main__":
    results = [
        ("Empty vs non-empty hardcoded", test_empty_vs_nonempty()),
        ("CLI overrides hardcoded", test_cli_overrides()),
        ("List type handling", test_list_types()),
        ("Boolean value handling", test_bool_values()),
    ]
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(p for _, p in results)
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    sys.exit(0 if all_passed else 1)
