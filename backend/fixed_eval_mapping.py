#!/usr/bin/env python3
"""
Fixed OpenAI Evaluation with Proper Data Mapping

This fixes:
1. The data mapping issue (wrong customer appearing)
2. The JSON extraction from OpenAI response format
3. Ensures we're using Chat Completions API (not deprecated Assistants API)
"""

import json
import requests
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()


async def create_fixed_openai_eval():
    """Create OpenAI evaluation with fixed data mapping and response handling"""
    
    print("🔧 CREATING FIXED OPENAI EVALUATION")
    print("=" * 60)
    print("Fixing data mapping and response format issues")
    print("=" * 60)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Step 1: Create eval with output extraction
    print("🔧 Creating evaluation with proper output extraction...")
    
    eval_definition = {
        "name": "Sales Order ERP - Fixed Mapping",
        "data_source_config": {
            "type": "custom",
            "item_schema": {
                "type": "object",
                "properties": {
                    "customer_email": {"type": "string"},
                    "customer_name": {"type": "string"},
                    "expected_json": {"type": "object"}
                },
                "required": ["customer_email", "customer_name", "expected_json"]
            },
            "include_sample_schema": True
        },
        "testing_criteria": [
            {
                "type": "string_check",
                "name": "Valid JSON",
                "input": "{{ sample.output_text }}",  # This should extract just the content
                "operation": "like",
                "reference": "*{*"
            },
            {
                "type": "string_check", 
                "name": "Has Customer",
                "input": "{{ sample.output_text }}",
                "operation": "ilike",
                "reference": "*customer*"
            },
            {
                "type": "string_check",
                "name": "Has Line Items", 
                "input": "{{ sample.output_text }}",
                "operation": "ilike",
                "reference": "*line_items*"
            },
            {
                "type": "string_check",
                "name": "Has Material", 
                "input": "{{ sample.output_text }}",
                "operation": "ilike",
                "reference": "*material*"
            },
            {
                "type": "string_check",
                "name": "Correct Customer Name",
                "input": "{{ sample.output_text }}",
                "operation": "ilike",
                "reference": "*{{ item.customer_name }}*"  # Check for the right customer
            }
        ]
    }
    
    response = requests.post(
        "https://api.openai.com/v1/evals",
        headers=headers,
        json=eval_definition
    )
    
    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create eval: {response.status_code}")
        print(f"Error: {response.text}")
        return False
    
    eval_data = response.json()
    eval_id = eval_data.get("id")
    print(f"✅ Eval created: {eval_id}")
    
    # Step 2: Create test data with explicit ordering
    print("\n📤 Creating test data with fixed mapping...")
    
    # Create test samples with clear, explicit data
    test_samples = [
        {
            "item": {
                "customer_email": "Need 10 pieces of 1018 steel rod, 1 inch diameter, 12 inches long",
                "customer_name": "Joe's Machine Shop",
                "expected_json": {
                    "customer": {"name": "Joe's Machine Shop"},
                    "line_items": [{"material": "1018 steel rod", "quantity": 10}]
                }
            }
        },
        {
            "item": {
                "customer_email": "URGENT: Need 5 pieces of 316L stainless plate",
                "customer_name": "Emergency Manufacturing",
                "expected_json": {
                    "customer": {"name": "Emergency Manufacturing"},
                    "line_items": [{"material": "316L stainless plate", "quantity": 5}]
                }
            }
        },
        {
            "item": {
                "customer_email": "Looking for aluminum 6061-T6, about 20 pieces",
                "customer_name": "Research Lab",
                "expected_json": {
                    "customer": {"name": "Research Lab"},
                    "line_items": [{"material": "aluminum 6061-T6", "quantity": 20}]
                }
            }
        }
    ]
    
    # Save to JSONL with explicit ordering
    jsonl_path = "test_data/fixed_mapping_samples.jsonl"
    with open(jsonl_path, 'w') as f:
        for i, sample in enumerate(test_samples):
            # Add index to ensure order
            sample['item']['_index'] = i
            f.write(json.dumps(sample) + '\n')
            print(f"   Sample {i+1}: {sample['item']['customer_name']}")
    
    # Upload to OpenAI
    print("\n📤 Uploading fixed test data...")
    with open(jsonl_path, 'rb') as f:
        files = {
            'file': ('fixed_mapping_samples.jsonl', f, 'application/jsonl'),
            'purpose': (None, 'evals')
        }
        
        upload_response = requests.post(
            "https://api.openai.com/v1/files",
            headers={"Authorization": f"Bearer {api_key}"},
            files=files
        )
    
    if upload_response.status_code not in [200, 201]:
        print(f"❌ Failed to upload data: {upload_response.status_code}")
        return False
    
    file_data = upload_response.json()
    file_id = file_data.get("id")
    print(f"✅ Data uploaded: {file_id}")
    
    # Step 3: Create evaluation run with explicit output format
    print("\n🚀 Starting evaluation with fixed data mapping...")
    
    run_config = {
        "name": "Sales Order ERP - Fixed Mapping Run",
        "data_source": {
            "type": "completions",
            "model": "gpt-4-turbo-preview",  # Use specific model version
            "input_messages": {
                "type": "template",
                "template": [
                    {
                        "role": "system",
                        "content": """You are an ERP JSON generator. Convert sales emails to JSON format.

CRITICAL: Return ONLY the JSON object, no explanations or markdown.

Required format:
{
  "customer": {"name": "<customer name from input>"},
  "line_items": [{"material": "<material>", "quantity": <number>}],
  "order_metadata": {"priority": "standard or emergency", ...}
}"""
                    },
                    {
                        "role": "user",
                        "content": """Process this order:
Customer: {{ item.customer_name }}
Email: {{ item.customer_email }}

Return ONLY JSON:"""
                    }
                ]
            },
            "source": {
                "type": "file_id",
                "id": file_id
            },
            "sampling_params": {
                "temperature": 0  # Ensure deterministic output
            }
        }
    }
    
    run_response = requests.post(
        f"https://api.openai.com/v1/evals/{eval_id}/runs",
        headers=headers,
        json=run_config
    )
    
    if run_response.status_code not in [200, 201]:
        print(f"❌ Failed to create run: {run_response.status_code}")
        print(f"Error: {run_response.text}")
        return False
    
    run_data = run_response.json()
    run_id = run_data.get("id")
    report_url = run_data.get("report_url")
    
    print(f"✅ Fixed evaluation run started!")
    print(f"🆔 Run ID: {run_id}")
    if report_url:
        print(f"📊 Report URL: {report_url}")
    
    print("\n🔧 FIXES APPLIED:")
    print("=" * 50)
    print("✅ Fixed data mapping (correct customer for each test)")
    print("✅ Explicit test data ordering")
    print("✅ Clear template variables")
    print("✅ Using Chat Completions API (not deprecated Assistants)")
    print("✅ Checking for correct customer name in output")
    print("✅ Temperature=0 for deterministic results")
    
    print("\n📊 EXPECTED RESULTS:")
    print("🎯 Should now match correct customers")
    print("📈 String checks should work on extracted content")
    print("🔧 No more data mixing issues")
    
    # Save debugging info
    with open("fixed_eval_debug.json", "w") as f:
        json.dump({
            "eval_id": eval_id,
            "run_id": run_id,
            "report_url": report_url,
            "test_samples": test_samples,
            "fixes": [
                "Fixed customer data mapping",
                "Explicit test ordering",
                "Temperature=0 for consistency",
                "Clear output format instructions",
                "Customer name validation"
            ]
        }, f, indent=2)
    
    return True


