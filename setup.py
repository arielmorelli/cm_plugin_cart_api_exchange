from setuptools import setup

PLUGIN_NAME="cm_plugin_cart_api_exchange"

setup(
    name=PLUGIN_NAME,
    packages=[PLUGIN_NAME],
    version="0.0.2",
    description="Enable automatic cart creation in DPLA Exchange account",
    url="https://github.com/arielmorelli/cm_plugin_cart_api_exchange",
    python_requres='<=2.7',
    install_requires=[],
)
