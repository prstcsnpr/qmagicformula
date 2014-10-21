# -*- coding: utf-8 -*-


import datetime
import logging
from google.appengine.api.labs import taskqueue
from google.appengine.api import mail
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api.urlfetch_errors import DownloadError
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app


class ShowStockIndexHandler(webapp.RequestHandler):
    
    def get(self):
        try:
            taskqueue.add(url='/tasks/magicformula',
                          queue_name='formula',
                          method='GET')
            taskqueue.add(url='/tasks/grahamformula',
                          queue_name='formula',
                          method='GET')
            taskqueue.add(url='/tasks/netcurrentassetapproach',
                          queue_name='formula',
                          method='GET')
        except Exception as e:
            logging.exception(e)
            taskqueue.add(url='/tasks/showstockindex',
                          queue_name='showstockindex',
                          method='GET')
    
    
application = webapp.WSGIApplication([('/tasks/showstockindex', ShowStockIndexHandler)],
                                     debug=True)


def main():
    run_wsgi_app(application)
    
    
if __name__ == '__main__':
    main()