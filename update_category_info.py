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


class UpdateCategoryInfoHandler(webapp.RequestHandler):

    def get(self):
        taskqueue.add(url='/tasks/updateallcategoryinfo',
                      queue_name='updateallcategoryinfo',
                      method='GET')
        

class UpdateAllCategoryInfoHandler(webapp.RequestHandler):
    
    def get(self):
        url = 'http://stockapp.finance.qq.com/mstats/menu_childs.php?id=bd_csrc'
        result = urlfetch.fetch(url=url)
        if 200 == result.status_code:
            data = result.content.decode('GBK').encode('UTF-8')
            data = json.loads(data)
            for i in data['bd_csrc']['chd']:
                taskqueue.add(url='/tasks/updatesinglecategoryinfo',
                              queue_name='updatesinglecategoryinfo',
                              method='GET',
                              params={'category' : i})
                
                
class UpdateSingleCategoryInfoHandler(webapp.RequestHandler):
    
    def get(self):
        category = self.request.get('category')
        url = 'http://stock.gtimg.cn/data/get_hs_xls.php?id=pt' + category[2:] + '&type=1&metric=name'
        result = urlfetch.fetch(url=url)
        if 200 == result.status_code:
            data = result.content
            print data
        
        
application = webapp.WSGIApplication([('/tasks/updatecategoryinfo', UpdateCategoryInfoHandler),
                                      ('/tasks/updateallcategoryinfo', UpdateAllCategoryInfoHandler),
                                      ('/tasks/updatesinglecategoryinfo', UpdateSingleCategoryInfoHandler)],
                                     debug=True)


def main():
    run_wsgi_app(application)
    
    
if __name__ == '__main__':
    main()