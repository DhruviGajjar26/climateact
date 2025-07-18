from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime
from app import run_carbon_agent  # Import our agent logic

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/track', methods=['GET', 'POST'])
def track():
    if request.method == 'GET':
        return render_template('index.html')
    
    elif request.method == 'POST':
        try:
            # Get form data
            user_data = {
                'car_km': request.form.get('car_km', '0'),
                'public_transport_km': request.form.get('public_transport_km', '0'),
                'flight_km': request.form.get('flight_km', '0'),
                'ac_hours': request.form.get('ac_hours', '0'),
                'heater_hours': request.form.get('heater_hours', '0'),
                'meat_meals': request.form.get('meat_meals', '0'),
                'vegetarian_meals': request.form.get('vegetarian_meals', '0'),
                'electricity_kwh': request.form.get('electricity_kwh', '0'),
                'water_heating_hours': request.form.get('water_heating_hours', '0'),
                'additional_activities': request.form.get('additional_activities', ''),
                'location': request.form.get('location', ''),
                'season': request.form.get('season', '')
            }
            
            # Run the carbon tracking agent
            result = run_carbon_agent(user_data)
            
            # Return results
            return render_template('results.html', result=result)
            
        except Exception as e:
            return render_template('error.html', error=str(e))

@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    """API endpoint for carbon calculation"""
    try:
        data = request.get_json()
        result = run_carbon_agent(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/reports')
def reports():
    """Display saved reports"""
    try:
        reports = []
        if os.path.exists('carbon_logs'):
            for filename in os.listdir('carbon_logs'):
                if filename.endswith('.json'):
                    with open(f'carbon_logs/{filename}', 'r') as f:
                        reports.append(json.load(f))
        
        # Sort by timestamp
        reports.sort(key=lambda x: x['timestamp'], reverse=True)
        return render_template('reports.html', reports=reports)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/tips')
def tips():
    """Display climate tips"""
    tips_data = {
        'transportation': [
            'Use public transport or carpooling',
            'Walk or bike for short distances',
            'Work from home when possible',
            'Plan efficient routes to combine trips'
        ],
        'energy': [
            'Use LED bulbs and energy-efficient appliances',
            'Set thermostat to 78°F (26°C) in summer',
            'Unplug electronics when not in use',
            'Use natural lighting during the day'
        ],
        'food': [
            'Eat more plant-based meals',
            'Buy local and seasonal produce',
            'Reduce food waste',
            'Choose sustainable seafood'
        ],
        'lifestyle': [
            'Reduce, reuse, recycle',
            'Buy second-hand when possible',
            'Use reusable bags and bottles',
            'Support renewable energy'
        ]
    }
    return render_template('tips.html', tips=tips_data)

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)