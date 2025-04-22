from flask import Blueprint, render_template, request, jsonify
from datetime import datetime, timezone, timedelta
import pandas as pd
from routes.supabase_client import get_supabase_instance
from routes.common import set_is_selected
import traceback
import csv

# Create Blueprint for the route
eod_summary = Blueprint('eod_summary', __name__)
supabase = get_supabase_instance()

# Not going to use this but keeping this for future purpose
def detect_delimiter(file):
    """Detect delimiter in an uploaded CSV file"""
    sample_bytes = file.read(1024)  # Read first 1024 bytes as bytes
    file.seek(0)  # Reset file pointer
    try:
        sample = sample_bytes.decode("utf-8")  # Decode to string
    except UnicodeDecodeError:
        sample = sample_bytes.decode("ISO-8859-1")  # Fallback to another encoding
    if not sample.strip():
        raise ValueError("Empty file provided")
    try:
        return csv.Sniffer().sniff(sample).delimiter
    except csv.Error:
        print("Warning: Could not determine delimiter. Checking manually...")
        delimiters = [',', '\t', ';', '|']
        counts = {d: sample.count(d) for d in delimiters}
        best_guess = max(counts, key=counts.get)
        print('best_guess', best_guess)
        if counts[best_guess] > 0:
            return best_guess
        raise ','


def transform_and_save_options(data):
    records = []
    for expiry_key, expiry_value in data.items():
        strike = expiry_value["Strike"]
        date_column = "Weekly_XpryDt" if expiry_key == "XpryDt1" else "Monthly_XpryDt"

        for option_type in ["CE", "PE"]:
            for record in expiry_value[option_type]:
                transformed_record = {
                    "Spot": strike,
                    "Option": option_type,
                    "Strike": record["StrkPric"],
                    "EOD_OI_Change": record["EODOIChng"],
                    date_column: datetime.strptime(expiry_value["Date"], "%d/%m/%y").strftime("%Y-%m-%d")
                }
                records.append(transformed_record)

    # Insert records into Supabase
    response = supabase.table("EOD_OPTIONS_SUMMARY").insert(records).execute()
    return response

@eod_summary.route('/')
def index():
    return render_template('index.html')

