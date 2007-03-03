#!/usr/bin/env python2.5
# -*- python -*-
from __future__ import generators
import web
import Core
import Store
import RenderUtils
import Config
import base64
import pickle
import User
import hmac
import urllib
import os

urls = (
    '/([^/]*)', 'read',
    '/([^/]*)/edit', 'edit',
    '/([^/]*)/save', 'save',
    '/([^/]*)/delete', 'delete',
    '/([^/]*)/mediacache/(.*)', 'mediacache',
    '/_/static/([^/]+)', 'static',
    '/_/settings', 'settings',
    '/_/logout', 'logout',
    )

def mac(str):
    return hmac.new(Config.session_passphrase, str).hexdigest()

def newSession():
    return web.storage({
        'username': None,
        })

class LoginPage(Core.Renderable):
    def __init__(self, action, login_failed):
        self.action = action
        self.login_failed = login_failed

    def templateName(self):
        return 'action_loginpage'

class Action(Core.Renderable):
    def __init__(self):
        self.loadCookies_()
        self.recoverSession_()
        self.input = web.input(**self.defaultInputs())
        self.ctx = web.ctx
        self.ctx.store = Store.FileStore(Config.filestore_dir)
        self.ctx.cache = Store.FileStore(Config.cache_dir)

    def defaultInputs(self):
        return {
            'format': 'html'
            }

    def loadCookies_(self):
        self.cookies = web.cookies(pyle_session = '')

    def recoverSession_(self):
        self.session = None
        try:
            if self.cookies.pyle_session:
                (cookiehash, sessionpickle64) = self.cookies.pyle_session.split('::', 1)
                sessionpickle = base64.decodestring(sessionpickle64)
                computedhash = mac(sessionpickle)
                if computedhash == cookiehash:
                    self.session = pickle.loads(sessionpickle)
        except:
            pass
        if not self.session:
            self.session = newSession()
        self._user = None

    def user(self):
        if not self._user:
            self._user = User.lookup(self.session.username)
        return self._user

    def ensure_login(self):
        if not self.user().is_anonymous():
            return True

        self._user = None

        login_failed = 0
        if self.input.has_key('Pyle_username'):
            username = self.input.Pyle_username
            password = self.input.Pyle_password
            user = User.lookup(username)
            if Config.user_authenticator.authenticate(user, password):
                self.session.username = username
                self._user = user
                return True
            login_failed = 1

        web.output(LoginPage(self, login_failed).render('html'))
        return False

    def ensure_login_if_required(self):
        if self.login_required():
            return self.ensure_login()
        else:
            return True

    def login_required(self):
        return False

    def render(self, format):
        self.saveSession_()
        self.ctx.store.commit()
        return Core.Renderable.render(self, format)

    def saveSession_(self):
        sessionpickle = pickle.dumps(self.session)
        computedhash = mac(sessionpickle)
        web.setcookie('pyle_session',
                      computedhash + '::' + base64.encodestring(sessionpickle).strip())

    def GET(self, *args):
        if self.ensure_login_if_required():
            self.handle_request(*args)

    def POST(self, *args):
        return self.GET(*args)

    def handle_request(self, *args):
        if self.input.format == 'html':
            web.header('Content-Type','text/html; charset=utf-8', unique=True)
        web.output(self.render(self.input.format))

class PageAction(Action):
    def init_page(self, pagename):
        if not pagename:
            pagename = Config.frontpage
        self.pagename = pagename
        self.page = Core.Page(self.ctx.store, self.ctx.cache, pagename)

    def login_required(self):
        return not Config.allow_anonymous_view

    def handle_request(self, pagename):
        self.init_page(pagename)
        Action.handle_request(self)

class read(PageAction):
    def templateName(self):
        return 'action_read'

class mediacache(PageAction):
    def handle_request(self, pagename, cachepath):
        self.init_page(pagename)
        (mimetype, bytes) = self.page.mediacache[cachepath]
        web.header('Content-Type', mimetype)
        web.output(bytes)

class edit(PageAction):
    def login_required(self):
        return not Config.allow_anonymous_edit

    def templateName(self):
        return 'action_edit'

class save(PageAction):
    def login_required(self):
        return not Config.allow_anonymous_edit

    def handle_request(self, pagename):
        self.init_page(pagename)
        self.page.setText(self.input.body)
        self.page.save(self.user())
        web.seeother(RenderUtils.InternalLink(self.page.title).url())

class static:
    def GET(self, filename):
        if filename in ['.', '..', '']:
            web.ctx.status = '403 Forbidden'
        else:
            f = open(os.path.join('static', filename), 'rb')
            web.output(f.read())
            f.close()

class logout(Action):
    def handle_request(self):
        self.session.username = None
        self._user = None
        Action.handle_request(self)

    def templateName(self):
        return 'action_logout'

class settings(Action):
    def login_required(self):
        return True

    def handle_request(self):
        self.changes_saved = False
        if self.input.has_key('action'):
            if self.input.action == 'save_settings':
                i = web.input(email = self.user().email,
                              unsubscribe = [])
                self.user().email = i.email
                self.user().subscriptions = [s for s in self.user().subscriptions
                                             if s not in i.unsubscribe]
                self.user().save_properties()
                self.changes_saved = True
        Action.handle_request(self)

    def templateName(self):
        return 'action_settings'

if __name__ == '__main__': web.run(urls, globals())
