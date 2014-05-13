# -*- coding: utf-8 -*-


import httplib
import logging
import string
from google.appengine.api.labs import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import stock_result

class BAEHandler(webapp.RequestHandler):
    def get(self):
        entry = stock_result.get_json('magicformula')
        logging.info('fuck: '+entry.content)
        uri = ''
        with open('config/uri') as file:
            for line in file.readlines():
                if len(line) > 0:
                    uri = line.strip()
                    break
        c = httplib.HTTPConnection('bcs.duapp.com')
        c.request("PUT", uri, entry.content)
        r = c.getresponse()
        
application = webapp.WSGIApplication([('/tasks/bae', BAEHandler)], debug=True)


def main():
    run_wsgi_app(application)
    
    
if __name__ == '__main__':
    main()