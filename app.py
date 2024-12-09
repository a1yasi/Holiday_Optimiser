from flask import Flask, render_template, request
from holiday_bot import create_vacation_plan



app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/', methods=['POST'])
def index_post():
	leave_days_available = int(request.form['leave_days_available'])
	year = int(request.form['year'])
	country_code = request.form['country_code']
	month = int(request.form['month'])

	vacation_plan = create_vacation_plan(leave_days_available, year, country_code, month)

	

	return render_template('index.html', 
		leave_days_available=leave_days_available, 
		year=year, 
		country_code=country_code, 
		month=month,
		current_month=vacation_plan.get("current_month"),
		current_suggestions = vacation_plan.get("suggestions"),
		alternative_month=vacation_plan.get("alternative_month"),
		alternative_suggestions=vacation_plan.get("alternative_suggestions")
		
		)