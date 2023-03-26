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
        # Replace this header information with your own, per SEC policies https://www.sec.gov/os/accessing-edgar-data

        cache: HttpCache = HttpCache('./cache')

        cache.set_headers({'From': 'laye@fort-seven.com',
                          'User-Agent': 'py-xbrl/2.1.0'})
        parser = XbrlParser(cache)

        schema_url = "https://www.sec.gov/Archives/edgar/data/51143/000155837022015322/ibm-20220930x10q.htm"
        inst: XbrlInstance = parser.parse_instance(schema_url)
        terr = inst.json(override_fact_ids=True)
        pass

        """for i in filings:
            filing_detail = i['statement_page']
            temp = ixbrl_parse"""


extract_obj = sec_filing_docs.SecUrlExtract("ibm")
p = SecFinData()
p.get_fin_statement(extract_obj.get_filing_data('1995', '10-Q'))
