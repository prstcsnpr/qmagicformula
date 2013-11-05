# -*- coding: utf-8 -*-


import logging
import string
import urllib
from google.appengine.api.labs import taskqueue
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app


class MailHandler(webapp.RequestHandler):
    def post(self):
        client = self.request.get("client")
        postman = self.request.get("postman")
        formula = self.request.get("formula")
        url = 'http://' + postman + '.appspot.com/tasks/postoffice'
        form_fields = {"client": client, "formula": formula}
        form_data = urllib.urlencode(form_fields)
        result = urlfetch.fetch(url=url,
                                payload=form_data,
                                method=urlfetch.POST,
                                headers={'Content-Type': 'application/x-www-form-urlencoded'})
        
class PostOfficeHandler(webapp.RequestHandler):
    def get(self):
        post('magicformula')
        post('grahamformula')

def post(formula):
    postmen = []
    with open('postmen') as file:
        for line in file.readlines():
            postman = line.split()[0]
            postmen.append(postman)
    i = 0;
    with open('clients') as file:
        for line in file.readlines():
            client = line.split()[0]
            postman = postmen[i % len(postmen)];
            taskqueue.add(url='/tasks/mail',
                          method="POST",
                          params={'postman' : postman, 'client' : client, 'formula': formula})
            i = i + 1
            


application = webapp.WSGIApplication([('/tasks/mail', MailHandler),
                                      ('/tasks/postoffice', PostOfficeHandler)], 
                                     debug=True)


def main():
    run_wsgi_app(application)
    
    
if __name__ == '__main__':
    main()