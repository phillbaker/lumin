# !/usr/bin/env python
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

Note that there were some naming problems with this file. Naming it googlevoice.py 
created a naming conflict with the pygooglevoice googlevoice module.

"""
#from __future__ import absolute_import
from datetime import datetime
import os, time, re, sys, ConfigParser

import django.utils.simplejson as json
from rapidsms.backends.base import BackendBase
from rapidsms.utils.modules import try_import
from googlevoice import Voice
#googlevoice = try_import('googlevoice')
#Voice = try_import('googlevoice.Voice')

class GoogleVoiceBackend(BackendBase):
    _title = "googlevoice" #or pyGoogleVoice?
    
    # number of seconds to wait between
    # polling the modem for incoming SMS
    POLL_INTERVAL = 10
    
    # time to wait for the start method to
    # complete before assuming that it failed
    MAX_CONNECT_TIME = 10
    
    def configure(self, **kwargs):
        #if Voice is None:
        #    raise ImportError(
        #        "The lumin.backends.googlevoice engine is not available, " +
        #        "because 'pygooglevoice' is not installed or not on the current path."
        #    )
        
        self.config = ConfigParser.ConfigParser()
        import lumin
        self.config.read(os.path.join(os.path.dirname(lumin.__file__), '.gvoice'))#TODO make sure that this is reading from the project root directory, not the same directory as where this file is placed
        #make sure we have at least the required parameters
        if self.config == [] or (not self.config.has_option('login', 'email') or not self.config.has_option('login', 'password')):
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
    
    def run(self):
        while self.running:
            self.info("Polling google voice for messages")
            
            messages = self.voice.inbox().messages #poll it, this will return conversations, not individual messages
            
            #google voice works like gmail: 
            #it automatically groups individual texts into conversations by 
            #phone number and similar timestamps (texts relatively close 
            #in time will be grouped together)
            status = json.loads(self.voice.inbox.json)
            html = self.voice.inbox.html
            
            if status['unreadCounts']['sms'] >= 1 : #check for new conversations
                for key in status['messages'].keys() :
                    phone_number = status['messages'][key]['phoneNumber']
                    #TODO figure out this datetime stuff
                    #datetime = datetime.fromtimestamp(int(status['messages'][key]['startTime'])/1000) #google gives three decimal places of precision, take it off
                    #date = #this date time will have some problems, 
                    #the json gives us a unix time stamp but that's updated every time we add something to the conversation; 
                    #the parsed datetime from the html can be shorthand/etc.
                    
                    #TODO (critical) another problem here is that everytime we get a reply, the entire conversation is returned
                    #so we replay the entire conversation everytime we get a text to add onto it, we either need to retrieve
                    # individual messages from google voice, or somehow separate these conversations up into atomic blocks
                    texts = re.findall(
                        re.escape(phone_number) + r'\:\s*\<\/span\>\s*\<span\s+class="gc\-message\-sms\-text"\>(.*?)\<\/span\>', 
                        html, 
                        re.S
                    )
                    
                    for text in texts :
                        identity = ''.join(re.findall(r'[0-9]+', phone_number))
                        message = self.message(identity, text) #, datetime)
                        self.router.incoming_message(message)
                
                for message in messages :
                    message.mark()
            
            #todo may be easier way to do this? just search for received messages that have not been read? flags for that?
            #in:unread to:me
            
            # wait for POLL_INTERVAL seconds before continuing
            # (in a slightly bizarre way, to ensure that we abort
            # as soon as possible when the backend is asked to stop)
            for n in range(0, self.POLL_INTERVAL*10):
                if not self.running: return None
                time.sleep(0.1)
            
        self.info("Run loop terminated.")
    
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
    
