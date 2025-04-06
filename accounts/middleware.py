class EnsureSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.session.session_key:
            request.session.save()  # Ensure session key is created
        return self.get_response(request)



