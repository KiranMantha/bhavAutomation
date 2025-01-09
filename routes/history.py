from flask import Blueprint, render_template
from collections import defaultdict
from datetime import datetime
from routes.supabase_client import get_supabase_instance

# Create Blueprint for the route
history = Blueprint('history', __name__)
supabase = get_supabase_instance()

@history.route('/history')
def index():
    # Fetch all data from the EOD_SUMMARY table
    response = supabase.table("EOD_SUMMARY").select("*").execute()
    data = response.data
    
    # Group the data by `created_at` (considering only the date part)
    grouped_data = defaultdict(list)
    
    for row in data:
        # Convert `created_at` to a date object
        created_date = datetime.fromisoformat(row['CREATED_AT']).date()
        grouped_data[created_date].append(row)
        
    # Convert defaultdict to a regular dict for passing to the template
    grouped_data = {str(date): rows for date, rows in grouped_data.items()}
    
    # Pass the grouped data to the template
    return render_template('history.html', table=grouped_data)