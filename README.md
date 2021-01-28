# Plugin Cart Api Exchange for Circulation Manager

With this plugin the CM can create and update carts in the DPLA Exchanche platform. To perform this is necessary a Feedbook acount (http://market.feedbooks.com/).

# Plugin changes

* No routes are added
* Frequently send to cart API all items that are expiring, expired or with long queues. (Must enable it in admin interface!).

# Upload to a PyPI server

To upload a package twine is used.
`pip install twine`

1. Build the package
`python setup.py sdist bdist_wheel`

2. Upload to a PyPI server
`twine upload --repository-url <pypi_server_name> dist/*`

Note: To use a local pypi server, please follow [this tutorial](https://github.com/arielmorelli/dev_env_for_circulation/tree/main/plugins)

# Installing the plugin

Please use `pip install -U --index-url <pypi_server_name> cm-plugin-cart-api-exchange`

# Running tests

Once the plugin needs the server_core packages to run, it's necessary to have it under the core folder.
To to this, clone the server_core:
`git clone https://github.com/arielmorelli/server_core core`

To run tests, just run `nosetests tests/` (don't forget to activate the virtualenv activated and install all requirements packages)

