# vim: ai sts=4 sw=4 ts=4 et
import rapidsms
import re
from models import FieldTest
from datetime import datetime

class App(rapidsms.app.App):

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
    
    pattern = re.compile(r'^report\s+(name|location|result)\s+(.*)', re.IGNORECASE)

    def start (self):
        """Configure your app in the start phase."""
        pass
    
    def parse (self, message):
        """Parse and annotate messages in the parse phase."""
        pass
    
    def handle (self, message):
        response = self.pattern.findall(message.text)
        if response:
            entry = response[0]
            entry_time = datetime.now()
            origin = message.connection.identity
            datum = entry[1]

            if entry[0].lower() == 'result':
                handle_result(message, entry_time, origin, datum)
            elif entry[0].lower() == 'location':
                handle_location(message, origin, datum)
            elif entry[0].lower() == "name":
                 message.respond("Not implemented yet.")
            
            return True
        else:
            return False
    

    def cleanup (self, message):
        """Perform any clean up after all handlers have run in the
           cleanup phase."""
        pass
    
    def outgoing (self, message):
        """Handle outgoing message notifications."""
        pass
    
    def stop (self):
        """Perform global app cleanup when the application is stopped."""
        pass
    
    def handle_result(message, entry_time, origin, datum):
        # Persist entry in the database
        FieldTest(
            location_name = datum,
            test_date = entry_time,
            origin = origin
        ).save()

        # Generate a response
        message.respond("Your test result has been saved, please send: test STOP mileage_reading")
    
    def handle_location(message, origin, datum):
         try:
            # TODO Do a lookup of locations?
            #
            # We attempt to find the latest "open" entry with the same origin. 
            # An "open" entry is one that has been created using "report result"
            # but has not been "closed" with a "report location"
            reading = Mileage.objects.filter(completed=False,origin=origin).order_by('-test_date')[0]
            if reading:
                reading.location = datum
                reading.completed = True
                reading.save()

                # Generate response to send back
                response = "You've finished a report indicating a test result of %d at %s on %s, logged by %s." % (reading.result, reading.location, reading.test_date.strip(), reading.origin)
                #TODO implement a correction facility, ie "is this correct?"
                message.respond(response)
         except(FieldTest.DoesNotExist, IndexError):
             message.respond("You can't complete a report you didn't start!")
    