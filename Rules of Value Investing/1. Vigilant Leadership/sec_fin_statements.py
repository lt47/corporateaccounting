import requests
import re
from bs4 import BeautifulSoup
import json
import sec_filing_docs
import logging
from xbrl.cache import HttpCache
from xbrl.instance import XbrlParser, XbrlInstance
from datetime import datetime, timedelta


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
                xbrl_bool, self.parse_html_statement)

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
            if instjson['facts'][f'f{j}']['dimensions']['concept'] == 'Liabilities' and abs(filing_date-resp_period) <= timedelta(days=120):
                total_liabilities = instjson['facts'][f'f{j}']['value']
            elif instjson['facts'][f'f{j}']['dimensions']['concept'] == 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest' and 'StatementEquityComponentsAxis' not in instjson['facts'][f'f{j}']['dimensions'] and abs(filing_date-resp_period) <= timedelta(days=90):
                total_shareholders_equity = instjson['facts'][f'f{j}']['value']
            elif instjson['facts'][f'f{j}']['dimensions']['concept'] == 'AssetsCurrent' and abs(filing_date-resp_period) <= timedelta(days=120):
                total_current_assets = instjson['facts'][f'f{j}']['value']
            elif instjson['facts'][f'f{j}']['dimensions']['concept'] == 'LiabilitiesCurrent' and abs(filing_date-resp_period) <= timedelta(days=120):
                total_current_liabilities = instjson['facts'][f'f{j}']['value']
            elif instjson['facts'][f'f{j}']['dimensions']['concept'] == 'NetIncomeLoss' and abs(filing_date-resp_period) <= timedelta(days=120):
                net_income_loss = instjson['facts'][f'f{j}']['value']

        debt_to_equity = round(
            float(total_liabilities/total_shareholders_equity), 2)
        current_ratio = round(
            float(total_current_assets/total_current_liabilities), 2)
        roe = round(
            float(net_income_loss/total_shareholders_equity), 2)
        single_statement_response.update(
            {'totalLiabilities': total_liabilities, 'totalShareholdersEquity': total_shareholders_equity, 'debtToEquity': debt_to_equity, 'totalCurrentAssets': total_current_assets, 'totalCurrentLiabilities': total_current_liabilities, 'currentRatio': current_ratio, 'netIncomeOrLoss': net_income_loss, 'returnOnEquity': roe})

        return single_statement_response

    def parse_txt_statement(self, filing):
        single_statement_response = dict()
        schema_url = filing['statement_url'].replace('gov//', 'gov/')
        if 'txt' not in schema_url:
            return self.parse_html_statement(filing)

        filing_date = filing['filing_date']
        filing_date = datetime.strptime(filing_date, '%Y-%m-%d')
        # Replace this header information with your own, per SEC policies https://www.sec.gov/os/accessing-edgar-data

        headers = {
            'User-Agent': 'Fort Seven laye@fort-seven.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }
        data = requests.get(schema_url, headers=headers).text

        currency_units = {'thousands': 1000,
                          'millions': 1000000, 'billions': 1000000000}
        total_liabilities = ''
        total_shareholders_equity = ''
        total_current_assets = ''
        total_current_liabilities = ''
        pref_stock_dividends = ''
        net_income_loss_commonshares = ''
        net_income_loss = ''
        for index, line in enumerate(data.split('\n')):
            line = line.lstrip()
            # total_liab_check = re.findall(r'(Total [l|L][a-zA-Z\s]*\b)', line)
            total_liab_check = re.findall(
                r'^(Total Liabilities\b)', line, re.IGNORECASE)
            total_sheq_check = re.findall(
                r"^(Total [s|S][a-zA-Z\s']*\b)", line)
            total_currass_check = re.findall(
                r"^(Total Current Assets\b)", line, re.IGNORECASE)
            total_currliab_check = re.findall(
                r"^(Total Current Liabilities\b)", line, re.IGNORECASE)
            pref_stockdiv_check = re.findall(
                r"^(Preferred stock dividends\b)", line, re.IGNORECASE)
            net_incomelosscomm_check = re.findall(
                r"^(common shareholders\b)", line, re.IGNORECASE)
            if 'Dollars in ' in line:
                currency_unit = re.findall(
                    r'Dollars in.*[n|d]s\b', line)[0].replace(')', '').split()[2].lower()
            elif len(total_liab_check) > 0 and total_liab_check[0].rstrip().lower() in ('total liabilities'):
                total_liabilities = re.findall(
                    r'\(?\b\d{1,3}(?:,\d{3})*(?:\.\d+)?(?!\d)\)?', line)[0]
                total_liabilities = f"-{total_liabilities.replace('(','').replace(')','')}" if '(' in total_liabilities else total_liabilities
                total_liabilities = int(total_liabilities.replace(
                    ',', '')) * currency_units[currency_unit]
            elif len(total_sheq_check) > 0 and total_sheq_check[0].rstrip().lower() in ("total stockholders' equity", "total shareholders' equity"):
                total_shareholders_equity = re.findall(
                    r'\(?\b\d{1,3}(?:,\d{3})*(?:\.\d+)?(?!\d)\)?', line)[0]
                total_shareholders_equity = f"-{total_shareholders_equity.replace('(','').replace(')','')}" if '(' in total_shareholders_equity else total_shareholders_equity
                total_shareholders_equity = int(total_shareholders_equity.replace(
                    ',', '')) * currency_units[currency_unit]
            elif len(total_currass_check) > 0 and total_currass_check[0].rstrip().lower() in ("total current assets"):
                total_current_assets = re.findall(
                    r'\(?\b\d{1,3}(?:,\d{3})*(?:\.\d+)?(?!\d)\)?', line)[0]
                total_current_assets = f"-{total_current_assets.replace('(','').replace(')','')}" if '(' in total_current_assets else total_current_assets
                total_current_assets = int(total_current_assets.replace(
                    ',', '')) * currency_units[currency_unit]
            elif len(total_currliab_check) > 0 and total_currliab_check[0].rstrip().lower() in ("total current liabilities"):
                total_current_liabilities = re.findall(
                    r'\(?\b\d{1,3}(?:,\d{3})*(?:\.\d+)?(?!\d)\)?', line)[0]
                total_current_liabilities = f"-{total_current_liabilities.replace('(','').replace(')','')}" if '(' in total_current_liabilities else total_current_liabilities
                total_current_liabilities = int(total_current_liabilities.replace(
                    ',', '')) * currency_units[currency_unit]
            elif len(pref_stockdiv_check) > 0 and pref_stockdiv_check[0].rstrip().lower() in ("preferred stock dividends"):
                pref_stock_dividends = re.findall(
                    r'\(?\b\d{1,3}(?:,\d{3})*(?:\.\d+)?(?!\d)\)?', line)[0]
                pref_stock_dividends = f"-{pref_stock_dividends.replace('(','').replace(')','')}" if '(' in pref_stock_dividends else pref_stock_dividends
            elif len(net_incomelosscomm_check) > 0 and net_incomelosscomm_check[0].rstrip().lower() in ("common shareholders"):
                net_income_loss_commonshares = re.findall(
                    r'\(?\b\d{1,3}(?:,\d{3})*(?:\.\d+)?(?!\d)\)?', line)[0]
                net_income_loss_commonshares = f"-{net_income_loss_commonshares.replace('(','').replace(')','')}" if '(' in net_income_loss_commonshares else net_income_loss_commonshares

        net_income_loss = (int(pref_stock_dividends.replace(',', '')) + int(
            net_income_loss_commonshares.replace(',', ''))) * currency_units[currency_unit]
        debt_to_equity = round(
            float(total_liabilities/total_shareholders_equity), 2)
        current_ratio = round(
            float(total_current_assets/total_current_liabilities), 2)
        roe = round(
            float(net_income_loss/total_shareholders_equity), 2)
        single_statement_response.update(
            {'totalLiabilities': total_liabilities, 'totalShareholdersEquity': total_shareholders_equity, 'debtToEquity': debt_to_equity, 'totalCurrentAssets': total_current_assets, 'totalCurrentLiabilities': total_current_liabilities, 'currentRatio': current_ratio, 'netIncomeOrLoss': net_income_loss, 'returnOnEquity': roe})

        return single_statement_response

    def parse_html_statement(self, filing):
        single_statement_response = dict()
        schema_url = filing['statement_url'].replace('gov//', 'gov/')
        filing_date = filing['filing_date']
        filing_date = datetime.strptime(filing_date, '%Y-%m-%d')

        currency_units = {'thousands': 1000,
                          'millions': 1000000, 'billions': 1000000000}
        total_liabilities = ''
        total_shareholders_equity = ''
        total_current_assets = ''
        total_current_liabilities = ''
        net_income_loss = ''

        # Replace this header information with your own, per SEC policies https://www.sec.gov/os/accessing-edgar-data
        headers = {
            'User-Agent': 'Fort Seven laye@fort-seven.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }
        req = requests.get(schema_url, headers=headers).text
        sec_soup = BeautifulSoup(req, 'lxml')
        results_table = sec_soup.findAll(
            'table')

        for t in range(len(results_table)):
            rows = results_table[t].find_all('tr')[1:]
            for tr in rows:
                element = tr.find_all('td')
                if 'dollars in ' in element[0].text.lower():
                    currency_unit = element[0].text.replace(
                        '(', '').replace(')', '').replace('\n', '').replace('\n ', '').lower().split(' ')[2]
                elif len(element) > 2 and 'total liabilities' == element[1].text.strip().replace('\n ', '').lower() and total_liabilities == '':
                    total_liabilities = element[4].text.replace(
                        '\n', '').replace('\n ', '')
                    total_liabilities = f"-{total_liabilities.replace('(','').replace(')','')}" if '(' in total_liabilities else total_liabilities
                    total_liabilities = int(total_liabilities.replace(
                        ',', '')) * currency_units[currency_unit]
                elif 'total liabilities and equity' == element[0].text.strip().replace('\n ', '').lower() and total_shareholders_equity == '':
                    total_shareholders_equity = element[3].text.replace(
                        '\n', '').replace('\n ', '')
                    total_shareholders_equity = f"-{total_shareholders_equity.replace('(','').replace(')','')}" if '(' in total_shareholders_equity else total_shareholders_equity
                    total_shareholders_equity = int(total_shareholders_equity.replace(
                        ',', '')) * currency_units[currency_unit]
                elif len(element) > 2 and 'total current assets' == element[1].text.strip().replace('\n ', '').lower() and total_current_assets == '':
                    total_current_assets = element[4].text.replace(
                        '\n', '').replace('\n ', '')
                    total_current_assets = f"-{total_current_assets.replace('(','').replace(')','')}" if '(' in total_current_assets else total_current_assets
                    total_current_assets = int(total_current_assets.replace(
                        ',', '')) * currency_units[currency_unit]
                elif len(element) > 2 and 'total current liabilities' == element[1].text.strip().replace('\n ', '').lower() and total_current_liabilities == '':
                    total_current_liabilities = element[4].text.replace(
                        '\n', '').replace('\n ', '')
                    total_current_liabilities = f"-{total_current_liabilities.replace('(','').replace(')','')}" if '(' in total_current_liabilities else total_current_liabilities
                    total_current_liabilities = int(total_current_liabilities.replace(
                        ',', '')) * currency_units[currency_unit]
                elif 'net income' == element[0].text.strip().replace('\n ', '').lower() and net_income_loss == '':
                    net_income_loss = element[3].text.replace(
                        '\n', '').replace('\n ', '')
                    net_income_loss = f"-{net_income_loss.replace('(','').replace(')','')}" if '(' in net_income_loss else net_income_loss
                    net_income_loss = int(net_income_loss.replace(
                        ',', '')) * currency_units[currency_unit]

        total_shareholders_equity = total_shareholders_equity - total_liabilities
        debt_to_equity = round(
            float(total_liabilities/total_shareholders_equity), 2)
        current_ratio = round(
            float(total_current_assets/total_current_liabilities), 2)
        roe = round(
            float(net_income_loss/total_shareholders_equity), 2)
        single_statement_response.update(
            {'totalLiabilities': total_liabilities, 'totalShareholdersEquity': total_shareholders_equity, 'debtToEquity': debt_to_equity, 'totalCurrentAssets': total_current_assets, 'totalCurrentLiabilities': total_current_liabilities, 'currentRatio': current_ratio, 'netIncomeOrLoss': net_income_loss, 'returnOnEquity': roe})

        return single_statement_response


extract_obj = sec_filing_docs.SecUrlExtract("ibm")
p = SecFinData()
print(p.get_fin_statement(extract_obj.get_filing_data('2014', '10-Q')))
