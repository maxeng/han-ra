#/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import db


class Statuses(db.Model):
    status = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    @property
    def jst_date(self):
        return self.date + datetime.timedelta(hours=9)