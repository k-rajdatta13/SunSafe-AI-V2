class SunSafeError(Exception):
    """Base application error with a stable public error code."""
    code = "SUNSAFE_ERROR"


class ExternalServiceError(SunSafeError):
    code = "EXTERNAL_SERVICE_ERROR"


class CityNotFoundError(SunSafeError):
    code = "CITY_NOT_FOUND"
