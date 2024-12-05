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
	return [holiday for holiday in holidays if datetime.strptime(holiday["date"], "%Y-%m-%d").month == month]

#suggest leave days for vacation
# genarate vacation suggest based on public holidays and leave days 
def genarate_vacation_suggestions(leave_days_available, holidays, min_days=4, max_days=14):
	suggestions = []
	for holiday in holidays:
		holiday_date = datetime.strptime(holiday["date"],"%Y-%m-%d")

#short vacation 
#calculate the start and end date for short vacation
		if leave_days_available >= min_days:
			suggestions.append(suggest_vacation(holiday_date,min_days, "short vacation"))

#long vacation calcutate the start and end date for long vacation
		if leave_days_available >= max_days:
			suggestions.append(suggest_vacation(holiday_date, max_days, "long vacation"))

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
	}

#genarate vacation plan and combaining holidays and leave days
def create_vacation_plan(leave_days_available, year, country_code="GB", month=None):
	holidays = get_holidays(year, country_code)

	if not holidays:
		return "No public holidays found for the {year}"

	if month:
		holidays = filter_holidays_by_month(holidays, month)
		if not holidays:
			return "No public holidays found for {month}/{year}."

	

	return genarate_vacation_suggestions(leave_days_available, holidays)

print(create_vacation_plan(4, 2025, "GB", 6))