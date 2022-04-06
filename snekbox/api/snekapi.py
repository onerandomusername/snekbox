import falcon

from .resources import About, EvalResource


class SnekAPI(falcon.API):
    """
    The main entry point to the snekbox JSON API.

    Routes:
    - /
        Snekbox Metadata

    - /eval
        Evaluation of Python code

    Error response format:

    >>> {
    ...     "title": "Unsupported media type",
    ...     "description": "application/xml is an unsupported media type."
    ... }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_route("/", About())
        self.add_route("/eval", EvalResource())
