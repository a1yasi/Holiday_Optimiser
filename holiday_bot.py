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



#suggest leave days for vacation
# genarate vacation suggest based on public holidays and leave days 
def generate_vacation_suggestions(leave_days_available, holidays):
	suggestions = []
	for holiday in holidays:
		holiday_date = datetime.strptime(holiday["date"],"%Y-%m-%d")


#short vacation 
#calculate the start and end date for short vacation
		if leave_days_available >= 1:
			suggestions.append(suggest_vacation(holiday_date, leave_days_available, f"{leave_days_available}-day vacation"))

#long vacation calcutate the start and end date for long vacation
		# if leave_days_available >= max_days:
		# 	suggestions.append(suggest_vacation(holiday_date, max_days, "long vacation"))

	return suggestions


#create vacation suggestion with start and end date
def suggest_vacation(holiday_date, leave_days, vacation_type):
	start_date = holiday_date - timedelta(days=leave_days // 2)
	end_date = holiday_date + timedelta(days=leave_days // 2)
	return{
		"type": vacation_type,
		"start_date": start_date.strftime("%Y-%m-%d"),
		"end_date": end_date.strftime("%Y-%m-%d"),
		"days_needed": leave_days,
		"explanation": f"By taking {leave_days} leave days around the holiday on {holiday_date.strftime('%Y-%m-%d')}, "
                       f"you can maximize your time off to {leave_days + 1} days."
		 
	}


#funcation to find the best alternative month with most holiday
#group holidays by month  
def find_month_long_vacation(holidays, current_month):
	month_holiday_count = {}

	for holiday in holidays:
		holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d")
		month = holiday_date.month

#ignore the current month
		if month != current_month:
			month_holiday_count[month]  = month_holiday_count.get(month, 0) + 1
		

#find the month with the most holidays
	if month_holiday_count:
		best_month = max(month_holiday_count, key=month_holiday_count.get)
		return best_month, month_holiday_count[best_month]

	return None, None



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
			current_suggestions = generate_vacation_suggestions(leave_days_available, month_holidays)
		
		
	alternative_month, _ = find_month_long_vacation(holidays, month or 0)
	alternative_suggestions = []
	if alternative_month:
		alt_month_holidays = filter_holidays_by_month(holidays, alternative_month)
		alternative_suggestions = generate_vacation_suggestions(leave_days_available, alt_month_holidays)


	return{
		"current_month": datetime(year, month, 1).strftime("%B") if month else None,
		"suggestions": current_suggestions,
		"alternative_month": datetime(year, alternative_month, 1).strftime("%B") if alternative_month else None,
		"alternative_suggestions": alternative_suggestions
	}



messages = [
	{"role":"system","content": "You are an assistant helping users plan vacations around public holidays."},
	{"role": "user", "content": "I have {leave_days_available} annual leave days left. Suggest how I can maximize my vacation time in {month} in {country_code}. The year is {year}."}

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
		}
	#}

]



response = client.chat.completions.create(model="GPT-4", messages = messages, functions=functions)
#print(response)

gpt_tools = response.choices[0].message.tool_calls


if gpt_tools:
	for gpt_tool in gpt_tools:
		function_name = gpt_tool.function.name
		function_parameters = gpt_tool.funcation.arguments

		if function_name == "create_vacation_plan":
			leave_days_available = function_parameters.get("leave_days_available")
			year = function_parameters.get("year")
			country_code = function_parameters.get("country_code")
			month = function_parameters.get("month")
			vacation_plan = create_vacation_plan(leave_days_available, year, country_code, month)
			print(vacation_plan)
else:
	print(response.choices[0].message.content)

