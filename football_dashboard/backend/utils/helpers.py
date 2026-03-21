"""
Utility Helper Functions
Common utility functions for the application
"""

from datetime import datetime, timedelta
import re

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    pattern = r'^\+?[0-9]{10,15}$'
    return re.match(pattern, phone) is not None

def format_date(date_obj, format_str='%Y-%m-%d'):
    """Format datetime object to string"""
    if isinstance(date_obj, datetime):
        return date_obj.strftime(format_str)
    return date_obj

def parse_date(date_str, format_str='%Y-%m-%d'):
    """Parse date string to datetime object"""
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError:
        return None

def calculate_age(dob):
    """Calculate age from date of birth"""
    if isinstance(dob, str):
        dob = parse_date(dob)
    if not dob:
        return None
    
    today = datetime.now()
    age = today.year - dob.year
    
    if today.month < dob.month or (today.month == dob.month and today.day < dob.day):
        age -= 1
    
    return age

def generate_unique_id(prefix=''):
    """Generate a unique ID"""
    import uuid
    unique_id = str(uuid.uuid4()).replace('-', '')[:12]
    return f"{prefix}{unique_id}" if prefix else unique_id

def paginate(query_result, page=1, per_page=20):
    """Paginate query results"""
    total = len(query_result)
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'data': query_result[start:end],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    }

def allowed_file(filename, allowed_extensions={'png', 'jpg', 'jpeg', 'gif'}):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    import re
    filename = re.sub(r'[^\w\s.-]', '', filename)
    return filename.strip()

def format_duration(minutes):
    """Format minutes to hours and minutes"""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"

def calculate_match_duration(start_time, end_time):
    """Calculate duration between two times"""
    if isinstance(start_time, str):
        start_time = parse_date(start_time, '%H:%M')
    if isinstance(end_time, str):
        end_time = parse_date(end_time, '%H:%M')
    
    if start_time and end_time:
        duration = end_time - start_time
        return int(duration.total_seconds() / 60)
    return 0

def get_season_year():
    """Get current football season year"""
    now = datetime.now()
    if now.month >= 7:
        return f"{now.year}-{now.year + 1}"
    return f"{now.year - 1}-{now.year}"

def is_match_live(match_date, status):
    """Check if match is currently live"""
    if status != 'scheduled':
        return status == 'live'
    
    if isinstance(match_date, str):
        match_date = parse_date(match_date)
    
    if not match_date:
        return False
    
    now = datetime.now()
    time_diff = now - match_date
    
    # Match is live if it's within 2 hours of start time
    return time_diff.total_seconds() <= 7200 and time_diff.total_seconds() >= -1800

def format_currency(amount, currency='RWF'):
    """Format currency amount"""
    return f"{currency} {amount:,.0f}"

def truncate_text(text, max_length=50):
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'

def build_response(data=None, message=None, error=None, status=200):
    """Build standardized API response"""
    response = {}
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    if error:
        response['error'] = error
    
    return response, status

def merge_dicts(*dicts):
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result

def filter_dict(d, keys):
    """Filter dictionary to only include specified keys"""
    return {k: v for k, v in d.items() if k in keys}

def remove_none_values(d):
    """Remove None values from dictionary"""
    return {k: v for k, v in d.items() if v is not None}

class DateTimeHelper:
    """DateTime helper class"""
    
    @staticmethod
    def now():
        return datetime.now()
    
    @staticmethod
    def today():
        return datetime.now().date()
    
    @staticmethod
    def add_days(date_obj, days):
        return date_obj + timedelta(days=days)
    
    @staticmethod
    def add_months(date_obj, months):
        return date_obj + timedelta(days=months*30)
    
    @staticmethod
    def is_past(date_obj):
        return date_obj < datetime.now()
    
    @staticmethod
    def is_future(date_obj):
        return date_obj > datetime.now()

class ValidationHelper:
    """Validation helper class"""
    
    @staticmethod
    def is_valid_jersey_number(number):
        return isinstance(number, int) and 1 <= number <= 99
    
    @staticmethod
    def is_valid_position(position):
        valid_positions = [
            'Goalkeeper', 'Defender', 'Midfielder', 'Forward',
            'Center Back', 'Left Back', 'Right Back',
            'Central Midfielder', 'Attacking Midfielder', 'Defensive Midfielder',
            'Striker', 'Left Winger', 'Right Winger'
        ]
        return position in valid_positions
    
    @staticmethod
    def is_valid_nationality(nationality):
        valid_nationalities = [
            'Rwandan', 'Kenyan', 'Ugandan', 'Tanzanian', 'Burundian',
            'Nigerian', 'Ghanaian', 'Ivorian', 'South African',
            'Cameroonian', 'Congolese', 'Other'
        ]
        return nationality in valid_nationalities
