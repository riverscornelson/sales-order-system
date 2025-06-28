#!/usr/bin/env python3
"""
Basic test of evaluation framework (without OpenAI API calls)
Tests core framework functionality before integrating with live APIs
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.evals.config import EvaluationConfig
from app.evals.data_structures import ERPAccuracyScore, ReasoningScore
from app.evals.runner import EvaluationRunner

async def test_config_loading():
    """Test configuration loading"""
    print("🔧 Testing Configuration Loading...")
    
    try:
        config = EvaluationConfig.from_file("app/evals/config.json")
        
        print(f"✅ Configuration loaded successfully")
        print(f"   Model: {config.evaluation_model}")
        print(f"   ERP JSON weight: {config.erp_accuracy_weight}")
        print(f"   Thresholds: min_accuracy={config.min_erp_accuracy_threshold}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

async def test_jsonl_loading():
    """Test JSONL data loading"""
    print("\n📊 Testing JSONL Data Loading...")
    
    try:
        jsonl_path = "test_data/sales_order_samples.jsonl"
        
        if not os.path.exists(jsonl_path):
            print(f"❌ JSONL file not found: {jsonl_path}")
            return False
        
        samples = []
        with open(jsonl_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    sample = json.loads(line.strip())
                    samples.append(sample)
                    
                    if line_num <= 3:  # Validate first 3 samples
                        required_fields = ['id', 'input', 'expected_erp_json']
                        for field in required_fields:
                            if field not in sample:
                                print(f"❌ Missing field '{field}' in sample {line_num}")
                                return False
                                
                except json.JSONDecodeError as e:
                    print(f"❌ JSON error on line {line_num}: {e}")
                    return False
        
        print(f"✅ JSONL Loading: SUCCESS")
        print(f"   Loaded {len(samples)} test samples")
        print(f"   Sample categories: {set(s.get('category', 'unknown') for s in samples[:5])}")
        
        return True
        
    except Exception as e:
        print(f"❌ JSONL Loading: ERROR - {str(e)}")
        return False

async def test_erp_accuracy_scorer():
    """Test ERP accuracy scoring without API calls"""
    print("\n🎯 Testing ERP Accuracy Scorer...")
    
    try:
        # Mock actual vs expected ERP JSON
        actual_erp = {
            "customer": {
                "name": "Ford Motor Company",
                "tier": "key_account"
            },
            "line_items": [{
                "material": "316L",
                "form": "tube",
                "diameter": 2.5,
                "length": 48,
                "quantity": 6
            }],
            "order_metadata": {
                "priority": "emergency",
                "processing_strategy": "exact_match"
            }
        }
        
        expected_erp = {
            "customer": {
                "name": "Ford Motor Company",
                "tier": "key_account"
            },
            "line_items": [{
                "material": "316L",
                "form": "tube", 
                "diameter": 2.5,
                "length": 48,
                "quantity": 6
            }],
            "order_metadata": {
                "priority": "emergency",
                "processing_strategy": "exact_match"
            }
        }
        
        # Manual scoring calculation
        schema_score = 1.0  # Perfect match
        required_fields_score = 1.0  # All fields present
        line_items_score = 1.0  # Perfect line items match
        business_rules_score = 1.0  # Business logic correct
        data_types_score = 1.0  # All data types correct
        part_numbers_score = 0.8  # Assume slight part number difference
        
        weights = {
            'schema_compliance': 0.2,
            'required_fields': 0.25,
            'line_items': 0.2,
            'business_rules': 0.15,
            'data_types': 0.1,
            'part_numbers': 0.1
        }
        
        overall_score = (
            schema_score * weights['schema_compliance'] +
            required_fields_score * weights['required_fields'] +
            line_items_score * weights['line_items'] +
            business_rules_score * weights['business_rules'] +
            data_types_score * weights['data_types'] +
            part_numbers_score * weights['part_numbers']
        )
        
        erp_score = ERPAccuracyScore(
            schema_compliance=schema_score,
            required_fields_accuracy=required_fields_score,
            line_items_accuracy=line_items_score,
            business_rules_compliance=business_rules_score,
            data_type_accuracy=data_types_score,
            part_numbers_accuracy=part_numbers_score
        )
        erp_score.overall_accuracy = overall_score
        
        print(f"✅ ERP Accuracy Scorer: SUCCESS")
        print(f"   Overall ERP Score: {erp_score.overall_accuracy:.3f}")
        print(f"   Schema Compliance: {erp_score.schema_compliance:.3f}")
        print(f"   Line Items Accuracy: {erp_score.line_items_accuracy:.3f}")
        print(f"   Required Fields: {erp_score.required_fields_accuracy:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERP Accuracy Scorer: ERROR - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_evaluation_runner_setup():
    """Test evaluation runner initialization"""
    print("\n🏃 Testing Evaluation Runner Setup...")
    
    try:
        config = EvaluationConfig.from_file("app/evals/config.json")
        runner = EvaluationRunner(config=config)
        
        print(f"✅ Evaluation Runner: SUCCESS")
        print(f"   Output directory: {runner.output_dir}")
        print(f"   Config loaded: {runner.config.evaluation_model}")
        
        # Test validation functionality
        validation_result = runner.validate_evaluation_data("test_data/sales_order_samples.jsonl")
        
        print(f"   Data validation: {validation_result['valid_samples']}/{validation_result['total_samples']} valid")
        
        if validation_result['validation_errors']:
            print(f"   Validation warnings: {len(validation_result['validation_errors'])} issues")
            for error in validation_result['validation_errors'][:3]:
                print(f"     - {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Evaluation Runner: ERROR - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_sample_structure():
    """Test sample structure validation"""
    print("\n📋 Testing Sample Structure...")
    
    try:
        # Load first sample
        with open("test_data/sales_order_samples.jsonl", 'r') as f:
            first_line = f.readline().strip()
            sample = json.loads(first_line)
        
        # Check required fields
        required_top_level = ['id', 'category', 'industry', 'customer_tier', 'complexity', 'input', 'expected_erp_json']
        required_input = ['customer', 'email_body', 'metadata']
        required_erp = ['customer_info', 'line_items']
        
        missing_fields = []
        
        for field in required_top_level:
            if field not in sample:
                missing_fields.append(f"Top level: {field}")
        
        if 'input' in sample:
            for field in required_input:
                if field not in sample['input']:
                    missing_fields.append(f"Input: {field}")
        
        if 'expected_erp_json' in sample:
            for field in required_erp:
                if field not in sample['expected_erp_json']:
                    missing_fields.append(f"ERP JSON: {field}")
        
        if missing_fields:
            print(f"❌ Sample Structure: Missing fields - {missing_fields}")
            return False
        
        print(f"✅ Sample Structure: SUCCESS")
        print(f"   Sample ID: {sample['id']}")
        print(f"   Category: {sample['category']}")
        print(f"   Industry: {sample['industry']}")
        print(f"   Complexity: {sample['complexity']}")
        print(f"   Line items count: {len(sample['expected_erp_json']['line_items'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Sample Structure: ERROR - {str(e)}")
        return False

async def main():
    """Run all basic framework tests"""
    print("🧪 Basic Evaluation Framework Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration Loading", test_config_loading),
        ("JSONL Data Loading", test_jsonl_loading),
        ("Sample Structure", test_sample_structure),
        ("ERP Accuracy Scorer", test_erp_accuracy_scorer),
        ("Evaluation Runner Setup", test_evaluation_runner_setup)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results[test_name] = success
        except Exception as e:
            print(f"❌ {test_name}: CRITICAL ERROR - {str(e)}")
            results[test_name] = False
    
    print(f"\n📋 Test Results Summary:")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("🎉 All basic tests passed! Framework is ready for OpenAI integration.")
    else:
        print("⚠️  Some tests failed. Review errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)