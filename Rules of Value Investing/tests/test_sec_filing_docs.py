import unittest

from vigilantleadership.sec_filing_docs import SecUrlExtract


class SecUrlExtractTest(unittest.TestCase):
    def test_get_cik(self):
        securlextract = SecUrlExtract('ibm')
        self.assertEqual(securlextract.get_cik(), '0000051143')
        securlextract = SecUrlExtract('aapl')
        self.assertEqual(securlextract.get_cik(), '0000320193')
        securlextract = SecUrlExtract('msft')
        self.assertEqual(securlextract.get_cik(), '0000789019')
        securlextract = SecUrlExtract('nvda')
        self.assertEqual(securlextract.get_cik(), '0001045810')
        securlextract = SecUrlExtract('cvx')
        self.assertEqual(securlextract.get_cik(), '0000093410')