@eod_summary.route('/', methods=['POST'])
def uploadFiles():
    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']
    if file.filename == '':
        return "No file selected", 400

    if not (file.filename.endswith('.csv') or file.filename.endswith('.txt')):
        return "Invalid file type. Please upload a CSV or TXT file.", 400

    try:
        # Read inputs from the request
        TckrSymb_input = request.form.get('TckrSymb', default='NIFTY').upper()
        strike_price = int(request.form.get('strike_price', default=0))
        XpryDt1 = request.form.get('XpryDt1')  # YYYY-MM-DD format
        XpryDt2 = request.form.get('XpryDt2')  # YYYY-MM-DD format
        FileDt = request.form.get('FileDt') # YYYY-MM-DD format

        # Convert request expiry dates to datetime objects (same format as in the CSV)
        XpryDt1 = datetime.strptime(XpryDt1, '%Y-%m-%d').strftime('%d/%m/%y') if TckrSymb_input == 'NIFTY' else None
        XpryDt2 = datetime.strptime(XpryDt2, '%Y-%m-%d').strftime('%d/%m/%y')

        # Validate expiry dates for Nifty
        if TckrSymb_input == 'NIFTY' and not XpryDt1 or not XpryDt2:
            return "Both weekly and monthly expiry dates are required for Nifty.", 400
        
        # Validate expiry dates
        if TckrSymb_input == 'BANKNIFTY' and not XpryDt2:
            return "Monthly expiry date is required for BankNifty.", 400

        # Load the CSV into a Pandas DataFrame
        df = pd.read_csv(file, sep=None, engine='python')

        # Add EODOI and EODOIChng columns
        df['EODOI'] = df['OpnIntrst'] * df['ClsPric']
        df['EODOIChng'] = df['ChngInOpnIntrst'] * df['ClsPric']

        # Filter based on TckrSymb and FinInstrmTp
        filtered_df = df[(df['FinInstrmTp'] == 'IDO') & (df['TckrSymb'] == TckrSymb_input)]
        
        # Filter further by the two expiry dates
        if TckrSymb_input == 'NIFTY':
            filtered_df = filtered_df[(filtered_df['XpryDt'] == XpryDt1) | (filtered_df['XpryDt'] == XpryDt2)]
        
        if TckrSymb_input == 'BANKNIFTY':
            filtered_df = filtered_df[(filtered_df['XpryDt'] == XpryDt2)]
        
        ce_xpry_dt1 = filtered_df[(filtered_df['OptnTp'] == 'CE') & (filtered_df['XpryDt'] == XpryDt1)].sort_values(by='EODOIChng', ascending=False).head(10)
        pe_xpry_dt1 = filtered_df[(filtered_df['OptnTp'] == 'PE') & (filtered_df['XpryDt'] == XpryDt1)].sort_values(by='EODOIChng', ascending=False).head(10)
        ce_xpry_dt2 = filtered_df[(filtered_df['OptnTp'] == 'CE') & (filtered_df['XpryDt'] == XpryDt2)].sort_values(by='EODOIChng', ascending=False).head(10)
        pe_xpry_dt2 = filtered_df[(filtered_df['OptnTp'] == 'PE') & (filtered_df['XpryDt'] == XpryDt2)].sort_values(by='EODOIChng', ascending=False).head(10)

        # Initialize toprecords and expiry groups
        toprecords = {}
        expiry_groups = []

        # populate toprecords and expiry groups dynamically based on provided expiry dates
        expiry_groups = []
        if TckrSymb_input == 'NIFTY':
            toprecords['XpryDt1'] = {
                'Strike': strike_price,
                'Date': XpryDt1,
                'CE': set_is_selected(
                    ce_xpry_dt1[['StrkPric', 'EODOIChng']].to_dict('records'),
                    strike_price,
                    lambda strk, strike: strk < strike
                ),
                'PE': set_is_selected(
                    pe_xpry_dt1[['StrkPric', 'EODOIChng']].to_dict('records'),
                    strike_price,
                    lambda strk, strike: strk > strike
                )
            }
            expiry_groups.append({'Expiry': 'Weekly', 'XpryDt': XpryDt1})
            

        toprecords['XpryDt2'] =  {
            'Strike': strike_price,
            'Date': XpryDt2,
            'CE': set_is_selected(
                    ce_xpry_dt2[['StrkPric', 'EODOIChng']].to_dict('records'),
                    strike_price,
                    lambda strk, strike: strk < strike
                ),
                'PE': set_is_selected(
                    pe_xpry_dt2[['StrkPric', 'EODOIChng']].to_dict('records'),
                    strike_price,
                    lambda strk, strike: strk > strike
                )
        }
        expiry_groups.append({'Expiry': 'Monthly', 'XpryDt': XpryDt2})
        
        result_rows = []
        for group in expiry_groups:
            expiry = group['Expiry']
            expiry_date = group['XpryDt']
            filtered_by_date = filtered_df[filtered_df['XpryDt'] == expiry_date]

            # Calculate CE sums
            ce_df = filtered_by_date[(filtered_by_date['OptnTp'] == 'CE')]
            ce_eod_sum = ce_df['EODOI'].sum()
            ce_eod_chng_sum = ce_df['EODOIChng'].sum()

            # Calculate ITM CE sums
            itm_ce_df = filtered_by_date[(filtered_by_date['OptnTp'] == 'CE') & (filtered_by_date['StrkPric'] <= strike_price)]
            itm_ce_eod_sum = itm_ce_df['EODOI'].sum()
            itm_ce_eod_chng_sum = itm_ce_df['EODOIChng'].sum()

            # Calculate PE sums
            pe_df = filtered_by_date[(filtered_by_date['OptnTp'] == 'PE')]
            pe_eod_sum = pe_df['EODOI'].sum()
            pe_eod_chng_sum = pe_df['EODOIChng'].sum()
            
            # Calculate PE sums
            itm_pe_df = filtered_by_date[(filtered_by_date['OptnTp'] == 'PE') & (filtered_by_date['StrkPric'] >= strike_price)]
            itm_pe_eod_sum = itm_pe_df['EODOI'].sum()
            itm_pe_eod_chng_sum = itm_pe_df['EODOIChng'].sum()

            # Append row to results
            result_rows.append({
                'Expiry': expiry,
                'TckrSymb': TckrSymb_input,
                'FileDt': FileDt,
                'Expiry_Date': expiry_date,
                'Strike': strike_price,
                'EOD_CE_OI_Sum': ce_eod_sum,
                'EOD_CE_OI_Change_Sum': ce_eod_chng_sum,
                'ITM_EOD_CE_OI_Sum': itm_ce_eod_sum,
                'ITM_EOD_CE_OI_Change_Sum': itm_ce_eod_chng_sum,
                'EOD_PE_OI_Sum': pe_eod_sum,
                'EOD_PE_OI_Change_Sum': pe_eod_chng_sum,
                'ITM_EOD_PE_OI_Sum': itm_pe_eod_sum,
                'ITM_EOD_PE_OI_Change_Sum': itm_pe_eod_chng_sum
            })

        # Return the tables as response
        return render_template('index.html', TckrSymb=TckrSymb_input, table=result_rows, toprecords=toprecords)

    except Exception as e:
        print("Error occurred:", e)
        print(traceback.format_exc())
        return f"Error processing the file: {e}", 500

@eod_summary.route('/saveeodsummary', methods=['POST'])
def save():
    # Receive JSON data from the frontend
    result_rows = request.json.get('rows', [])
    toprecords = request.json.get('toprecords', {})
    
    transform_and_save_options(toprecords)

    # Insert the data into Supabase table
    response = supabase.table("EOD_SUMMARY").insert(result_rows).execute()
    
    # Cleanup: Delete records older than 10 days
    ten_days_ago = datetime.now(timezone.utc) - timedelta(days=10)
    delete_response1 = supabase.table('EOD_SUMMARY').delete().lt('CREATED_AT', ten_days_ago).execute()
    delete_response2 = supabase.table('EOD_OPTIONS_SUMMARY').delete().lt('CREATED_AT', ten_days_ago).execute()
    # return jsonify({'message': 'Failed to save data!'}), 200
    if response.data:
        return jsonify({'message': 'Data saved successfully!', 
                        'inserted_data': response.data,
                        'deleted_data': [delete_response1.data, delete_response2.data]}), 200
    else:
        return jsonify({'message': 'Failed to save data!'}), 400
