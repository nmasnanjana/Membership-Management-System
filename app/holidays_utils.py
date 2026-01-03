"""
Sri Lankan Public Holidays Utility
Returns list of holidays for any given year
"""
from datetime import date, datetime
import calendar


def get_sri_lankan_holidays(year=None):
    """
    Get all Sri Lankan public holidays for a given year
    Returns a list of dictionaries with 'date' and 'name' keys
    """
    if year is None:
        year = datetime.now().year
    
    holidays = []
    
    # Fixed date holidays
    fixed_holidays = [
        (1, 1, "New Year's Day"),
        (2, 4, "Independence Day"),
        (5, 1, "May Day"),
        (6, 30, "Ramazan Festival Day"),
        (12, 25, "Christmas Day"),
    ]
    
    for month, day, name in fixed_holidays:
        try:
            holiday_date = date(year, month, day)
            holidays.append({
                'date': holiday_date,
                'name': name,
                'type': 'fixed'
            })
        except ValueError:
            pass  # Invalid date (e.g., Feb 30)
    
    # Calculate movable holidays (approximations for Buddhist/Sinhala calendar)
    # These are approximations - actual dates vary based on lunar calendar
    
    # Sinhala and Tamil New Year (usually April 13-14)
    # Using April 13-14 as standard
    holidays.append({
        'date': date(year, 4, 13),
        'name': 'Sinhala and Tamil New Year',
        'type': 'cultural'
    })
    holidays.append({
        'date': date(year, 4, 14),
        'name': 'Sinhala and Tamil New Year',
        'type': 'cultural'
    })
    
    # Vesak (Full Moon Poya Day in May - varies)
    # Approximation: Usually around May 10-15
    vesak_date = date(year, 5, 10)  # This is an approximation
    holidays.append({
        'date': vesak_date,
        'name': 'Vesak Full Moon Poya Day',
        'type': 'religious'
    })
    
    # Poson (Full Moon Poya Day in June - varies)
    poson_date = date(year, 6, 10)  # Approximation
    holidays.append({
        'date': poson_date,
        'name': 'Poson Full Moon Poya Day',
        'type': 'religious'
    })
    
    # All Full Moon Poya Days (12 per year, approximate)
    poya_months = [
        (1, 'Duruthu'),
        (2, 'Navam'),
        (3, 'Medin'),
        (4, 'Bak'),
        (5, 'Vesak'),
        (6, 'Poson'),
        (7, 'Esala'),
        (8, 'Nikini'),
        (9, 'Binara'),
        (10, 'Vap'),
        (11, 'Il'),
        (12, 'Unduvap')
    ]
    
    for month, name in poya_months:
        # Approximate: Full moon is usually around 15th of each month
        try:
            poya_date = date(year, month, 15)
            # Check if it's a Sunday, if not, find nearest Sunday
            if poya_date.weekday() != 6:  # 6 = Sunday
                days_until_sunday = (6 - poya_date.weekday()) % 7
                if days_until_sunday > 3:
                    days_until_sunday -= 7
                poya_date = date(year, month, 15 + days_until_sunday)
            
            holidays.append({
                'date': poya_date,
                'name': f'{name} Full Moon Poya Day',
                'type': 'religious'
            })
        except ValueError:
            pass
    
    # Deepavali (varies, usually October/November)
    deepavali_date = date(year, 10, 27)  # Approximation
    holidays.append({
        'date': deepavali_date,
        'name': 'Deepavali Festival Day',
        'type': 'religious'
    })
    
    # Milad-Un-Nabi (varies)
    milad_date = date(year, 9, 27)  # Approximation
    holidays.append({
        'date': milad_date,
        'name': 'Milad-Un-Nabi (Prophet Muhammad\'s Birthday)',
        'type': 'religious'
    })
    
    # Sort by date
    holidays.sort(key=lambda x: x['date'])
    
    return holidays


def is_holiday(check_date):
    """Check if a given date is a Sri Lankan public holiday"""
    holidays = get_sri_lankan_holidays(check_date.year)
    holiday_dates = [h['date'] for h in holidays]
    return check_date in holiday_dates


def get_holiday_name(check_date):
    """Get the name of the holiday if the date is a holiday, else None"""
    holidays = get_sri_lankan_holidays(check_date.year)
    for holiday in holidays:
        if holiday['date'] == check_date:
            return holiday['name']
    return None


def get_upcoming_holidays(count=5, start_date=None):
    """Get upcoming holidays from a start date"""
    if start_date is None:
        start_date = date.today()
    
    current_year = start_date.year
    holidays = []
    
    # Get holidays for current year and next year
    for year in [current_year, current_year + 1]:
        year_holidays = get_sri_lankan_holidays(year)
        holidays.extend([h for h in year_holidays if h['date'] >= start_date])
    
    # Sort and return top N
    holidays.sort(key=lambda x: x['date'])
    return holidays[:count]

