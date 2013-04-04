# -*- coding: utf-8 -*-


import datetime
import logging
from google.appengine.api import mail
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
import stock
    
    
class ShowStockInfoHandler(webapp.RequestHandler):
    
    def __magicformula(self, stocks):
        results = []
        for s in stocks:
            if s.market_capital == 0.0:
                logging.warn("The market capital is 0 for %s %s" % (s.ticker, s.title))
                continue
            if s.bank_flag == True:
                logging.warn("The stock (%s, %s) is a bank" % (s.ticker, s.title))
                continue
            if datetime.date.today().year - s.earnings_date.year > 2:
                logging.warn("The earnings is too old for %s %s %s" % (s.ticker, s.title, s.earnings_date.strftime("%Y%m%d")))
                continue
            sv = stock.StockView()
            try:
                sv.parse(s)
            except Exception as e:
                logging.exception("Parse stock (%s, %s) has %s" % (s.ticker, s.title, e))
                continue
            results.append(sv)
        results = sorted(results, cmp=lambda a, b : stock.cmp_roic(a, b))
        for i in range(len(results)):
            if i != 0 and stock.cmp_roic(results[i], results[i-1]) == 0:
                results[i].roic_rank = results[i-1].roic_rank
            else:
                results[i].roic_rank = i + 1
        results = sorted(results, cmp=lambda a, b : stock.cmp_ebit_ev(a, b))
        for i in range(len(results)):
            if i != 0 and stock.cmp_ebit_ev(results[i], results[i-1]) == 0:
                results[i].ebit_ev_rank = results[i-1].ebit_ev_rank
            else:
                results[i].ebit_ev_rank = i + 1
        results = sorted(results, key=lambda stock : stock.roic_rank + stock.ebit_ev_rank)
        p = 0.0
        b = 0.0
        for i in range(len(results)):
            if i != 0 and results[i].roic_rank + results[i].ebit_ev_rank == results[i-1].roic_rank + results[i-1].ebit_ev_rank:
                results[i].rank = results[i-1].rank
            else:
                results[i].rank = i + 1
            p += results[i].market_capital
            b += results[i].ownership_interest
            results[i].format()
        return p/b, results
    
    def __send_mail(self, content):
        mail.send_mail(sender="prstcsnpr@gmail.com",
                       to="prstcsnpr@gmail.com",
                       subject="神奇公式",
                       body=None,
                       html=content)
            
    def get(self):
        values = {}
        query = db.Query(stock.Stock)
        stocks = query.fetch(10000)
        pb, stocks = self.__magicformula(stocks)
        position=50
        while position<len(stocks):
            if stocks[position].rank == stocks[position - 1].rank:
                position = position + 1
            else:
                break
        values['stocks'] = stocks[0 : position]
        values['PB'] = "%.4f" % (pb)
        content = template.render('qmagicformula.html', values)
        self.__send_mail(content)
            
        
application = webapp.WSGIApplication([('/tasks/showstockinfo', ShowStockInfoHandler)],
                                     debug=True)


def main():
    run_wsgi_app(application)
    
    
if __name__ == '__main__':
    main()