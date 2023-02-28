# Getting Inflation rates from api-ninja
# Sign up and get your own API key to run this code here: https://api-ninjas.com
import json
import requests


def get_inflation_rate(country: str):
    api_url = f'https://api.api-ninjas.com/v1/inflation?country={country}'
    response = requests.get(
        api_url, headers={'X-Api-Key': 'YOUR_API_KEY'})
    if response.status_code == requests.codes.ok:
        inflation_rate = response.json()[0]['yearly_rate_pct']
        result = inflation_rate
    else:
        result = f"Error: {response.status_code},  {response.text}"
    return result


def main():
    # Pass in the desired Country Name as an argument to the get inflation rate function.
    print(
        f"The current American inflation rate is {get_inflation_rate('United States')}%")
    print(
        f"The current Canadian inflation rate is {get_inflation_rate('Canada')}%")


if __name__ == '__main__':
    main()
