class APINoStoreMiddleware:
    """Keep private API responses and withdrawn publications out of shared caches."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/api/v1/'):
            response['Cache-Control'] = 'no-store'
        return response
