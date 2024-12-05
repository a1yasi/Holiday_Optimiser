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