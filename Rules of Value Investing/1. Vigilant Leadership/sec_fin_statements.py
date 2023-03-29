import requests
import re
from bs4 import BeautifulSoup
import json
import sec_filing_docs
import logging
from xbrl.cache import HttpCache
from xbrl.instance import XbrlParser, XbrlInstance

# The purpose of this class is to get information from financial statements.


class SecFinData():
    def get_fin_statement(self, filings: json):
        # everything below will be part of an xbrl function. There will be an if statement to determine the func to use based on file type
        filings = json.loads(filings)
        # have to loop through filings response
        for i in range(len(filings)):
            schema_url = filings[i]['statement_url'].replace('/ix?doc=/', '')
            filing_date = filings[i]['filing_date']
            # Replace this header information with your own, per SEC policies https://www.sec.gov/os/accessing-edgar-data

            cache: HttpCache = HttpCache('./cache')

            cache.set_headers({'From': 'laye@fort-seven.com',
                               'User-Agent': 'py-xbrl/2.1.0'})
            parser = XbrlParser(cache)

            # schema_url = "https://www.sec.gov/Archives/edgar/data/51143/000155837022015322/ibm-20220930x10q.htm"
            inst: XbrlInstance = parser.parse_instance(schema_url)
            instjson = inst.json(override_fact_ids=True)
            instjson = json.loads(instjson)
            # inst.json('./test.json')
            statements_response = list()

            for j in range(len(instjson['facts'])):
                single_statement_response = dict()
                # need to import datetime module, convert date strings and find out if period is within 3 months of filing date
                if instjson['facts'][f'f{j}']['dimensions']['concept'] == 'Liabilities' and filing_date in instjson['facts'][f'f{j}']['dimensions']['period']:
                    single_statement_response.update(
                        {'totalLiabilities': instjson['facts'][f'f{j}']['value'], 'filing_date': instjson['facts'][f'f{j}']['dimensions']['period']})
                statements_response.append(single_statement_response) if len(
                    single_statement_response) > 0 else None


extract_obj = sec_filing_docs.SecUrlExtract("ibm")
p = SecFinData()
p.get_fin_statement(extract_obj.get_filing_data('2021', '10-Q'))
