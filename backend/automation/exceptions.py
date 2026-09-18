class TrackingAutomationError(Exception):
    """Base class for expected tracking failures."""


class TrackingNotFoundError(TrackingAutomationError):
    pass


class CarrierUnavailableError(TrackingAutomationError):
    pass


class AutomationTimeoutError(TrackingAutomationError):
    pass


class TrackingParsingError(TrackingAutomationError):
    pass
