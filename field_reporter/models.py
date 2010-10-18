from django.db import models

class FieldTest(models.Model):
    #stuff from test
    #since the test generates a color, numbers don't exactly correlate. Model this as:
    # * rgb/hex values
    # * scale 0-100 (whatever upper bound we'd like)
    # * choice of letters that represent basic colors
    # just use range 0-100 for now, with two decimal places
    result = models.DecimalField(decimal_places=5,max_digits=2)
    
    #TODO consolidate this in a separate model
    # * grab from phone number
    reporter = models.PositiveIntegerField(null=False, default=0) 
    reporter_name = models.CharField(null=False, max_length=64)
    
    #TODO consolidate this in a separate model
    # * grab from cell location? (probably not given...)
    location = models.PositiveIntegerField(null=False, default=0)
    location_name = models.CharField(null=False, max_length=64)
    
    test_date = models.DateTimeField(null=True) #don't make it an auto field since we might be reporting a past test?
    
    #meta data
    created = models.DateTimeField(null=False, auto_now_add=True)
    updated = models.DateTimeField(null=False, auto_now=True)
