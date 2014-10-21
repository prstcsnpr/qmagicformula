# -*- coding: utf-8 -*-


from google.appengine.api import memcache
from google.appengine.ext import db


class StockResult(db.Model):
    content = db.TextProperty(indexed=False)
    
def get_html(ticker):
    key = 'html' + ticker
    entry = memcache.get(key)
    if entry is None:
        entry = StockResult.get_or_insert(key)
        memcache.add(key, entry)
    return entry
        
def set_html(ticker, entry):
    key = 'html' + ticker
    entry.put()
    memcache.set(key, entry)
