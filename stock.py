# -*- coding: utf-8 -*-


from google.appengine.api import memcache
from google.appengine.ext import db


class Stock(db.Model):
    ticker = db.StringProperty()
    title = db.StringProperty()
    market_capital = db.FloatProperty()
    market_capital_date = db.DateProperty()
    bank_flag = db.BooleanProperty()
    ebit = db.FloatProperty()
    enterprise_value = db.FloatProperty()
    income = db.FloatProperty()
    tangible_asset = db.FloatProperty()
    ownership_interest = db.FloatProperty()
    net_profit = db.FloatProperty()
    earnings_date = db.DateProperty()
    
    
class StockView(object):
    
    def __init__(self):
        self.rank = 0
        self.roic_rank = 0
        self.roic = 0.0
        self.ebit_ev_rank = 0
        self.ebit_ev = 0.0
        self.ticker = ''
        self.title = ''
        self.market_capital = 0.0
        self.income = 0.0
        self.tangible_asset = 0.0
        self.ebit = 0.0
        self.enterprise_value = 0.0
        self.net_profit = 0.0
        self.ownership_interest = 0.0
        self.earnings_date = None
        self.pe = 0.0
        self.pb = 0.0
        self.roe = 0.0
        self.color = ""
        
    def format(self):
        if self.roe >= 15 and self.pe <=15:
            self.color = "#119911"
        else:
            self.color = "#991111"
        if self.enterprise_value != 0.0:
            self.ebit_ev = "%d%%" % (self.ebit_ev * 100)
        else:
            self.ebit_ev = "∞"
        if self.tangible_asset != 0.0:
            self.roic = "%d%%" % (self.roic * 100)
        else:
            self.roic = "∞"
        self.market_capital = "%.2f亿" % (self.market_capital / 100000000)
        self.roe = "%.1f%%" % (self.roe)
        self.pe = "%.1f" % (self.pe)
        self.pb = "%.1f" % (self.pb)
        self.earnings_date = self.earnings_date.strftime("%Y%m%d")
            
    def parse(self, s):
        self.ticker = s.ticker
        self.title = s.title
        self.market_capital = s.market_capital
        self.income = s.income
        self.tangible_asset = s.tangible_asset
        self.ebit = s.ebit
        self.enterprise_value = s.enterprise_value + s.market_capital
        self.net_profit = s.net_profit
        self.ownership_interest = s.ownership_interest
        self.earnings_date = s.earnings_date
        self.pe = self.market_capital / self.net_profit
        self.pb = self.market_capital / self.ownership_interest
        self.roe = self.net_profit * 100 / self.ownership_interest
        if self.tangible_asset != 0.0:
            self.roic = self.income / self.tangible_asset
        else:
            self.roic = '∞'
        if self.enterprise_value != 0.0:
            self.ebit_ev = self.ebit / self.enterprise_value
        else:
            self.ebit_ev = '∞'
            

def cmp_roic(s1, s2):
    if s1.tangible_asset * s2.tangible_asset == 0:
        if s1.tangible_asset == 0:
            return -1
        else:
            return 1
    else:
        return -cmp(s1.roic, s2.roic)
    

def cmp_ebit_ev(s1, s2):
    if s1.enterprise_value * s2.enterprise_value == 0:
        if s1.enterprise_value == 0:
            return -1
        else:
            return 1
    else:
        return -cmp(s1.ebit_ev, s2.ebit_ev)
    
    
def get(ticker):
    entry = memcache.get(ticker)
    if entry is None:
        entry = Stock.get_or_insert(ticker)
        memcache.add(ticker, entry)
    return entry


def put(entry):
    entry.put()
    memcache.set(entry.ticker, entry)
    