from openai import AzureOpenAI
import os
import requests
import json
from datetime import datetime, timedelta


client = AzureOpenAI(
	api_key = os.getenv("AZURE_KEY"),
	api_version = "2023-10-01-preview",
	azure_endpoint = os.getenv("AZURE_ENDPOINT")
)

#fetch public holiday for specific year and country 

def get_holidays(year,country_code):
	url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"
	response = requests.get(url)
	data = response.json()
	return data


#filter public holiday to specific month
def filter_holidays_by_month(holidays, month):
	return [
		holiday
		for holiday in holidays
		if datetime.strptime(holiday["date"], "%Y-%m-%d").month == month

	]


#calculating working days excluding weekend and public holiday
def calculate_working_days(start, end, holidays):
	current_date = start
	working_days = 0
	while current_date <= end:
		if current_date.weekday()<5 and current_date.strftime("%Y-%m-%d") not in holidays:
			working_days += 1
		current_date += timedelta(days=1)
	return working_days


#create vacation suggestion based on a holiday and leave days
#craeted dictionary containing the vacation suggestion details
def suggest_vacation(holiday_date, leave_days, vacation_type, holiday_name, public_holidays, max_leave_days):
	start_date = holiday_date - timedelta(days=max_leave_days // 2)
	end_date = holiday_date + timedelta(days=leave_days // 2)
	

	working_days_needed = calculate_working_days(start_date, end_date, public_holidays)

	if working_days_needed > max_leave_days:
		end_date = start_date + timedelta(days=max_leave_days - 1)
		working_days_needed = calculate_working_days(start_date, end_date, public_holidays)

	total_days_off = (end_date - start_date).days + 1

	explanation = (
		f"Take {working_days_needed} annual leave days from {start_date.strftime('%Y-%m-%d')} to "
		f"{end_date.strftime('%Y-%m-%d')} around the {holiday_name} holiday to maximize "
		f"your vacation to a total of {total_days_off} days off, including weekends and public holidays."
	)

	return{
		"type": vacation_type,
		"start_date": start_date.strftime("%Y-%m-%d"),
		"end_date": end_date.strftime("%Y-%m-%d"),
		"days_needed": working_days_needed,
		"total_days_off": total_days_off,
		"holiday_name": holiday_name,
		"explanation":explanation,
	}

#adding all the total days off
def sort_by_total_days_off(suggestion):
	return suggestion["total_days_off"]



#suggest leave days for vacation
# genarate vacation suggest based on public holidays and leave days 
def generate_vacation_suggestions(leave_days_available, holidays, country_code, max_leave_days):
	suggestions = []
	seen_explanations = set()

	public_holidays = [holiday["date"] for holiday in holidays]
	for holiday in holidays:
		holiday_date = datetime.strptime(holiday["date"],"%Y-%m-%d")
		holiday_name = holiday["name"]


#calculate the start and end date for short vacation
		for leave_days in [leave_days_available, leave_days_available - 1]:
			if leave_days > 0:
				suggestion = suggest_vacation(holiday_date, leave_days, f"{leave_days}-day vacation", holiday_name, public_holidays, max_leave_days)

			if suggestion['explanation'] not in seen_explanations:
				suggestions.append(suggestion)
				seen_explanations.add(suggestion['explanation'])


	return suggestions


#find an alternative month with holidays if no holidays are available in the requested month
def find_alternative_month_with_holiday(holidays, current_month):
	months_with_holidays = set(datetime.strptime(holiday["date"], "%Y-%m-%d").month for holiday in holidays)
	next_month = (current_month % 12) + 1
	if next_month in months_with_holidays:
		return next_month

	for month in range(1, 13):
		adjusted_month = (next_month + month - 1) % 12 + 1
		if adjusted_month in months_with_holidays:
			return adjusted_month

	return None




#genarate vacation plan and combaining holidays and leave days
def create_vacation_plan(leave_days_available, year, country_code, month=None):
	holidays = get_holidays(year, country_code)
	

	if not holidays:
		return {"message": f"No public holidays found for the year {year}"}

	current_suggestions= []

#filter holiday for the request month 
	if month:
		month_holidays = filter_holidays_by_month(holidays, month)
		if month_holidays:
			current_suggestions = generate_vacation_suggestions(leave_days_available, month_holidays, country_code, leave_days_available)
		else:
			alternative_month = find_alternative_month_with_holiday(holidays, month)
			if alternative_month:
				alt_month_holidays = filter_holidays_by_month(holidays, alternative_month)
				alternative_suggestions = generate_vacation_suggestions(leave_days_available, alt_month_holidays, country_code, leave_days_available)
				return {
					"message": f"No public holidays found in {datetime(year, month, 1).strftime('%B')}.",
					"alternative_month": datetime(year, alternative_month, 1).strftime("%B"),
					"alternative_suggestions": alternative_suggestions
					}

			else:
				return {"message": f"No public holidays found in {datetime(year, month, 1).strftime('%B')} and no alternative month available."}


	return {
		"current_month": datetime(year, month, 1).strftime("%B") if month else None,
		"suggestions": current_suggestions,
    }	




messages = [
	{"role":"system","content": "You are an assistant helping users plan vacations around public holidays."},
	{"role": "user", "content": "I have {leave_days_available} annual leave days left. Suggest how I can maximize my vacation time in {month} in {country_code}. The year is {year}."},

]

functions = [
	{
		#"type":"function",
		#"function": {
			"name": "create_vacation_plan",
			"description":"Suggest vacation plans based on public holidays, available leave days, and a specific month.",
			"parameters":{
				"type":"object",
				"properties":{
					"leave_days_available":{
						"type": "integer",
						"description": "Number of leave days the user has available"
					},
					"year": {"type": "integer","description":"Year for which vacation planning is needed."},
					"country_code":{
						"type": "string",
						"description": "Country code to find public holidays (e.g., 'GB')."
					},
					"month": {
						"type":"integer",
						"description":"Specific month for which vacation planning is needed (1-12)."

					},

				},
				"required":["leave_days_available","year","country_code"]

			}
		#}
	}

]



response = client.chat.completions.create(model="GPT-4", messages = messages, functions=functions)

gpt_tools = response.choices[0].message.tool_calls


if gpt_tools:
	for gpt_tool in gpt_tools:
		function_name = gpt_tool.function.name
		function_parameters = gpt_tool.function.arguments

		if function_name == "create_vacation_plan":
			leave_days_available = function_parameters.get("leave_days_available")
			year = function_parameters.get("year")
			country_code = function_parameters.get("country_code")
			month = function_parameters.get("month")
			vacation_plan = create_vacation_plan(leave_days_available, year, country_code, month)
			print(vacation_plan)
else:
	print(response.choices[0].message.content)

