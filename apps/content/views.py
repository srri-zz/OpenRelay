import sendfile

from core.runtime import content_cache


def serve_resource(request):
    resource_id = request.GET.get('id', None)
    resource_descriptor = content_cache.retrieve(resource_id) 
    
    return sendfile.sendfile(request, resource_descriptor)
