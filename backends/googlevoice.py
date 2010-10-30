#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

"""
This backend leverages the pygooglevoice egg, which must be installed. It also 
uses the built-in python ConfigParser to read login e-mail and password 
information from a .gvoice file in the project directory. This file should 
be created of the following form.

<<<
[login]
email = me@example.com
password = password

<<<

"""

import time
import ConfigParser

from rapidsms.backends.base import BackendBase
from rapidsms.utils.modules import try_import
googlevoice = try_import('googlevoice')
Voice = None

class GoogleVoiceBackend(BackendBase):
    _title = "googlevoice" #or pyGoogleVoice?
    
    # number of seconds to wait between
    # polling the modem for incoming SMS
    POLL_INTERVAL = 10
    
    # time to wait for the start method to
    # complete before assuming that it failed
    MAX_CONNECT_TIME = 10
    
    def configure(self, **kwargs):
        if googlevoice is None:
            raise ImportError(
                "The lumin.backends.googlevoice engine is not available, " +
                "because 'pygooglevoice' is not installed."
            )
        
        from googlevoice import Voice
        
        self.config = ConfigParser.ConfigParser()
        self.config.read('.gvoice')#TODO make sure that this is reading from the project root directory, not the same directory as where this file is placed
        #make sure we have at least the required parameters
        if len(self.config) == 0 || (!config.has_option('login', 'email') or !config.has_option('login', 'password'))
            raise ImportError( #TODO is importerror really what we want to use?
                "The lumin.backends.googlevoice engine is not available, " +
                "because a .gvoice configuration file in the root of the project " +
                "with login and password attributes does not exist."
            )
    
    def __str__(self):
        return self._title
    
    def send(self, message):
        try: #TODO this is based on the assumption that the googlevoice method will throw exceptions (it returns None)
            self.voice.send_sms(
                str(message.connection.identity), 
                message.text
            ) 
        except:
            self.info(sys.exc_info()) #log the exception
            self.failed_messages += 1
            return False
            
        self.sent_messages += 1
        return True
    
    def status(self):
        vars = {
            "_title":   self.title,
            "Messages Sent": self.sent_messages,
            "Messages Received": self.received_messages 
        }
        
        #TODO see if we can pull data from googlevoice object
        
        return vars
    
    #TODO
    #def run(self):
    #    while self.running:
    #        self.info("Polling modem for messages")
    #        msg = self.modem.next_message()
            
    #        if msg is not None:
    #            self.received_messages += 1
                
                # we got an sms! hand it off to the
                # router to be dispatched to the apps
    #            x = self.message(msg.sender, msg.text)
    #            self.router.incoming_message(x)
            
            # wait for POLL_INTERVAL seconds before continuing
            # (in a slightly bizarre way, to ensure that we abort
            # as soon as possible when the backend is asked to stop)
    #        for n in range(0, self.POLL_INTERVAL*10):
    #            if not self.running: return None
    #            time.sleep(0.1)
            
    #    self.info("Run loop terminated.")
    
    def start(self):
        try:
            self.sent_messages = 0
            self.failed_messages = 0
            self.received_messages = 0
            
            self.info("Connecting via googlevoice...")
            self.voice = Voice()
            
            result = self.voice.login(email=self.config.get('login','email'), passwd=self.config.get('login','password'))
            #if result is None:
            #    raise #TODO find the exception this should raise
            
            # call the superclass to start the run loop -- it just sets
            # ._running to True and calls run, but let's not duplicate it.
            BackendBase.start(self)
            
        except:
            if getattr(self, "voice", None):
                self.voice.logout()
            
            raise
    
    def stop(self):
        # call superclass to stop--sets self._running
        # to False so that the 'run' loop will exit cleanly.
        BackendBase.stop(self)
        
        # logout from googlevoice
        if self.voice is not None:
            self.voice.logout()
    
