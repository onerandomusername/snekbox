import json
import logging
import os
import shlex
import subprocess
import sys

import falcon
from falcon.media.validators.jsonschema import validate

from snekbox.nsjail import NsJail

logger = logging.getLogger(__name__)

USERBASE = "/snekbox/user_base"


class PackageListResource:
    """
    Represents a package list.

    Supported methods:
    - GET
        Returns a list of all installed packages.
    - POST
        Installs the provided packages
    """

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        """Get a list of all packages and their versions."""
        command = f"{sys.executable} -m pip list --format=json --user"
        env = os.environ.copy()
        env["PYTHONUSERBASE"] = USERBASE
        result = subprocess.run(command.split(), text=True, capture_output=True, env=env)
        print(result.stdout)
        print(result.stderr)
        if result.returncode != 0:
            resp.status = falcon.HTTP_500
            return

        resp.media = {"packages": json.loads(result.stdout)}
        resp.content_type = falcon.MEDIA_JSON

    POST_REQ_SCHEMA = {
        "type": "object",
        "properties": {
            "packages": {
                "type": "array",
                "items": {
                    "type": "string",
                },
            },
            "upgrade": {
                "type": "boolean",
            },
            "force_reinstall": {
                "type": "boolean",
            },
        },
        "required": ["packages"],
    }

    @validate(POST_REQ_SCHEMA)
    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        """Install the provided packages to snekbox."""
        packages = shlex.join(req.media["packages"])
        logger.debug(f"Installing packages: {packages}")
        cmd = f"PYTHONUSERBASE={USERBASE} {sys.executable} -m pip install "
        if req.media.get("upgrade"):
            cmd += "-upgrade "
        if req.media.get("force_reinstall"):
            cmd += "--force-reinstall "

        # todo: switch to subprocess and collect the stdout
        code = os.system(cmd + packages)

        if code == 0:
            resp.status = falcon.HTTP_204
        else:
            resp.status = falcon.status.HTTP_500


GET_INFO_CODE = """
import importlib.metadata
import json
metadata = importlib.metadata.metadata("{package}")
print(json.dumps(metadata.json))
"""


class SinglePackageResource:
    """
    Represents a single package.

    Supported methods:
    - GET
        Returns the package's metadata
    - DELETE
        Uninstalls the package
    """

    def __init__(self, nsjail: NsJail):
        self.nsjail = nsjail

    def on_get(self, req: falcon.Request, resp: falcon.Response, name: str) -> None:
        """Get the specified package, if it exists and is installed."""
        code = GET_INFO_CODE.format(package=name)
        valid_keys = {"version", "home_page", "name", "summary", "license"}
        result = self.nsjail.python3(code)
        if result.returncode != 0:
            if result.returncode == 255:
                resp.status = falcon.HTTP_500
            else:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "No package found."}
            return

        data = json.loads(result.stdout)
        data = {k: v for k, v in data.items() if k in valid_keys}
        resp.media = data
        resp.content_type = falcon.MEDIA_JSON

    def on_delete(self, req: falcon.Request, resp: falcon.Response, name: str) -> None:
        """Deletes the provided package."""
        logger.debug(f"Uninstalling package: {name}")
        cmd = f"PYTHONUSERBASE={USERBASE} {sys.executable} -m pip uninstall -y {name}"

        code = os.system(cmd)

        if code == 0:
            resp.status = falcon.HTTP_204
        else:
            resp.status = falcon.status.HTTP_404
            resp.media = {"error": "No package found."}
