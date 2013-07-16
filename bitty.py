#!/usr/bin/env python
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup

from kivy.support import install_twisted_reactor
install_twisted_reactor()

from twisted.internet import ssl, reactor
from twisted.internet.protocol import ClientFactory, Protocol

import json

class TenthbitClient(Protocol):
    def connectionMade(self):
        self.factory.root.on_connection(self.transport)

    def dataReceived(self, data):
        self.factory.root.handle_payload(data)

class TenthbitClientFactory(ClientFactory):
    protocol = TenthbitClient

    def __init__(self, root):
        self.root = root

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - goodbye!"
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print reason
        print "Connection lost - goodbye!"
        reactor.stop()

class ConnectDialog(FloatLayout):
    connect = ObjectProperty(None)
    cancel = ObjectProperty(None)

class Root(TabbedPanel):
    connection = None
    chat = ObjectProperty(None)
    scrollback = ObjectProperty(None)

    username = None
    password = None

    def send_payload(self, payload):
        '''Take a JSON string and send it down the wire.'''
        self.scrollback.text += '<<< ' + str(payload) + '\n'
        self.connection.write(str(payload) + "\n")

    def send_auth(self):
        auth = {
            'op': 'auth',
            'ex': {
                'username': self.username,
                'password': self.password,
            }
        }
        self.send_payload(json.dumps(auth))

    def dismiss_popup(self):
        self._popup.dismiss()

    def send_from_inputbox(self):
        self.send_payload(self.chat.text)
        self.chat.text = ''
        self.chat.focus = True
        self.chat.select_all()

    def handle_payload(self, data):
        print "*** " + data
        self.scrollback.text +=  ">>> " + data
        parsed = json.loads(data)

        # TODO: Use fn.py's Option monad.
        if parsed['op'] == 'welcome' and self.username != None and self.password != None:
            self.send_auth()

    def on_connection(self, connection):
        print "/!\ Connected successfully!"
        self.connection = connection

    def show_connect(self):
        content = ConnectDialog(connect=self.connect, cancel=self.dismiss_popup)
        self._popup = Popup(title="Connect to Network", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def connect(self, server, port, username, password):
        self.username = username
        self.password = password
        factory = TenthbitClientFactory(self)
        reactor.connectSSL(server, int(port), factory, ssl.ClientContextFactory())

class Bitty(App):
    pass

Factory.register('Root', cls=Root)
Factory.register('ConnectDialog', cls=ConnectDialog)

if __name__ == '__main__':
    Bitty().run()
