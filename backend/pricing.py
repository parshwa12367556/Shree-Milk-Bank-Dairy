"""
Smart Dairy ERP — Pricing Engine

Business logic for computing milk collection prices and quality grading.
"""
from enum import Enum


class QualityGrade(Enum):
    """Quality grades for milk testing."""
    A = 'PASS'
    B = 'BORDERLINE'
    C = 'REJECTED'


def compute_price(fat, snf, quantity, fat_rate, snf_rate):
    """
    Compute the price for a milk collection.
    
    Formula:
        rate_per_liter = fat × fat_rate + snf × snf_rate
        amount = rate_per_liter × quantity
    
    Args:
        fat: Fat percentage (e.g., 4.2)
        snf: SNF percentage (e.g., 8.6)
        quantity: Milk quantity in liters
        fat_rate: Rate per unit of fat (e.g., 5.00)
        snf_rate: Rate per unit of SNF (e.g., 2.50)
    
    Returns:
        dict with 'rate_per_liter' and 'amount'
    """
    rate_per_liter = round(fat * fat_rate + snf * snf_rate, 2)
    amount = round(rate_per_liter * quantity, 2)
    return {
        'rate_per_liter': rate_per_liter,
        'amount': amount
    }


def quality_grade(fat, water, milk_type):
    """
    Determine the quality grade of a milk sample.
    
    Grading criteria:
        - Water > 8% → REJECTED (C)
        - Fat < 70% of minimum for type → REJECTED (C)
        - Water > 5% or fat < 85% of minimum → BORDERLINE (B)
        - Otherwise → PASS (A)
    
    Minimum fat by milk type:
        COW: 3.0%, BUFFALO: 4.5%, MIXED: 3.5%
    
    Args:
        fat: Fat percentage
        water: Water percentage
        milk_type: 'COW', 'BUFFALO', or 'MIXED'
    
    Returns:
        dict with 'grade' (A/B/C), 'label' (PASS/BORDERLINE/REJECTED),
        and 'warnings' list
    """
    warnings = []
    
    # Minimum fat thresholds by milk type
    min_fat = {
        'COW': 3.0,
        'BUFFALO': 4.5,
        'MIXED': 3.5
    }.get(milk_type, 3.0)
    
    # Check water content
    if water > 8:
        warnings.append(f'Water content ({water}%) exceeds maximum threshold (8%)')
        return {'grade': 'C', 'label': 'REJECTED', 'warnings': warnings}
    
    if water > 5:
        warnings.append(f'Water content ({water}%) is above ideal threshold (5%)')
    
    # Check fat content
    if fat < min_fat * 0.7:
        warnings.append(f'Fat content ({fat}%) critically low for {milk_type} milk (min: {min_fat}%)')
        return {'grade': 'C', 'label': 'REJECTED', 'warnings': warnings}
    
    if fat < min_fat * 0.85:
        warnings.append(f'Fat content ({fat}%) below ideal for {milk_type} milk (min: {min_fat}%)')
        return {'grade': 'B', 'label': 'BORDERLINE', 'warnings': warnings}
    
    if water > 5 or fat < min_fat:
        return {'grade': 'B', 'label': 'BORDERLINE', 'warnings': warnings}
    
    return {'grade': 'A', 'label': 'PASS', 'warnings': warnings}


def auto_grade_quality(fat, snf, clr, water, temperature, milk_type):
    """
    Full quality auto-grading based on multiple parameters.
    
    Args:
        fat: Fat percentage
        snf: SNF percentage
        clr: CLR reading
        water: Water percentage
        temperature: Temperature in Celsius
        milk_type: 'COW', 'BUFFALO', or 'MIXED'
    
    Returns:
        dict with final grade and all parameter statuses
    """
    parameters = {}
    warnings = []
    all_pass = True
    any_borderline = False
    
    # Temperature check (ideal: ≤ 6°C)
    if temperature > 8:
        parameters['temperature'] = {'value': temperature, 'status': 'FAIL'}
        warnings.append(f'Temperature {temperature}°C exceeds maximum (8°C)')
        all_pass = False
    elif temperature > 6:
        parameters['temperature'] = {'value': temperature, 'status': 'BORDERLINE'}
        warnings.append(f'Temperature {temperature}°C above ideal (6°C)')
        any_borderline = True
    else:
        parameters['temperature'] = {'value': temperature, 'status': 'PASS'}
    
    # CLR check
    clr_min = {'COW': 28.0, 'BUFFALO': 27.0, 'MIXED': 27.5}.get(milk_type, 28.0)
    if clr < clr_min - 2:
        parameters['clr'] = {'value': clr, 'status': 'FAIL'}
        all_pass = False
    elif clr < clr_min:
        parameters['clr'] = {'value': clr, 'status': 'BORDERLINE'}
        any_borderline = True
    else:
        parameters['clr'] = {'value': clr, 'status': 'PASS'}
    
    # Water check
    if water > 8:
        parameters['water'] = {'value': water, 'status': 'FAIL'}
        all_pass = False
    elif water > 5:
        parameters['water'] = {'value': water, 'status': 'BORDERLINE'}
        any_borderline = True
    else:
        parameters['water'] = {'value': water, 'status': 'PASS'}
    
    # Fat check
    min_fat = {'COW': 3.0, 'BUFFALO': 4.5, 'MIXED': 3.5}.get(milk_type, 3.0)
    if fat < min_fat * 0.7:
        parameters['fat'] = {'value': fat, 'status': 'FAIL'}
        all_pass = False
    elif fat < min_fat:
        parameters['fat'] = {'value': fat, 'status': 'BORDERLINE'}
        any_borderline = True
    else:
        parameters['fat'] = {'value': fat, 'status': 'PASS'}
    
    # Determine overall result
    if not all_pass:
        overall = 'FAIL'
    elif any_borderline:
        overall = 'BORDERLINE'
    else:
        overall = 'PASS'
    
    return {
        'overall': overall,
        'parameters': parameters,
        'warnings': warnings,
        'grade': 'A' if overall == 'PASS' else 'B' if overall == 'BORDERLINE' else 'C'
    }
