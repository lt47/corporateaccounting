import requests
import re
from bs4 import BeautifulSoup
import json

# The purpose of this class is to get the cik and relevant urls for each filing type.


class SecUrlExtract():
    def __init__(self, ticker) -> None:
        self.ticker = ticker

    '''The Central Index Key (CIK) is a 10 digit used by the SEC to identify 
        people and corps that have filed disclosures with them.'''

    def get_cik(self):
        ticker = self.ticker
        ticker = ticker.strip().lower()
        self.ticker = ticker
        cik = ''
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
            # print(f'${ticker} not found')
        return cik if cik != '' else f'${ticker} not found'

    # This function is used for pagination

    def get_edgar_rows(self, cik: str, filing_type: str, start_at: int, count_max: int):
        search_url = f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={filing_type}&dateb=&owner=exclude&search_text=&start={start_at}&count={count_max}'
        # Replace this header information with your own, per SEC policies https://www.sec.gov/os/accessing-edgar-data
        headers = {
            'User-Agent': 'Fort Seven laye@fort-seven.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }

        # Parse entire HTML file
        html_content = requests.get(search_url, headers=headers).text
        sec_soup = BeautifulSoup(html_content, 'lxml')
        results_table = sec_soup.findAll('table', class_='tableFile2')[0]
        table_rows = results_table.find_all('tr')

        return table_rows

    # Next step is a function that returns a 10-K or 10-Q url based on the years provided

    def get_filing_data(self, years: str, filing_type='10-K', cik='placeholder'):
        cik = self.get_cik()
        # remove spaces from filing type arg
        filing_type.strip()
        filing_types = ['10-K', '10-Q']
        if filing_type not in filing_types:
            raise ValueError(
                f'Invalid filing type. Expected one of: {filing_types}')

        # Pagination details
        start_count = 0
        count_max = 100

        # Getting rid of all spaces in string before converting to list.
        years = years.replace(' ', '')
        years_list = years.split(',')

        sec_urls_response = list()

        for year in years_list:
            # check if its a valid year.
            try:
                int(year)
            except:
                print(f'{year} is an invalid year.')
                break
            start_count = 0
            year.strip()
            table_rows = self.get_edgar_rows(
                cik, filing_type, start_count, count_max)
            i = -1
            url_tbl_rows = table_rows[1:]
            # The sole purpose of the while loop is to update the url_tbl_rows based on the current page.
            while i <= len(url_tbl_rows):
                if len(url_tbl_rows) == 0:
                    break
                for tr in url_tbl_rows:
                    i += 1
                    single_response = dict()
                    filing_row = tr.find_all('td')
                    if year == re.split('-', filing_row[3].text)[0]:
                        filing_type = filing_row[0].text
                        filing_page = f'https://www.sec.gov{filing_row[1].find_all("a")[0].get("href")}'
                        filing_date = filing_row[3].text
                        filing_doc = self.get_filing_doc(
                            filing_page, filing_type)
                        single_response.update(
                            {'filing_type': filing_type, 'filing_detail_page': filing_page, 'statement_url': filing_doc, 'filing_date': filing_date})
                        sec_urls_response.append(single_response)
                    elif filing_type == '10-K' and len(sec_urls_response) > 0:
                        break
                    elif len(filing_row) == 0:
                        break
                    elif i == len(url_tbl_rows)-1:
                        i = -1
                        start_count += 100
                        table_rows = self.get_edgar_rows(
                            cik, filing_type, start_count, count_max)
                        url_tbl_rows = table_rows[1:]
                        break

        return json.dumps(sec_urls_response)

    def get_filing_doc(self, filing_page: str, filing_type: str):
        # Replace this header information with your own, per SEC policies https://www.sec.gov/os/accessing-edgar-data

        headers = {
            'User-Agent': 'Fort Seven laye@fort-seven.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }

        # Parse entire HTML file
        html_content = requests.get(filing_page, headers=headers).text
        sec_soup = BeautifulSoup(html_content, 'lxml')
        results_table = sec_soup.findAll(
            'table', class_='tableFile')[0]
        doc_filing_rows = results_table.find_all('tr')[1:]
        filing_doc = ''
        alt_filing_doc = ''

        for tr in doc_filing_rows:
            file_element = tr.find_all('td')
            # Even when there is no ixbrl doc for older files, the td element still contains a link. Checking for text to workaround that.
            if filing_type == file_element[3].text and file_element[2].text != '':
                filing_doc = f'https://www.sec.gov/{file_element[2].find_all("a")[0].get("href")}'
            elif file_element[1].text == 'Complete submission text file':
                alt_filing_doc = f'https://www.sec.gov/{file_element[2].find_all("a")[0].get("href")}'

        return filing_doc if filing_doc != '' else alt_filing_doc


# p = SecUrlExtract("ibm")
# print(p.get_cik())
# print(p.get_filing_data('1994, 1995, 1996', '10-Q'))
