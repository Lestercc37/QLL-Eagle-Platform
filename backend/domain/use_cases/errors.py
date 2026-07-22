class QllError(Exception):
    code = "INTERNAL_ERROR"


class NotFoundError(QllError):
    code = "NOT_FOUND"
