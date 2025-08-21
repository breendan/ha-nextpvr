"""Constants for the nextpvr component"""

DOMAIN = "nextpvr"

# Configuration keys
CONF_HOST = "host"
CONF_PIN = "pin"
CONF_PORT = "port"
CONF_SSL = "ssl"                # New: Use HTTPS
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_PORT = 8866
DEFAULT_SSL = False             # Default to HTTP
DEFAULT_SCAN_INTERVAL = 120  # seconds (2 minutes)
