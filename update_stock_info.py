#coding=utf8


import datetime
import json
import logging
import re
import string
import sys
import urllib
from google.appengine.api.labs import taskqueue
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import exchange_rate
import stock


class UpdateStockInfoHandler(webapp.RequestHandler):
    
    def get(self):
        taskqueue.add(url='/tasks/updateallmarketcapital')
        print 'OK'
        
        
class UpdateAllMarketCapitalHandler(webapp.RequestHandler):

    def __get_exchange_rate(self, area):
        url = "http://download.finance.yahoo.com/d/quotes.html?s=%sCNY=X&f=l1" % area
        result = urlfetch.fetch(url=url)
        if result.status_code == 200:
            return result.content.strip()
    
    def __get_page_content(self):
        url = 'https://www.google.com.hk/finance?output=json&start=0&num=10000&noIL=1&q=[%28%28exchange%20%3D%3D%20%22SHE%22%29%20%7C%20%28exchange%20%3D%3D%20%22SHA%22%29%29%20%26%20%28market_cap%20%3E%3D%200%29%20%26%20%28market_cap%20%3C%3D%2010000000000000000%29]&restype=company&gl=cn'
        result = urlfetch.fetch(url=url)
        if result.status_code == 200:
            data = result.content
            data = data.replace('&quot;', '\\"').replace('&amp;', '&').replace('&gt;','>').replace('&lt;', '<')
            data = data.replace('\\x22','\\"').replace('\\x26','&').replace('\\x3E','>').replace('\\x3C','<')
            data = data.replace('\\x27','\'').replace('\\x2F','\/').replace('\\x3B',';')
            return data
        
    def post(self):
        usd = exchange_rate.get().usd
        hkd = exchange_rate.get().hkd
        data = self.__get_page_content()
        data = json.loads(data)
        count=0
        for stock in data['searchresults']:
            if stock['ticker'].find('399')==0 or stock['ticker'].find('000')==0 and stock['exchange']=='SHA':
                continue
            taskqueue.add(url='/tasks/updatesinglemarketcapital',
                          #queue_name='queue'+str(count % 10),
                          params={'ticker' : stock['ticker'],
                                  'title' : stock['title'],
                                  'exchange' : stock['exchange'],
                                  'local_currency_symbol' : stock['local_currency_symbol'],
                                  'value' : stock['columns'][0]['value'],
                                  'usd' : usd,
                                  'hkd' : hkd})
            count += 1
        

class UpdateSingleMarketCapitalHandler(webapp.RequestHandler):
    
    def __get_page_content(self, ticker, exchange):
        if exchange == 'SHA':
            query = 'sh' + ticker
        elif exchange == 'SHE':
            query = 'sz' + ticker
        else:
            query = ''
            logging.warn('Error exchange: ' + exchange)
        url = "http://qt.gtimg.cn/S?q=" + query
        result = urlfetch.fetch(url=url)
        if result.status_code == 200:
            data = result.content
            data = data.split('~')
            return string.atof(data[len(data) - 5]) * 100000000
        return 0.0
        
    def __change_unit(self, symbol):
        symbol = symbol.encode('UTF-8')
        if symbol.find('-') > -1:
            return 0.0
        m = re.search(r'\d+\.\d*', symbol)
        number = string.atof(symbol[m.start() : m.end()])
        unit = symbol[m.end():]
        if unit == '亿':
            return number * 10000 * 10000
        elif unit == '万':
            return number * 10000
        elif unit == '万亿':
            return number * 10000 * 10000 * 10000
        else:
            logging.warn('unit is wrong')
            return 0.0
        
    def __get_market_capital(self):
        ticker = self.request.get('ticker')
        exchange = self.request.get('exchange')
        local_currency_symbol = self.request.get('local_currency_symbol')
        usd = self.request.get('usd')
        hkd = self.request.get('hkd')
        value = self.__get_page_content(ticker, exchange)
        if value == 0:
            value = self.__change_unit(self.request.get('value'))
        if local_currency_symbol.encode('UTF-8') == "￥":
            rate = 1
        elif local_currency_symbol == 'US$':
            rate = string.atof(usd)
        elif local_currency_symbol == 'HK$':
            rate = string.atof(hkd)
        elif local_currency_symbol == '-' and ticker.find('900') == -1 and ticker.find('200') == -1:
            rate = 1
        else:
            rate = 0
            logging.warn("Invalid Exchangerate: %s %s" % (type(ticker), local_currency_symbol))
        return value * rate
    
    def __update_market_capital(self, market_capital):
        ticker = self.request.get('ticker')
        title = self.request.get('title')
        entry = stock.get(ticker)
        entry.ticker = ticker
        entry.title = title
        entry.market_capital = market_capital
        entry.market_capital_date = datetime.date.today()
        stock.put(entry)
    
    def post(self):
        ticker = self.request.get('ticker')
        market_capital = self.__get_market_capital()
        self.__update_market_capital(market_capital)
