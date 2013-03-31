# -*- coding: utf-8 -*-


from google.appengine.ext import db


class Stock(db.Model):
    title = db.StringProperty
    market_capital = db.StringProperty
    market_capital_date = db.IntegerProperty
    bank_flag = db.BooleanProperty
    
        