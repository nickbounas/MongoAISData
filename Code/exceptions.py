class ApplicationException(Exception):
    def __init__(self, status_code=400, message="Application Error"):
        self.status_code = status_code
        self.message = message