#            logging.warn('Market capital is %s for %s' % (market_capital, ticker))
        taskqueue.add(url='/tasks/updateearnings', params={'ticker' : ticker})
        

class UpdateEarningsHandler(webapp.RequestHandler):
    
    def __get_page_content(self, url):
        result = urlfetch.fetch(url=url)
        if result.status_code == 200:
            data = result.content
        map = {}
        lines = data.decode('GBK').encode('UTF-8').split('\n')
        for line in lines:
            fields = line.split('\t')
            for i in range(len(fields) - 2):
                if i + 1 not in map:
                    map[i + 1] = {}
                map[i + 1][fields[0]] = fields[i + 1]
        results = {}
        for k in map:
            if '报表日期' in map[k]:
                results[map[k]['报表日期']] = map[k]
        return results
    
    def __get_profit_earnings(self):
        ticker = self.request.get('ticker')
        url = "http://money.finance.sina.com.cn/corp/go.php/vDOWN_ProfitStatement/displaytype/4/stockid/%s/ctrl/all.phtml" % (ticker)
        return self.__get_page_content(url)
    
    def __get_balance_earnings(self):
        ticker = self.request.get('ticker')
        url = "http://money.finance.sina.com.cn/corp/go.php/vDOWN_BalanceSheet/displaytype/4/stockid/%s/ctrl/all.phtml" % (ticker)
        return self.__get_page_content(url)
    
    def __get_ebit(self, profit):
        operating_income = string.atof(profit['营业收入'])
        operating_costs = string.atof(profit['营业成本'])
        business_tax_and_additional = string.atof(profit['营业税金及附加'])
        management_expenses = string.atof(profit['管理费用'])
        sales_expenses = string.atof(profit['销售费用'])
        investment_income = string.atof(profit['其中:对联营企业和合营企业的投资收益'])
        ebit = (operating_income - operating_costs - business_tax_and_additional - management_expenses - sales_expenses + investment_income)
        return ebit
    
    def __get_income(self, profit):
        operating_income = string.atof(profit['营业收入'])
        operating_costs = string.atof(profit['营业成本'])
        business_tax_and_additional = string.atof(profit['营业税金及附加'])
        management_expenses = string.atof(profit['管理费用'])
        sales_expenses = string.atof(profit['销售费用'])
        investment_income = string.atof(profit['其中:对联营企业和合营企业的投资收益'])
        income = (operating_income - operating_costs - business_tax_and_additional - management_expenses - sales_expenses)
        return income
    
    def __get_enterprise_value(self, balance):
        current_assets = string.atof(balance['流动资产合计'])
        current_liabilities = string.atof(balance['流动负债合计'])
        short_term_borrowing = string.atof(balance['短期借款'])
        notes_payable = string.atof(balance['应付票据'])
        a_maturity_of_non_current_liabilities = string.atof(balance['一年内到期的非流动负债'])
        cope_with_short_term_bond = string.atof(balance['应付短期债券'])
        monetary_fund = string.atof(balance['货币资金'])
        long_term_borrowing = string.atof(balance['长期借款'])
        bonds_payable = string.atof(balance['应付债券'])
        minority_equity = string.atof(balance['少数股东权益'])
        available_for_sale_financial_assets = string.atof(balance['可供出售金融资产'])
        hold_expires_investment = string.atof(balance['持有至到期投资'])
        delay_income_tax_liabilities = string.atof(balance['递延所得税负债'])
        excess_cash = max(0, monetary_fund - max(0, current_liabilities - current_assets + monetary_fund))
        enterprise_value = (short_term_borrowing + notes_payable + a_maturity_of_non_current_liabilities
                            + cope_with_short_term_bond + long_term_borrowing
                            + bonds_payable + minority_equity
                            - available_for_sale_financial_assets - hold_expires_investment
                            + delay_income_tax_liabilities - excess_cash)
        return enterprise_value
    
    def __get_tangible_asset(self, balance):
        current_assets = string.atof(balance['流动资产合计'])
        current_liabilities = string.atof(balance['流动负债合计'])
        short_term_borrowing = string.atof(balance['短期借款'])
        notes_payable = string.atof(balance['应付票据'])
        a_maturity_of_non_current_liabilities = string.atof(balance['一年内到期的非流动负债'])
        cope_with_short_term_bond = string.atof(balance['应付短期债券'])
        net_value_of_fixed_assets = string.atof(balance['固定资产净值'])
        investment_real_estate = string.atof(balance['投资性房地产'])
        monetary_fund = string.atof(balance['货币资金'])
        excess_cash = max(0, monetary_fund - max(0, current_liabilities - current_assets + monetary_fund))
        tangible_asset = (current_assets - current_liabilities
                          + short_term_borrowing + notes_payable
                          + a_maturity_of_non_current_liabilities
                          + cope_with_short_term_bond + net_value_of_fixed_assets
                          + investment_real_estate - excess_cash)
        return tangible_asset
    
    def __get_net_profit(self, profit):
        net_profit = string.atof(profit['四、净利润'])
        return net_profit
    
    def __get_ownership_interest(self, balance):
        ownership_interest = string.atof(balance['所有者权益(或股东权益)合计'])
        return ownership_interest
        
    def __update_earnings(self):
        ticker = self.request.get('ticker')
        entry = stock.get(ticker)
        if entry.bank_flag:
            logging.info("%s is a bank" % (ticker))
            return
        balance = self.__get_balance_earnings()
        profit = self.__get_profit_earnings()
        year = datetime.date.today().year
        for i in range(3):
            earnings_date = self.__get_recent_earnings_date(year - i, balance, profit)
            if earnings_date is not None:
                break
        if earnings_date is None:
            logging.warn('There is no earnings date for %s' % (ticker))
            return
        else:
            try:
                bank_flag = False
                if earnings_date.month == 12:
                    this_earnings_date = earnings_date.strftime('%Y%m%d')
                    ebit = self.__get_ebit(profit[this_earnings_date])
                    income = self.__get_income(profit[this_earnings_date])
                    enterprise_value = self.__get_enterprise_value(balance[this_earnings_date])
                    tangible_asset = self.__get_tangible_asset(balance[this_earnings_date])
                    ownership_interest = self.__get_ownership_interest(balance[this_earnings_date])
                    net_profit = self.__get_net_profit(profit[this_earnings_date])
                else:
                    this_earnings_date = earnings_date.strftime('%Y%m%d')
                    last_earnings_date = earnings_date.replace(earnings_date.year - 1).strftime('%Y%m%d')
                    last_year_date = datetime.date(year=earnings_date.year - 1, month=12, day=31).strftime('%Y%m%d')
                    enterprise_value = self.__get_enterprise_value(balance[this_earnings_date])
                    tangible_asset = self.__get_tangible_asset(balance[this_earnings_date])
                    ownership_interest = self.__get_ownership_interest(balance[this_earnings_date])
                    ebit = (self.__get_ebit(profit[this_earnings_date]) 
                            + self.__get_ebit(profit[last_year_date]) 
                            - self.__get_ebit(profit[last_earnings_date]))
                    income = (self.__get_income(profit[this_earnings_date]) 
                              + self.__get_income(profit[last_year_date]) 
                              - self.__get_income(profit[last_earnings_date]))
                    net_profit = (self.__get_net_profit(profit[this_earnings_date]) 
                                  + self.__get_net_profit(profit[last_year_date]) 
                                  - self.__get_net_profit(profit[last_earnings_date]))
            except KeyError as ke:
                logging.exception(ke)
                bank_flag = True
                entry.bank_flag = bank_flag
                entry.earnings_date = earnings_date
                stock.put(entry)
                logging.info("Firstly %s is a bank" % (ticker))
                return
            entry.bank_flag = bank_flag
            entry.earnings_date = earnings_date
            entry.ebit = ebit
            entry.income = income
            entry.enterprise_value = enterprise_value
            entry.tangible_asset = tangible_asset
            entry.ownership_interest = ownership_interest
            entry.net_profit = net_profit
            stock.put(entry)
        
    def __get_recent_earnings_date(self, year, balance, profit):
        q4 = datetime.date(year=year, month=12, day=31)
        q3 = datetime.date(year=year, month=9, day=30)
        q2 = datetime.date(year=year, month=6, day=30)
        q1 = datetime.date(year=year, month=3, day=31)
        last_year= year - 1
        if q4.strftime('%Y%m%d') in balance and q4.strftime('%Y%m%d') in profit:
            return q4
        elif q4.replace(year=last_year).strftime('%Y%m%d') in balance and q4.replace(year=last_year).strftime('%Y%m%d') in profit:
            if q3.strftime('%Y%m%d') in balance and q3.strftime('%Y%m%d') in profit and q3.replace(year=last_year).strftime('%Y%m%d') in balance and q3.replace(year=last_year).strftime('%Y%m%d') in profit:
                return q3
            elif q2.strftime('%Y%m%d') in balance and q2.strftime('%Y%m%d') in profit and q2.replace(year=last_year).strftime('%Y%m%d') in balance and q2.replace(year=last_year).strftime('%Y%m%d') in profit:
                return q2
            elif q1.strftime('%Y%m%d') in balance and q1.strftime('%Y%m%d') in profit and q1.replace(year=last_year).strftime('%Y%m%d') in balance and q1.replace(year=last_year).strftime('%Y%m%d') in profit:
                return q1
            else:
                return None
        else:
            return None
        
    def __need_update_earnings(self):
        ticker = self.request.get('ticker')
        entry = stock.get(ticker)
        earnings_date = entry.earnings_date
        if earnings_date is None:
            return True
        today = datetime.date.today()
        logging.info(str(today)+' '+str(earnings_date))
        if (today.month <= 3 and today.month >= 1
            and earnings_date.month == 12 and earnings_date.year + 1 == today.year):
            return False
        elif (today.month <= 6 and today.month >= 4
              and earnings_date.month == 3 and earnings_date.year == today.year):
            return False
        elif (today.month <= 9 and today.month >= 7
              and earnings_date.month == 6 and earnings_date.year == today.year):
            return False
        elif (today.month <= 12 and today.month >= 10
              and earnings_date.month == 9 and earnings_date.year == today.year):
            return False
        else:
            return True
            
    def post(self):
        if self.__need_update_earnings():
            ticker = self.request.get('ticker')
            logging.info('Update earnings for %s' % (ticker))
            self.__update_earnings()
        
application = webapp.WSGIApplication([('/tasks/updatestockinfo', UpdateStockInfoHandler),
                                      ('/tasks/updateallmarketcapital', UpdateAllMarketCapitalHandler),
                                      ('/tasks/updatesinglemarketcapital', UpdateSingleMarketCapitalHandler),
                                      ('/tasks/updateearnings', UpdateEarningsHandler)],
                                     debug=True)


def main():
    run_wsgi_app(application)
    
    
if __name__ == '__main__':
    main()