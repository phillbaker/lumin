# vim: ai sts=4 sw=4 ts=4 et

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from ..models import FieldTest
from datetime import datetime
from decimal import *
import re

class ReportHandler(KeywordHandler):
    """
    Handle any message prefixed ``report''.
    """
    keyword = 'report'
    
    # This prototype app will process two (self-explanatory) data points: 
    #   location_name, 
    #   result
    # The message pattern expected one of:
    #   report location [location]
    #   report result []
    # should order matter? store the result and then associate it with other stuff?
    # what if we hand out/make available a pdf strip with a color spectrum with decimal numbers along the axis? that would be fairly precise/disposable
    
    # This prototype app will process three (self-explanatory) data points: 
    #   reporter_name, 
    #   location_name, 
    #   result
    # The message pattern expected one of:
    #   report name [name]
    #   report location [location]
    #   report result []
    
    def handle(self, text):
        pattern = re.compile(r'^\s*(name|location|result)\s+(.*)', re.IGNORECASE)
        response = pattern.findall(text)
        if response:
            if self.msg.connection.identity is not None:
                origin = self.msg.connection.identity
            else:
                origin = 'UNKNOWN'
            
            entry = response[0]
            entry_time = datetime.now()
            datum = entry[1]
            
            if entry[0].lower() == 'result':
                self.handle_result(entry_time, origin, datum)
            elif entry[0].lower() == 'location':
                self.handle_location(origin, datum)
            else:
                self.respond('Not implemented yet.')
            
            return True
        else:
            self.help
    
    def help(self):
        self.respond("To report a result, send: REPORT RESULT [result]")
    
    def handle_result(self, entry_time, origin, datum):
        # Persist entry in the database
        FieldTest(
            result = datum.strip(),
            test_date = entry_time,
            origin = origin
        ).save()
        
        # Generate a response
        self.respond("Your test result has been saved, please send: REPORT LOCATION [location]")
    
    def handle_location(self, origin, datum):
         try:
            # TODO Do a lookup of locations?
            #
            # We attempt to find the latest "open" entry with the same origin. 
            # An "open" entry is one that has been created using "report result"
            # but has not been "closed" with a "report location"
            reading = FieldTest.objects.filter(completed=False,origin=origin).order_by('-test_date')[0]
            if reading:
                reading.location_name = datum.strip()
                reading.completed = True
                reading.save()
                
                # Generate response to send back
                response = "You've finished a report indicating a test result of %s at %s on %s, logged by %s." % ("%001.2f" % reading.result, reading.location_name, reading.test_date.strftime('%b %d, %Y %H:%M'), reading.origin)
                #TODO implement a correction facility, ie "is this correct?"
                self.respond(response)
         except(FieldTest.DoesNotExist, IndexError):
             self.respond("You can't complete a report you didn't start!")
    
