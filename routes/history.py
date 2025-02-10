from flask import Blueprint, request, render_template, jsonify
from collections import defaultdict
from datetime import datetime
from routes.supabase_client import get_supabase_instance

# Create Blueprint for the route
history = Blueprint('history', __name__)
supabase = get_supabase_instance()

def format_date(date_str):
    """
    Formats a date from 'YYYY-MM-DD' to 'DD/MM/YY'.
    """
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%y")

@history.route('/history')
def index():
    TckrSymb = request.args.get('TckrSymb', 'NIFTY') 

    # Fetch all data from the EOD_SUMMARY table
    response = supabase.table("EOD_SUMMARY").select("*").eq('TckrSymb', TckrSymb).execute()
    data = response.data
    
    # Group the data by `created_at` (considering only the date part)
    grouped_data = defaultdict(list)
    
    for row in data:
        # Convert `created_at` to a date object
        created_date = row['FileDt'] if row['FileDt'] else datetime.fromisoformat(row['CREATED_AT']).date()
        key = f"{created_date}__{row['Strike']}"
        grouped_data[key].append(row)
        
    # Convert defaultdict to a regular dict with sorted data based on created_date for passing to the template
    grouped_data = dict(
        sorted(
            grouped_data.items(),
            key=lambda x: (datetime.fromisoformat(x[0].split('__')[0]).date(), x[0].split('__')[1]),
            reverse=True
        )
    )
    
    # Pass the grouped data to the template
    return render_template('history.html', table=grouped_data)

@history.route("/get-data/<int:spot_value>", methods=["GET"])
def get_options_data(spot_value):
    # Query the table to get records by Spot
    response = supabase.table("EOD_OPTIONS_SUMMARY").select("*").eq("Spot", spot_value).execute()
    
    if not response.data:
        return {"message": "No records found for the given Spot."}

    data = defaultdict(lambda: {"CE": [], "PE": []})
    
    # Track separate expiry dates for XpryDt1 and XpryDt2
    xpry_dt_1 = None
    xpry_dt_2 = None
    
    for record in response.data:
        # Formatting date to the required format
        # Use Weekly_XpryDt if not None, else use Monthly_XpryDt
        
        if record["Weekly_XpryDt"]:
            xpry_dt_1 = format_date(record["Weekly_XpryDt"])
            expiry_key = "XpryDt1"
        elif record["Monthly_XpryDt"]:
            xpry_dt_2 = format_date(record["Monthly_XpryDt"])
            expiry_key = "XpryDt2"
        else:
            continue
        
        # Identify if the record is for CE or PE
        option_type = record["Option"]

        # Add the record to the respective option list
        data[expiry_key][option_type].append({
            "EODOIChng": record["EOD_OI_Change"],
            "StrkPric": record["Strike"]
        })

    # Build the result in the required format
    result = {}
    # Add data for XpryDt1 if there are records for it
    if xpry_dt_1:
        result["XpryDt1"] = {
            "Strike": spot_value,
            "Date": xpry_dt_1,
            "CE": data["XpryDt1"]["CE"],
            "PE": data["XpryDt1"]["PE"],
        }

    # Add data for XpryDt2 if there are records for it
    if xpry_dt_2:
        result["XpryDt2"] = {
            "Strike": spot_value,
            "Date": xpry_dt_2,
            "CE": data["XpryDt2"]["CE"],
            "PE": data["XpryDt2"]["PE"],
        }

    # If no data for XpryDt1 or XpryDt2, return an appropriate message
    if not result:
        return {"message": "No valid data found for the given Spot."}

    return jsonify(result)