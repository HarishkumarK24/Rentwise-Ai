import re
from typing import Dict, Any, Tuple

# Official Indian Income Tax Act Section 10(13A) Rule 2A & CBDT Circular guidelines
# Threshold for mandatory PAN of Landlord: Rs. 1,00,000 per annum (Rs. 8,333.33/month)
DEFAULT_ANNUAL_PAN_THRESHOLD = 100000

PAN_REGEX = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'

class TaxRuleConfig:
    source: str = "Income Tax Act, 1961 Section 10(13A) / CBDT Circular No. 08/2013 (Configured Demonstration Policy)"
    effective_date: str = "2013-10-10 (ongoing FY 2025-2026 guidelines)"
    threshold_amount: int = DEFAULT_ANNUAL_PAN_THRESHOLD
    policy_type: str = "STATUTORY_AND_EMPLOYER_MANDATE"

def validate_pan_format(pan: str) -> Tuple[bool, str]:
    """
    Preliminary format check only.
    As per guidelines, format validity does not prove authentic ownership.
    """
    if not pan:
        return False, "PAN is not provided"
    cleaned = pan.strip().upper()
    if re.match(PAN_REGEX, cleaned):
        return True, "PAN matches Indian 10-character alphanumeric syntax (5 letters, 4 digits, 1 letter). Authentic ownership not verified."
    return False, "PAN format invalid. Expected 5 uppercase letters, 4 digits, 1 uppercase letter (e.g., ABCDE1234F)."

def evaluate_pan_requirement(annual_rent: int, landlord_pan: str = None, threshold: int = DEFAULT_ANNUAL_PAN_THRESHOLD) -> Dict[str, Any]:
    """
    Evaluates whether Landlord PAN is strictly required, boundary cases,
    and returns traceable policy reasoning.
    """
    is_above_threshold = annual_rent > threshold
    is_at_threshold = annual_rent == threshold
    pan_provided = bool(landlord_pan and landlord_pan.strip())
    
    pan_valid_format = False
    format_message = ""
    if pan_provided:
        pan_valid_format, format_message = validate_pan_format(landlord_pan)
        
    pan_required = is_above_threshold
    
    status = "COMPLIANT"
    explanation = ""
    
    if is_above_threshold:
        if not pan_provided:
            status = "PAN_REQUIRED_BLOCKING"
            explanation = (
                f"Annual rent of ₹{annual_rent:,} strictly exceeds the statutory threshold of ₹{threshold:,}. "
                f"As per CBDT Circular No. 08/2013 & Section 10(13A), Landlord PAN is mandatory for HRA exemption. "
                f"Final employer submission cannot proceed without Landlord PAN or a Form 60 declaration."
            )
        elif not pan_valid_format:
            status = "INVALID_PAN_FORMAT"
            explanation = f"Landlord PAN provided but format is invalid: {format_message}"
        else:
            status = "COMPLIANT_WITH_PAN"
            explanation = (
                f"Annual rent is ₹{annual_rent:,} (exceeds ₹{threshold:,}). "
                f"Landlord PAN '{landlord_pan}' provided and format verified."
            )
    else:
        if pan_provided:
            explanation = f"Annual rent ₹{annual_rent:,} is within threshold ₹{threshold:,}. Landlord PAN provided voluntarily."
            status = "COMPLIANT_WITH_OPTIONAL_PAN"
        else:
            explanation = f"Annual rent ₹{annual_rent:,} does not exceed statutory threshold ₹{threshold:,}. Landlord PAN is optional under this policy."
            status = "COMPLIANT_BELOW_THRESHOLD"

    return {
        "annual_rent": annual_rent,
        "threshold": threshold,
        "is_above_threshold": is_above_threshold,
        "is_at_threshold": is_at_threshold,
        "pan_required": pan_required,
        "pan_provided": pan_provided,
        "pan_valid_format": pan_valid_format,
        "status": status,
        "explanation": explanation,
        "policy_source": TaxRuleConfig.source,
        "effective_date": TaxRuleConfig.effective_date,
        "policy_type": TaxRuleConfig.policy_type
    }
