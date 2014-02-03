"""Contains Error classes
"""

class OtherError(Exception):
    pass

class NotProcessedError(Exception):
    pass

class HTTPNotFoundError(Exception):
    pass

class HTTPForbiddenError(Exception):
    pass