#!/usr/bin/env python3
"""
Bill Parser - Extract utility bill information using LLM vision
Uses Gemini 2.5 Flash (free tier) to parse PDF/image bills
"""

import os
import sys
import json
import base64
from pathlib import Path
from typing import Dict, Optional

def parse_bill_with_gemini(image_path: str, utility_type: str) -> Dict:
    """
    Parse utility bill using Google Gemini 2.5 Flash

    Args:
        image_path: Path to bill image/PDF
        utility_type: Type of utility ('water', 'electricity', 'gas')

    Returns:
        Dict with extracted bill information
    """
    try:
        import google.generativeai as genai
        from PIL import Image

        # Configure Gemini
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return {'error': 'GOOGLE_API_KEY not set'}

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Load image
        img = Image.open(image_path)

        # Create utility-specific prompt
        prompts = {
            'water': """
Analyze this water utility bill and extract the following information in JSON format:

{
  "account_number": "customer account number",
  "service_address": "service address",
  "billing_period_start": "YYYY-MM-DD",
  "billing_period_end": "YYYY-MM-DD",
  "billing_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD",
  "current_reading": "current meter reading in m³",
  "previous_reading": "previous meter reading in m³",
  "usage_m3": "water usage in cubic meters",
  "water_rate": "rate per m³",
  "wastewater_rate": "wastewater rate per m³",
  "stormwater_rate": "stormwater rate per m³",
  "fixed_charge": "monthly fixed/service charge",
  "total_amount": "total bill amount",
  "provider": "utility provider name",
  "notes": "any important notes or rate changes mentioned"
}

Only extract information that is clearly visible in the bill. Use null for missing information.
Return ONLY the JSON object, no other text.
""",
            'electricity': """
Analyze this electricity utility bill and extract the following information in JSON format:

{
  "account_number": "customer account number",
  "service_address": "service address",
  "billing_period_start": "YYYY-MM-DD",
  "billing_period_end": "YYYY-MM-DD",
  "billing_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD",
  "total_usage_kwh": "total usage in kWh",
  "off_peak_usage": "off-peak usage in kWh",
  "mid_peak_usage": "mid-peak usage in kWh",
  "on_peak_usage": "on-peak usage in kWh",
  "off_peak_rate": "off-peak rate in cents per kWh",
  "mid_peak_rate": "mid-peak rate in cents per kWh",
  "on_peak_rate": "on-peak rate in cents per kWh",
  "delivery_charge": "delivery charge amount",
  "regulatory_charge": "regulatory charge amount",
  "hst": "HST amount",
  "oer_rebate": "Ontario Electricity Rebate amount (if any)",
  "total_amount": "total bill amount",
  "provider": "utility provider name (e.g., Hydro One)",
  "rate_plan": "rate plan (e.g., Time-of-Use)",
  "notes": "any important notes or rate changes mentioned"
}

Only extract information that is clearly visible in the bill. Use null for missing information.
Return ONLY the JSON object, no other text.
""",
            'gas': """
Analyze this natural gas utility bill and extract the following information in JSON format:

{
  "account_number": "customer account number",
  "service_address": "service address",
  "billing_period_start": "YYYY-MM-DD",
  "billing_period_end": "YYYY-MM-DD",
  "billing_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD",
  "current_reading": "current meter reading in m³",
  "previous_reading": "previous meter reading in m³",
  "usage_m3": "gas usage in cubic meters",
  "gas_supply_rate": "gas supply rate in cents per m³",
  "delivery_rate": "delivery rate in cents per m³",
  "transportation_rate": "transportation rate in cents per m³",
  "customer_charge": "monthly customer charge",
  "carbon_charge": "carbon charge amount (if any)",
  "total_amount": "total bill amount",
  "provider": "utility provider name (e.g., Enbridge Gas)",
  "rate_zone": "rate zone (e.g., Rate 1 - EGD)",
  "notes": "any important notes or rate changes mentioned"
}

Only extract information that is clearly visible in the bill. Use null for missing information.
Return ONLY the JSON object, no other text.
"""
        }

        prompt = prompts.get(utility_type, prompts['water'])

        # Generate response
        response = model.generate_content([prompt, img])

        # Parse JSON from response
        response_text = response.text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            # Extract JSON from code block
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1])  # Remove first and last line

        # Parse JSON
        extracted_data = json.loads(response_text)

        # Track API usage
        api_usage = {
            'input_tokens': response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
            'output_tokens': response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
            'total_tokens': response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0,
            'model': 'gemini-2.0-flash-exp'
        }

        return {
            'status': 'success',
            'extracted': extracted_data,
            'api_usage': api_usage,
            'utility_type': utility_type,
            'source_file': os.path.basename(image_path)
        }

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}", file=sys.stderr)
        print(f"Response text: {response_text}", file=sys.stderr)
        return {
            'error': f'Failed to parse JSON response: {str(e)}',
            'raw_response': response_text
        }
    except Exception as e:
        print(f"❌ Bill parsing error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def save_bill_data(bill_data: Dict, config_path: str = 'config/pricing.json'):
    """
    Save extracted bill data to pricing configuration

    Args:
        bill_data: Extracted bill information
        config_path: Path to pricing config file
    """
    try:
        # Load existing config
        with open(config_path, 'r') as f:
            config = json.load(f)

        utility_type = bill_data.get('utility_type')
        extracted = bill_data.get('extracted', {})

        # Update account number
        if 'utility_accounts' in config and utility_type in config['utility_accounts']:
            if extracted.get('account_number'):
                config['utility_accounts'][utility_type]['account_number'] = extracted['account_number']
            if extracted.get('provider'):
                config['utility_accounts'][utility_type]['provider'] = extracted['provider']

        # Update rates based on utility type
        if 'utility_rates' in config and utility_type in config['utility_rates']:
            if utility_type == 'water':
                if extracted.get('water_rate'):
                    config['utility_rates']['water']['volumetric_rate']['water'] = float(extracted['water_rate'])
                if extracted.get('wastewater_rate'):
                    config['utility_rates']['water']['volumetric_rate']['wastewater'] = float(extracted['wastewater_rate'])
                if extracted.get('fixed_charge'):
                    config['utility_rates']['water']['fixed_charges']['monthly_service_charge'] = float(extracted['fixed_charge'])

            elif utility_type == 'electricity':
                if extracted.get('off_peak_rate'):
                    config['utility_rates']['electricity']['time_of_use_rates']['off_peak']['rate'] = float(extracted['off_peak_rate'])
                if extracted.get('mid_peak_rate'):
                    config['utility_rates']['electricity']['time_of_use_rates']['mid_peak']['rate'] = float(extracted['mid_peak_rate'])
                if extracted.get('on_peak_rate'):
                    config['utility_rates']['electricity']['time_of_use_rates']['on_peak']['rate'] = float(extracted['on_peak_rate'])

            elif utility_type == 'gas':
                if extracted.get('gas_supply_rate'):
                    config['utility_rates']['natural_gas']['gas_supply']['total_effective_rate'] = float(extracted['gas_supply_rate'])
                if extracted.get('delivery_rate'):
                    config['utility_rates']['natural_gas']['delivery_charges']['volumetric_charge'] = float(extracted['delivery_rate'])
                if extracted.get('customer_charge'):
                    config['utility_rates']['natural_gas']['fixed_charges']['monthly_customer_charge'] = float(extracted['customer_charge'])

        # Add to bill uploads history
        if 'bill_uploads' not in config:
            config['bill_uploads'] = {}
        if utility_type not in config['bill_uploads']:
            config['bill_uploads'][utility_type] = []

        config['bill_uploads'][utility_type].append({
            'uploaded_at': bill_data.get('uploaded_at'),
            'source_file': bill_data.get('source_file'),
            'billing_period': f"{extracted.get('billing_period_start')} to {extracted.get('billing_period_end')}",
            'total_amount': extracted.get('total_amount'),
            'usage': extracted.get('usage_m3') or extracted.get('total_usage_kwh')
        })

        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✅ Saved bill data to {config_path}", file=sys.stderr)
        return True

    except Exception as e:
        print(f"❌ Error saving bill data: {e}", file=sys.stderr)
        return False


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python bill_parser.py <image_path> <utility_type>")
        sys.exit(1)

    result = parse_bill_with_gemini(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2))
