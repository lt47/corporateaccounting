# Getting Interest rates from api-ninja
# Sign up and get your own API key to run this code here: https://api-ninjas.com
import json
import requests


def get_interest_rate(central_bank: str):
    api_url = f'https://api.api-ninjas.com/v1/interestrate?name={central_bank}'
    response = requests.get(
        api_url, headers={'X-Api-Key': 'YOUR_API_KEY'})
    if response.status_code == requests.codes.ok:
        interest_rate = response.json()['central_bank_rates'][0]['rate_pct']
        result = interest_rate
    else:
        result = f"Error: {response.status_code},  {response.text}"
    return result


def main():
    # Pass in the desired Central Bank abbreviation as an argument to the get interest rate function.
    print(f"The current American interest rate is {get_interest_rate('FED')}%")
    print(f"The current Canadian interest rate is {get_interest_rate('BOC')}%")


if __name__ == '__main__':
    main()
