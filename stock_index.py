# -*- coding: utf-8 -*-


import logging
from google.appengine.api import mail
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app


class StockIndex(db.Model):
    ss_000001 = db.StringProperty(indexed=False)
    sz_399001 = db.StringProperty(indexed=False)
    ss_000300 = db.StringProperty(indexed=False)
    sz_399300 = db.StringProperty(indexed=False)
    sz_399005 = db.StringProperty(indexed=False)
    sz_399006 = db.StringProperty(indexed=False)
    
        
def get():
    entry = StockIndex.get_or_insert('stock_index')
    return entry


def put(entry):
    entry.put()
    
    
class UpdateStockIndexHandler(webapp.RequestHandler):
    
    def __get_stock_index(self, symbol):
        url = 'http://finance.yahoo.com/d/quotes.csv?s=%s&f=l1' % (symbol)
        result = urlfetch.fetch(url=url)
        if result.status_code == 200:
            return result.content.strip()
        
    def __get_stock_indexes(self):
        entry = StockIndex(key_name='stock_index')
        entry.ss_000001 = self.__get_stock_index('000001.ss')
        entry.sz_399001 = self.__get_stock_index('399001.sz')
        entry.ss_000300 = self.__get_stock_index('000300.ss')
        entry.sz_399300 = self.__get_stock_index('399300.sz')
        entry.sz_399005 = self.__get_stock_index('399005.sz')
        entry.sz_399006 = self.__get_stock_index('399006.sz')
        return entry
    
    def __equal(self, old_index, new_index):
        if (old_index.ss_000001 == new_index.ss_000001
            and old_index.sz_399001 == new_index.sz_399001
            and old_index.ss_000300 == new_index.ss_000300
            and old_index.sz_399300 == new_index.sz_399300
            and old_index.sz_399005 == new_index.sz_399005
            and old_index.sz_399006 == new_index.sz_399006):
            return True
        else:
            return False
        
    def get(self):
        entry_old = get()
        entry_new = self.__get_stock_indexes()
        if not self.__equal(entry_old, entry_new):
            logging.info('It is on the exchange today')
            put(entry_new)
            taskqueue.add(url='/tasks/updatemarketcapital',
                          queue_name='updatemarketcapital',
                          method='GET')
        else:
            logging.info('It is not on the exchange today')
            mail.send_mail(sender="prstcsnpr@gmail.com",
                           to="prstcsnpr@gmail.com",
                           subject="神奇公式",
                           body='It is not on the exchange today')
            
            
application = webapp.WSGIApplication([('/tasks/updatestockindex', UpdateStockIndexHandler)],
                                     debug=True)


def main():
    run_wsgi_app(application)
    
    
if __name__ == '__main__':
    main()