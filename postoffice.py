# -*- coding: utf-8 -*-


import logging
import string
import sys
import urllib
from google.appengine.api.labs import taskqueue
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template


class Client(db.Model):
    email = db.StringProperty(indexed=False)
    
    
class ClientHandler(webapp.RequestHandler):
    def get(self):
        query = db.Query(Client)
        clients = query.fetch(10000)
        value = {}
        value['clients'] = clients
        content = template.render('client.html', value)
        self.response.write(content)
        
    def post(self):
        behavior = self.request.get("behavior")
        if "add" == behavior:
            email = self.request.get("clientemail").strip().lower()
            client = Client.get_or_insert(email)
            client.email = email
            client.put()
        if "remove" == behavior:
            email = self.request.get("clientemail")
            Client.get_by_key_name(email).delete()
        self.redirect("/client")


class PostMan(db.Model):
    name = db.StringProperty(indexed=False)
    
    
class PostManHandler(webapp.RequestHandler):
    def get(self):
        query = db.Query(PostMan)
        postmen = query.fetch(1000)
        value = {}
        value['postmen'] = postmen
        content = template.render('postman.html', value)
        self.response.write(content)
        
        
    def post(self):
        behavior = self.request.get("behavior")
        if "add" == behavior:
            name = self.request.get("postmanname").strip().lower()
            postman = PostMan.get_or_insert(name)
            postman.name = name
            postman.put()
        if "remove" == behavior:
            name = self.request.get("postmanname")
            PostMan.get_by_key_name(name).delete()
        self.redirect("/postman")
    
class MailHandler(webapp.RequestHandler):
    def post(self):
        client = self.request.get("client")
        postman = self.request.get("postman")
        formula = self.request.get("formula")
        subject = self.request.get("subject")
        url = 'http://' + postman + '.appspot.com/tasks/postoffice'
        code = sys.getdefaultencoding()
        if code != 'utf8':
            reload(sys)
            sys.setdefaultencoding('utf8')
        form_fields = {"client": client, "formula": formula, "subject": subject}
        form_data = urllib.urlencode(form_fields)
        result = urlfetch.fetch(url=url,
                                payload=form_data,
                                method=urlfetch.POST,
                                headers={'Content-Type': 'application/x-www-form-urlencoded'})
        
class PostOfficeHandler(webapp.RequestHandler):
    def get(self):
        post('magicformula', '神奇公式')
        post('grahamformula', '格雷厄姆公式')
        post('netcurrentassetapproach', '净流动资产法')

def post(formula, subject):
    postmen = []
    clients = []
    query = db.Query(PostMan)
    men = query.fetch(1000)
    for man in men:
        postmen.append(man.name)
    query = db.Query(Client)
    men = query.fetch(10000)
    for man in men:
        clients.append(man.email)
    i = 0
    for client in clients:
        postman = postmen[i % len(postmen)]
        logging.info(client + " by " + postman)
        taskqueue.add(url='/tasks/mail',
                      method="POST",
                      params={'postman' : postman, 'client' : client, 'formula': formula, 'subject': subject})
        i = i + 1


application = webapp.WSGIApplication([('/tasks/mail', MailHandler),
                                      ('/tasks/postoffice', PostOfficeHandler),
                                      ('/postman', PostManHandler),
                                      ('/client', ClientHandler)], 
                                     debug=True)


def main():
    run_wsgi_app(application)
    
    
if __name__ == '__main__':
    main()