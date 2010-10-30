from django.template import RequestContext
from django.shortcuts import render_to_response

#@require_GET
def home(req):
    return render_to_response(
        "home.html",
        context_instance=RequestContext(req))
