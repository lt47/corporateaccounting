import requests
import re
from bs4 import BeautifulSoup
import json


class SecExtract():
    def __init__(self, ticker) -> None:
        self.ticker = ticker

    '''The Central Index Key (CIK) is a 10 digit used by the SEC to identify 
        people and corps that have filed disclosures with them.'''

    def get_cik(self):
        ticker = self.ticker
        ticker = ticker.strip().lower()
        self.ticker = ticker
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

    # Next step is a function that returns a 10-K or 10-Q url based on the years provided
    def get_cik_urls(self, cik: str, years: str, filing_type='10-K'):
        # remove spaces from filing type arg
        filing_type.strip()
        filing_types = ['10-K', '10-Q']
        if filing_type not in filing_types:
            raise ValueError(
                f'Invalid filing type. Expected one of: {filing_types}')

        # Pagination details
        start_count = 0
        count_max = 100

        years_list = years.split(',')
        table_rows = self.get_edgar_rows(
            cik, filing_type, start_count, count_max)

        sec_urls_response = list()

        for year in years_list:
            year.strip()
            i = -1
            for tr in table_rows[1:]:
                i += 1
                single_response = dict()
                filing_row = tr.find_all('td')
                if year == re.split('-', filing_row[3].text)[0]:
                    filing_type = filing_row[0].text
                    filing_doc = f'https://www.sec.gov{filing_row[1].find_all("a")[0].get("href")}'
                    filing_date = filing_row[3].text
                    single_response.update(
                        {'filing_type': filing_type, 'filing_doc': filing_doc, 'filing_date': filing_date})
                    sec_urls_response.append(single_response)
                if filing_type == '10-K' and len(sec_urls_response) > 0:
                    break
                elif len(filing_row) == 0:
                    break
                elif i == len(table_rows[1:])-1:
                    table_rows = self.get_edgar_rows(
                        cik, filing_type, start_count+100, count_max)

        return json.dumps(sec_urls_response)

    # This function is used for pagination

    def get_edgar_rows(self, cik: str, filing_type: str, start_at: int, count_max: int):
        search_url = f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={filing_type}&dateb=&owner=exclude&search_text=&start={start_at}&count={count_max}'
        # Replace this header information with your own, per SEC policies https://www.sec.gov/os/accessing-edgar-data
        headers = {
            'User-Agent': 'YOUR INFO GOES HERE',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }

        # Parse entire HTML file
        html_content = requests.get(search_url, headers=headers).text
        sec_soup = BeautifulSoup(html_content, 'lxml')
        results_table = sec_soup.findAll('table', class_='tableFile2')[0]
        table_rows = results_table.find_all('tr')

        return table_rows


p = SecExtract("aapl")
# print(p.get_cik())
print(p.get_cik_urls(p.get_cik(), '2022', '10-K'))
