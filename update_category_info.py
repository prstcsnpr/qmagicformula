#coding=utf8


import logging
import string
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import stock


class UpdateCategoryInfoHandler(webapp.RequestHandler):

    def get(self):
        with open('category') as file:
            for line in file.readlines():
                fields = line.split()
                entry = stock.get(fields[0])
                entry.categories.append(fields[1])
                stock.put(fields[0], entry)
        
        
application = webapp.WSGIApplication([('/tasks/updatecategoryinfo', UpdateCategoryInfoHandler)],
                                     debug=True)


def main():
    run_wsgi_app(application)
    
    
if __name__ == '__main__':
    main()