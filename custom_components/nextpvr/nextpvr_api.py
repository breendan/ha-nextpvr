import aiohttp
import hashlib
import xml.etree.ElementTree as ET
import urllib.parse
from urllib.parse import urlparse

from .const import DEFAULT_PORT, DEFAULT_SSL # Use default if not provided

class NextPVRApi:
    def __init__(self, session: aiohttp.ClientSession, host: str, pin: str, port: int = DEFAULT_PORT, use_ssl: bool = DEFAULT_SSL):
        self.original_host_input = host
        self.pin = pin
        self.port = port
        self.session = session
        self.sid = None  # Session ID

        scheme, hostname = self._derive_scheme_and_hostname(host, use_ssl)
        self.scheme = scheme
        self.host = hostname
        self.base_url = f"{scheme}://{hostname}:{port}/service"

    @staticmethod
    def _derive_scheme_and_hostname(host: str, use_ssl: bool):
        """ determine if host has been provided with prefix or not """
        if "://" in host:
            parsed = urlparse(host)
            scheme = parsed.scheme or ("https" if use_ssl else "http")
            hostname = parsed.hostname or host
        else:
            scheme = "https" if use_ssl else "http"
            hostname = host
        return scheme, hostname

    async def _call_method(self, params: dict, use_get=False, retry=True):
        """
        Internal helper to send a GET or POST request to the NextPVR service.
        Automatically retries login once if SID is invalid.
        """
        # Ensure logged in for calls needing sid
        if "sid" in params and (params["sid"] is None):
            await self.login()
            params["sid"] = self.sid

        try:
            if use_get:
                async with self.session.get(self.base_url, params=params) as resp:
                    resp.raise_for_status()
                    text = await resp.text()
            else:
                encoded_data = urllib.parse.urlencode(params)
                async with self.session.post(self.base_url, data=encoded_data) as resp:
                    resp.raise_for_status()
                    text = await resp.text()

            root = ET.fromstring(text)

            # Check for session error
            if root.tag == "rsp" and root.attrib.get("stat") == "fail":
                err = root.find("err")
                if err is not None and "not logged in" in err.attrib.get("msg", "").lower():
                    if retry:
                        # Session likely expired, re-login and retry once
                        await self.login()
                        params["sid"] = self.sid
                        return await self._call_method(params, use_get=use_get, retry=False)
                    else:
                        raise RuntimeError("SID expired and retry already attempted")

            return root

        except Exception as e:
            raise RuntimeError(f"API call failed: {e}")

    async def login(self):
        """
        Initiates a session and logs in using the hashed PIN authentication.
        Stores the session ID (`sid`) for subsequent calls.
        """
        # Step 1: Start session
        root = await self._call_method({"method": "session.initiate", "ver": "1.0", "device": "python-client"}, use_get=True)

        sid = root.findtext("sid")
        salt = root.findtext("salt")

        # Step 2: Create MD5 hash of PIN
        pin_md5 = hashlib.md5(self.pin.encode()).hexdigest().lower()
        combined = f":{pin_md5}:{salt}"
        md5 = hashlib.md5(combined.encode()).hexdigest()

        # Step 3: Log in with session ID and hashed credentials
        await self._call_method({"method": "session.login", "sid": sid, "md5": md5}, use_get=True)

        self.sid = sid

    async def ensure_logged_in(self):
        """Call login only if not already logged in."""
        if self.sid is None:
            await self.login()

    async def get_devices(self):
        """
        Fetches the status of all NextPVR devices (tuners).
        Returns a list of device dictionaries.
        """
        await self.ensure_logged_in()
        root = await self._call_method({"method": "system.status", "sid": self.sid}, use_get=True)

        devices_info = []
        for dev in root.findall(".//Device"):
            oid = dev.get("oid")
            identifier = dev.get("identifier")

            # Collect device activity status (e.g., LiveTV, Recording)
            states = {}
            for child in dev:
                states[child.tag] = child.text

            if not states:
                status = "IDLE"
                path = None
            else:
                # Pick first child as main status
                status = next(iter(states))
                path = states[status]

            devices_info.append({
                "oid": oid,
                "identifier": identifier,
                "status": status,
                "path": path
            })

        return devices_info

    async def devices_in_use(self):
        """
        Checks which tuners are currently in use.
        Returns a dict mapping device oid to True if in use.
        """
        await self.ensure_logged_in()
        root = await self._call_method({"method": "system.status", "sid": self.sid}, use_get=True)

        in_use_devices = {}
        for dev in root.findall(".//Device"):
            oid = dev.get("oid")
            # If any active state, mark device as in use
            if dev.find("LiveTV") is not None or dev.find("Recording") is not None:
                in_use_devices[oid] = True

        return in_use_devices
