from cart_api_scripts import (
    KEY_USER,
    KEY_PASSWORD,
    KEY_DATASOURCE,
    KEY_EXPIRED_FROM_DPLA,
    KEY_EXPIRED_FROM_ANY,
    KEY_EXPIRING_FROM_DPLA,
    KEY_EXPIRING_FROM_ANY,
    KEY_LONG_QUEUE_FROM_DPLA,
    KEY_LONG_QUEUE_FROM_ANY,
    TRUE_VALUE,
    FALSE_VALUE,
)
from cart_api_scripts import CartApiScript, GetDatasourcesScript


datasources = GetDatasourcesScript().get_datasources()

class CartApiPlugin(object):
    """ Cart API Plugin entry point.

    This class represent a plugin and all atributes necessary to run Cart API
    from the Circulation Manager (CM) plugin extension.

    Attributes:
        FREQUENCY (int, optional): integer represing minimum hours to execute.
        SCRIPTS (list): List of scripts to run in the backend of CM.
        FIELDS (list): List of fields to add in the admin interface of CM.
    """

    FREQUENCY = 24*5 # 5 days min of frequency
    SCRIPTS = [CartApiScript]
    FIELDS = [
        {
            "key": KEY_USER,
            "label": "Username",
            "description": "DPLA Exchange user account.",
            "type": "input",
            "required": True,
        },
        {
            "key": KEY_PASSWORD,
            "label": "Password",
            "description": "DPLA Exchange account password.",
            "type": "input",
            "required": True,
        },
        {
            "key": KEY_DATASOURCE,
            "label": "Datasources",
            "description": "Select DPLA datasource.",
            "options": datasources,
            "type": "select",
            "required": True,
        },
        {
            "key": KEY_EXPIRED_FROM_DPLA,
            "label": "Expired items from the DPLA Exchange",
            "description": "Enable cart with expired items from DPLA Exchange.",
            "options": [
                {"key": TRUE_VALUE, "label": "Enable"},
                {"key": FALSE_VALUE, "label": "Disable"},
            ],
            "type": "select",
            "default": FALSE_VALUE,
            "required": False,
        },
        {
            "key": KEY_EXPIRED_FROM_ANY,
            "label": "Expired items from any vendor",
            "description": "Enable cart with expired items from any vendor.",
            "options": [
                {"key": TRUE_VALUE, "label": "Enable"},
                {"key": FALSE_VALUE, "label": "Disable"},
            ],
            "type": "select",
            "default": FALSE_VALUE,
            "required": False,
        },
        {
            "key": KEY_EXPIRING_FROM_DPLA,
            "label": "Expiring items from the DPLA Exchange",
            "description": "Enable cart with expiring items from DPLA Exchange.",
            "options": [
                {"key": TRUE_VALUE, "label": "Enable"},
                {"key": FALSE_VALUE, "label": "Disable"},
            ],
            "type": "select",
            "default": FALSE_VALUE,
            "required": False,
        },
        {
            "key": KEY_EXPIRING_FROM_ANY,
            "label": "Expiring items from the any vendor",
            "description": "Enable cart with expiring items from any vendor.",
            "options": [
                {"key": TRUE_VALUE, "label": "Enable"},
                {"key": FALSE_VALUE, "label": "Disable"},
            ],
            "type": "select",
            "default": FALSE_VALUE,
            "required": False,
        },
        {
            "key": KEY_LONG_QUEUE_FROM_DPLA,
            "label": "Items with long queue from DPLA Exchange",
            "description": "Enable cart with long queue items from DPLA Exchange.",
            "options": [
                {"key": TRUE_VALUE, "label": "Enable"},
                {"key": FALSE_VALUE, "label": "Disable"},
            ],
            "type": "select",
            "default": FALSE_VALUE,
            "required": False,
        },
        {
            "key": KEY_LONG_QUEUE_FROM_ANY,
            "label": "Items with long queue from any vendor",
            "description": "Enable cart with long queue items from any vendor.",
            "options": [
                {"key": TRUE_VALUE, "label": "Enable"},
                {"key": FALSE_VALUE, "label": "Disable"},
            ],
            "type": "select",
            "default": FALSE_VALUE,
            "required": False,
        },
        
    ]

    def activate(self, app):
        """ No routes is add with this plugin. """
        pass

    def run_scripts(self, plugin_name):
        for script in self.SCRIPTS:
            script().run(plugin_name)

