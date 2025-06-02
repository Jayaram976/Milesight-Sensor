# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
app.secret_key = 'your-secret-key'

data_store = []  # Temporary in-memory storage

def format_ist_time(utc_time_str):
    utc_time = datetime.strptime(utc_time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    utc_time = utc_time.replace(tzinfo=pytz.utc)
    ist_time = utc_time.astimezone(pytz.timezone('Asia/Kolkata'))
    return ist_time.strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    filter_option = request.args.get('filter', 'today')
    selected_date = request.args.get('date')

    today = datetime.now(pytz.timezone('Asia/Kolkata')).date()
    filtered_data = []

    for entry in data_store:
        entry_time = datetime.strptime(entry['time'], '%Y-%m-%d %H:%M:%S').date()
        if filter_option == 'today' and entry_time == today:
            filtered_data.append(entry)
        elif filter_option == 'yesterday' and entry_time == today - timedelta(days=1):
            filtered_data.append(entry)
        elif filter_option == 'date' and selected_date:
            try:
                selected = datetime.strptime(selected_date, '%Y-%m-%d').date()
                if entry_time == selected:
                    filtered_data.append(entry)
            except:
                pass
        elif filter_option not in ['today', 'yesterday', 'date']:
            filtered_data.append(entry)

    return render_template('main_dashboard.html', data=filtered_data, filter_option=filter_option)

@app.route('/ttn/uplink', methods=['POST'])
def ttn_uplink():
    payload = request.get_json()
    try:
        decoded = payload['uplink_message']['decoded_payload']
        received_at = payload['received_at']
        formatted_time = format_ist_time(received_at)

        entry = {
            'device_id': payload.get('end_device_ids', {}).get('device_id', 'Unknown'),
            'battery': decoded.get('battery', 0),
            'distance': decoded.get('distance', 0),
            'tilt': decoded.get('tilt', 'normal'),
            'time': formatted_time
        }

        data_store.append(entry)
        if len(data_store) > 500:
            data_store.pop(0)

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

