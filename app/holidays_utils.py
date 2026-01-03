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
    Uses accurate dates from government gazette
    """
    if year is None:
        year = datetime.now().year
    
    holidays = []
    
    # Accurate holidays by year (from government gazette)
    # For 2026
    if year == 2026:
        holidays = [
            (date(2026, 1, 3), "Duruthu Full Moon Poya Day", "religious"),
            (date(2026, 1, 15), "Tamil Thai Pongal Day", "cultural"),
            (date(2026, 2, 1), "Navam Full Moon Poya Day", "religious"),
            (date(2026, 2, 4), "Independence Day", "fixed"),
            (date(2026, 2, 15), "Maha Sivarathri Day", "religious"),
            (date(2026, 3, 2), "Medin Full Moon Poya Day", "religious"),
            (date(2026, 3, 21), "Id-Ul-Fitr (Ramazan Festival Day)", "religious"),
            (date(2026, 4, 1), "Bak Full Moon Poya Day", "religious"),
            (date(2026, 4, 3), "Good Friday", "religious"),
            (date(2026, 4, 13), "Day Prior to Sinhala & Tamil New Year Day", "cultural"),
            (date(2026, 4, 14), "Sinhala & Tamil New Year Day", "cultural"),
            (date(2026, 5, 1), "Vesak Full Moon Poya Day", "religious"),
            (date(2026, 5, 1), "May Day (International Workers' Day)", "fixed"),
            (date(2026, 5, 2), "Day Following Vesak Full Moon Poya Day", "religious"),
            (date(2026, 5, 28), "Id-Ul-Alha (Hadji Festival Day)", "religious"),
            (date(2026, 5, 30), "Adhi Poson Full Moon Poya Day", "religious"),
            (date(2026, 6, 29), "Poson Full Moon Poya Day", "religious"),
            (date(2026, 7, 29), "Esala Full Moon Poya Day", "religious"),
            (date(2026, 8, 26), "Milad-Un-Nabi (Holy Prophet's Birthday)", "religious"),
            (date(2026, 8, 27), "Nikini Full Moon Poya Day", "religious"),
            (date(2026, 9, 26), "Binara Full Moon Poya Day", "religious"),
            (date(2026, 10, 25), "Vap Full Moon Poya Day", "religious"),
            (date(2026, 11, 8), "Deepavali Festival Day", "religious"),
            (date(2026, 11, 24), "Il Full Moon Poya Day", "religious"),
            (date(2026, 12, 23), "Unduvap Full Moon Poya Day", "religious"),
            (date(2026, 12, 25), "Christmas Day", "fixed"),
        ]
    else:
        # For other years, use approximations (fallback)
        # Fixed date holidays
        fixed_holidays = [
            (1, 1, "New Year's Day"),
            (2, 4, "Independence Day"),
            (5, 1, "May Day"),
            (12, 25, "Christmas Day"),
        ]
        
        for month, day, name in fixed_holidays:
            try:
                holiday_date = date(year, month, day)
                holidays.append((holiday_date, name, "fixed"))
            except ValueError:
                pass
        
        # Sinhala and Tamil New Year (usually April 13-14)
        holidays.append((date(year, 4, 13), "Day Prior to Sinhala & Tamil New Year Day", "cultural"))
        holidays.append((date(year, 4, 14), "Sinhala & Tamil New Year Day", "cultural"))
        
        # All Full Moon Poya Days (approximate - around 15th of each month)
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
            try:
                poya_date = date(year, month, 15)
                holidays.append((poya_date, f'{name} Full Moon Poya Day', "religious"))
            except ValueError:
                pass
        
        # Other movable holidays (approximations)
        holidays.append((date(year, 3, 21), "Id-Ul-Fitr (Ramazan Festival Day)", "religious"))
        holidays.append((date(year, 5, 28), "Id-Ul-Alha (Hadji Festival Day)", "religious"))
        holidays.append((date(year, 8, 26), "Milad-Un-Nabi (Holy Prophet's Birthday)", "religious"))
        holidays.append((date(year, 11, 8), "Deepavali Festival Day", "religious"))
    
    # Convert to dictionary format and sort
    holiday_list = []
    for holiday_date, name, holiday_type in holidays:
        holiday_list.append({
            'date': holiday_date,
            'name': name,
            'type': holiday_type
        })
    
    # Remove duplicates and sort
    seen = set()
    unique_holidays = []
    for h in holiday_list:
        key = (h['date'], h['name'])
        if key not in seen:
            seen.add(key)
            unique_holidays.append(h)
    
    unique_holidays.sort(key=lambda x: x['date'])
    return unique_holidays


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

