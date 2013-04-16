#coding=utf8


import logging
import string
from google.appengine.api.labs import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import stock


class UpdateCategoryInfoHandler(webapp.RequestHandler):

    def get(self):
        taskqueue.add(url='/tasks/updateallcategoryinfo',
                      queue_name='updatecategoryinfo',
                      method='GET')
        
        
class UpdateAllCategoryInfoHandler(webapp.RequestHandler):
    
    def get(self):
        with open('category') as file:
            for line in file.readlines():
                fields = line.split()
                taskqueue.add(url='/tasks/updatesinglecategoryinfo',
                              queue_name='updatecategoryinfo',
                              method='GET',
                              params={'ticker' : fields[0],
                                      'category' : fields[1]})
                
                
class UpdateSingleCategoryInfoHandler(webapp.RequestHandler):
    
    def get(self):
        ticker = self.request.get('ticker')
        category = self.request.get('category')
        entry = stock.get(ticker)
        entry.category = category
        stock.put(ticker, entry)
        
        
application = webapp.WSGIApplication([('/tasks/updatecategoryinfo', UpdateCategoryInfoHandler),
                                      ('/tasks/updateallcategoryinfo', UpdateAllCategoryInfoHandler),
                                      ('/tasks/updatesinglecategoryinfo', UpdateSingleCategoryInfoHandler)],
                                     debug=True)


def main():
    run_wsgi_app(application)
    
    
if __name__ == '__main__':
    main()