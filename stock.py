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
    
    
def get(ticker):
    entry = memcache.get(ticker)
    if entry is None:
        entry = Stock.get_or_insert(ticker)
        memcache.add(ticker, entry)
    return entry


def put(entry):
    entry.put()
    memcache.set(entry.ticker, entry)
    