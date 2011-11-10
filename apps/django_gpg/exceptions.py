class GPGException(Exception):
    pass

class GPGVerificationError(GPGException):
    pass

class GPGSigningError(GPGException):
    pass
