import requests
import re


class SecExtract():
    def __init__(self, ticker) -> None:
        self.ticker = ticker

    '''The Central Index Key (CIK) is a 10 digit used by the SEC to identify 
        people and corps that have filed disclosures with them.'''

    def get_cik(self):
        ticker = self.ticker
        ticker = ticker.strip().lower()
        # Check the SEC ticker file for a match.
        response = requests.get('https://www.sec.gov/include/ticker.txt')
        data = response.text
        for index, line in enumerate(data.split('\n')):
            if ticker in line:
                cik = re.split('\t', line)[1]
                '''The following line ensures that the CIK is exactly 
                    10 digits with leading zeros if necessary.'''
                cik = '0'*(10-len(cik)) + cik if len(cik) < 10 else cik
                break
            # This will eventually be replaced with a logger.
            print(f'${ticker} not found')
        return cik

    # Next step is a function that returns a 10-K or 10-Q url based on a date range


# p = SecExtract("aapl")
# print(p.get_cik())
