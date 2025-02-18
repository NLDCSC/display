class DisplayError(Exception):
    pass


class DisplayClientMissing(DisplayError):
    pass


class DisplayClientTypeError(DisplayError):
    pass


class DisplayLockAlreadyExistsError(DisplayError):
    pass