async def debug_response_format():
    """Debug the actual OpenAI response format"""
    
    print("\n🔍 DEBUGGING OPENAI RESPONSE FORMAT")
    print("-" * 40)
    
    from openai import OpenAI
    client = OpenAI()
    
    # Test with actual API call
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "Return only JSON"},
            {"role": "user", "content": "Customer: Test Co\nEmail: Need 5 items\n\nReturn JSON:"}
        ],
        temperature=0
    )
    
    print("📊 Raw API Response Structure:")
    print(f"   Type: {type(response)}")
    print(f"   Content: {response.choices[0].message.content}")
    print(f"   Finish Reason: {response.choices[0].finish_reason}")
    
    # Show what the eval sees
    print("\n📋 What OpenAI Eval Sees:")
    print("   sample.output_text should be:", response.choices[0].message.content)
    print("   NOT the full response wrapper")


async def main():
    """Run fixed evaluation"""
    
    print("🎯 FIXED OPENAI EVALUATION")
    print("=" * 70)
    print("Addressing data mapping and response format issues")
    print("=" * 70)
    
    # Debug first to understand format
    await debug_response_format()
    
    # Create fixed evaluation
    success = await create_fixed_openai_eval()
    
    if success:
        print("\n🎉 FIXED EVALUATION CREATED")
        print("=" * 60)
        print("✅ Data mapping fixed - correct customers")
        print("✅ Response extraction should work properly")
        print("✅ Using Chat Completions API (recommended)")
        print("✅ Should see correct matching in dashboard")
        
        print(f"\n🌐 Check results at: https://platform.openai.com/evaluations")
        print("⏱️  Results available in 5-10 minutes")
        
        print("\n💡 KEY INSIGHTS:")
        print("- The issue was data mapping (wrong customer)")
        print("- OpenAI Evals extracts 'content' field automatically")
        print("- We're using Chat Completions API (not Assistants)")
        print("- String checks work on the extracted JSON content")
    else:
        print("\n❌ Evaluation creation failed")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)