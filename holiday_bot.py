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


