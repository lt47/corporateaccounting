import requests
import re
from bs4 import BeautifulSoup
import json
import sec_filing_docs
import logging
from xbrl.cache import HttpCache
from xbrl.instance import XbrlParser, XbrlInstance
from datetime import datetime, timedelta
import html2text


# The purpose of this class is to get information from financial statements.


class SecFinData():
    def get_fin_statement(self, filings: json):
        # everything below will be part of an xbrl function. There will be an if statement to determine the func to use based on file type
        filings = json.loads(filings)

        # decision making dict in place of if statement.
        statement_actions = {True: self.parse_xbrl_statement,
                             False: self.parse_txt_statement}

        statements_response = list()
        # have to loop through filings response
        for i in range(len(filings)):
            filing = filings[i]
            xbrl_bool = '/ix?doc=/' in filing['statement_url']
            statement_action = statement_actions.get(
                xbrl_bool, self.parse_html_txt_statement)

            single_response = statement_action(filing)

            statements_response.append(single_response) if len(
                single_response) > 0 else None

        return statements_response

    def parse_xbrl_statement(self, filing):
        single_statement_response = dict()
        schema_url = filing['statement_url'].replace('/ix?doc=/', '')
        filing_date = filing['filing_date']
        filing_date = datetime.strptime(filing_date, '%Y-%m-%d')
        # Replace this header information with your own, per SEC policies https://www.sec.gov/os/accessing-edgar-data

        cache: HttpCache = HttpCache('./cache')

        cache.set_headers({'From': 'laye@fort-seven.com',
                           'User-Agent': 'py-xbrl/2.1.0'})
        parser = XbrlParser(cache)

        inst: XbrlInstance = parser.parse_instance(schema_url)
        instjson = inst.json(override_fact_ids=True)
        instjson = json.loads(instjson)
        for j in range(len(instjson['facts'])):
            resp_period = datetime.strptime(
                instjson['facts'][f'f{j}']['dimensions']['period'].split('/')[0], '%Y-%m-%d')
            # need to import datetime module, convert date strings and find out if period is within 3 months of filing date
            if instjson['facts'][f'f{j}']['dimensions']['concept'] == 'Liabilities' and abs(filing_date-resp_period) <= timedelta(days=90):
                single_statement_response.update(
                    {'totalLiabilities': instjson['facts'][f'f{j}']['value'], 'filing_period': instjson['facts'][f'f{j}']['dimensions']['period']})

        return single_statement_response

    def parse_txt_statement(self, filing):
        single_statement_response = dict()
        schema_url = filing['statement_url'].replace('gov//', 'gov/')
        filing_date = filing['filing_date']
        filing_date = datetime.strptime(filing_date, '%Y-%m-%d')
        # Replace this header information with your own, per SEC policies https://www.sec.gov/os/accessing-edgar-data

        headers = {
            'User-Agent': 'Fort Seven laye@fort-seven.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }
        data = requests.get(schema_url, headers=headers).text

        currency_units = ['thousands', 'millions', 'billions']
        for index, line in enumerate(data.split('\n')):
            if 'Dollars in ' in line:
                currency_unit = re.findall(
                    r'Dollars in.*[n|d]s\b', line)[0].replace(')', '').split()[2].lower()
            if 'Total liabilities' in line or 'Total Liabilities' in line:
                # convert the total liabilities amount to an integer and convert it to currency unit
                total_liabilities = re.findall(
                    r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?(?!\d)', line)[0]

                pass

        return single_statement_response

    def parse_html_txt_statement(self, filing):
        single_statement_response = dict()
        schema_url = filing['statement_url'].replace('gov//', 'gov/')
        filing_date = filing['filing_date']
        filing_date = datetime.strptime(filing_date, '%Y-%m-%d')
        # Replace this header information with your own, per SEC policies https://www.sec.gov/os/accessing-edgar-data

        headers = {
            'User-Agent': 'Fort Seven laye@fort-seven.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }
        req = requests.get(schema_url, headers=headers).text
        url_txt = html2text.html2text(req)

        txt_json = dict()

        for index, line in enumerate(url_txt.split('\n')):
            command, description = line.strip().split(
                None, 1) if len(line.strip().split(None, 1)) > 1 else [None, None]
            txt_json[command] = description.strip(
            ) if command != None else None

        out_file = open('./testtxt.json', "w")
        json.dump(txt_json, out_file, indent=4, sort_keys=False)
        out_file.close()
        pass

        return single_statement_response


extract_obj = sec_filing_docs.SecUrlExtract("ibm")
p = SecFinData()
print(p.get_fin_statement(extract_obj.get_filing_data('1994', '10-Q')))
