import falcon

from snekbox import GIT_SHA


class About:
    """
    About snekbox.

    Supported methods:

    - GET /
        Returns information about snekbox
    """

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        """Return some metadata about snekbox."""
        resp.media = {
            "sha": GIT_SHA,
        }
