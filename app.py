from flask import Flask, render_template, request, jsonify
from holiday_bot import create_vacation_plan



app = Flask(__name__)


@app.route('/')
def index():
	return	render_template('index.html')

@app.route('/vacation_plan', methods=['POST'])
def vacation_plan():
	data = request.get_json()
	leave_days_available = data.get('leave_days_available')
	year = data.get('year')
	country_code = data.get('country_code','GB')
	month = data.get('month')

	vacation_plan = create_vacation_plan(
		leave_days_available, year, country_code, month	
	)

	return jsonify(vacation_plan)
