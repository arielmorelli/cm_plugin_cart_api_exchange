from core.model.plugin_configuration import PluginConfiguration
from core.model.library import Library
from core.model.identifier import Identifier
from core.model.licensing import LicensePool
from core.model.datasource import DataSource
from core.model.collection import Collection, collections_libraries
from core.scripts import Script
from cart_api_operations import ExchangeApi

import logging


KEY_USER = "user"
KEY_PASSWORD = "password"
KEY_DATASOURCE = "datasource-id"
KEY_EXPIRED_FROM_DPLA = "expired-from-dpla"
KEY_EXPIRED_FROM_ANY = "expired-from-any"
KEY_EXPIRING_FROM_DPLA = "expiring-from-dpla"
KEY_EXPIRING_FROM_ANY = "expiring-from-any"
KEY_LONG_QUEUE_FROM_DPLA= "long-queue-from-dpla"
KEY_LONG_QUEUE_FROM_ANY = "long-queue-from-any"
TRUE_VALUE = "true"
FALSE_VALUE = "false"

INTERNAL = "_internal."


class GetDatasourcesScript(Script):
    def get_datasources(self):
        datasources = self._db.query(DataSource).all()
        return [{"key": datasource.id, "label": datasource.name}
                for datasource in datasources]

class CartApiScript(Script):
    def __init__(self, _db=None):
        super(CartApiScript, self).__init__(_db=_db)

    def run(self, plugin_name):
        plugin_model = PluginConfiguration()
        internal_plugin_name = INTERNAL+plugin_name

        libraries = self._db.query(Library).all()

        for library in libraries:
            values = PluginConfiguration().get_saved_values(
                self._db, library.short_name, plugin_name
            )

            user = None
            user_config = values.get(KEY_USER)
            if user_config:
                user = user_config

            pwd = None
            pwd_config = values.get(KEY_PASSWORD)
            if pwd_config:
                pwd = pwd_config
            exchange_api = ExchangeApi(user, pwd)

            internal_values = plugin_model.get_saved_values(
                self._db, library.short_name, internal_plugin_name
            )

            vendor = internal_values.get(KEY_DATASOURCE)
            if values.get(KEY_EXPIRED_FROM_DPLA) and \
                values[KEY_EXPIRED_FROM_DPLA] == TRUE_VALUE:
                    self._run_expired_items(
                        exchange_api, internal_values, library, vendor=vendor
                    )
                    plugin_model.save_values(
                        self._db, library.short_name, internal_plugin_name, internal_values
                    )
            if values.get(KEY_EXPIRED_FROM_ANY) and \
                values[KEY_EXPIRED_FROM_ANY] == TRUE_VALUE:
                    self._run_expired_items(
                        exchange_api, internal_values, library
                    )
                    plugin_model.save_values(
                        self._db, library.short_name, internal_plugin_name, internal_values
                    )
            if values.get(KEY_EXPIRING_FROM_DPLA) and \
                values[KEY_EXPIRING_FROM_DPLA] == TRUE_VALUE:
                    self._run_expiring_items(
                        exchange_api, internal_values, library, vendor=vendor
                    )
                    plugin_model.save_values(
                        self._db, library.short_name, internal_plugin_name, internal_values
                    )
            if values.get(KEY_EXPIRING_FROM_ANY) and \
                values[KEY_EXPIRING_FROM_ANY] == TRUE_VALUE:
                    self._run_expiring_items(
                        exchange_api, internal_values, library
                    )
                    plugin_model.save_values(
                        self._db, library.short_name, internal_plugin_name, internal_values
                    )
            if values.get(KEY_LONG_QUEUE_FROM_DPLA) and \
                values[KEY_LONG_QUEUE_FROM_DPLA] == TRUE_VALUE:
                    self._run_long_queue_items(
                        exchange_api, internal_values, library, vendor=vendor
                    )
                    plugin_model.save_values(
                        self._db, library.short_name, internal_plugin_name, internal_values
                    )
            if values.get(KEY_LONG_QUEUE_FROM_ANY) and \
                values[KEY_LONG_QUEUE_FROM_ANY] == TRUE_VALUE:
                    self._run_long_queue_items(
                        exchange_api, internal_values, library
                    )
                    plugin_model.save_values(
                        self._db, library.short_name, internal_plugin_name, internal_values
                    )

    def _get_or_create_cart(self, exchange_api, library_name, cart_key, internal_values):
        cart_name = library_name + " " + cart_key
        cart_url = internal_values.get(cart_key)
        if cart_url:
            cart_url = cart_url
        else:
            cart_url = exchange_api.create_cart(cart_name)
            internal_values[cart_key] = cart_url
            try:
                self._db.commit()
            except Exception as ex:
                self._db.rollback()
        return cart_name, cart_url

    def _get_licenses_query(self, library, vendor_id):
        target_collections = self._db.query(
            Collection,
            collections_libraries
        ).filter(
            Collection.id == collections_libraries.columns.collection_id
        ).filter(
            collections_libraries.columns.library_id == library.id
        ).all()

        licenses_query = self._db.query(
            LicensePool
        ).filter(
            LicensePool.open_access.is_(False)
        ).filter(
            LicensePool.collection_id.in_([t[0].id for t in target_collections])
        )

        if vendor_id:
            licenses_query = licenses_query.filter(
                LicensePool.data_source_id == vendor_id
            )

        return licenses_query
        
    def _get_items_from_licenses(self, licenses):
        items = {}
        for license in licenses:
            if license.identifier_id:
                items[license.identifier_id] = {"copies": license.licenses_available}

        identifiers = self._db.query(
            Identifier
        ).filter(
            Identifier.id.in_([l.identifier_id for l in licenses])
        ).all()

        for identifier in identifiers:
            items[identifier.id]["identifier"] = identifier.identifier
            if identifier.type != "ISBN":
                for equivalent in identifier.equivalencies:
                    equivalent.output.type != "ISBN"
                    items[identifier.id]["identifier"] = equivalent.output.identifier
        return items

    def _run_expired_items(self, exchange_api, internal_values, library, vendor=None):
        logging.info("Running expired queue. Library: %s. vendor %s", library.name, vendor)
        if vendor:
            cart_key = KEY_EXPIRED_FROM_DPLA
        elif not vendor:
            cart_key = KEY_EXPIRED_FROM_ANY
        else:
            raise NotImplementedError

        cart_name, cart_url = self._get_or_create_cart(exchange_api, library.name,
                                                       cart_key, internal_values)

        licenses_query = self._get_licenses_query(library, vendor)
        licenses_query = licenses_query.filter(
            LicensePool.licenses_available == 0,
        )
        licenses = licenses_query.all()

        items = self._get_items_from_licenses(licenses)

        if items:
            exchange_api.send_items(cart_url, items, cart_name)
        else:
            logging.warning("No items found.")

    def _run_expiring_items(self, exchange_api, internal_values, library, vendor=None):
        logging.info("Running expiring queue. Library: %s. vendor %s", library.name, vendor)
        if vendor:
            cart_key = KEY_EXPIRING_FROM_DPLA
        elif not vendor:
            cart_key = KEY_EXPIRING_FROM_ANY
        else:
            raise NotImplementedError

        cart_name, cart_url = self._get_or_create_cart(exchange_api, library.name,
                                                       cart_key, internal_values)

        licenses_query = self._get_licenses_query(library, vendor)
        licenses_query = licenses_query.filter(
            LicensePool.licenses_available > 0,
        ).filter(
            LicensePool.licenses_available <= 5,
        )
        licenses = licenses_query.all()

        items = self._get_items_from_licenses(licenses)

        if items:
            exchange_api.send_items(cart_url, items, cart_name)
        else:
            logging.warning("No items found.")

    def _run_long_queue_items(self, exchange_api, internal_values, library, vendor=None):
        logging.info("Running long queue. Library: %s. vendor %s", library.name, vendor)
        if vendor:
            cart_key = KEY_LONG_QUEUE_FROM_DPLA
        elif not vendor:
            cart_key = KEY_LONG_QUEUE_FROM_ANY
        else:
            raise NotImplementedError

        cart_name, cart_url = self._get_or_create_cart(exchange_api, library.name,
                                                       cart_key, internal_values)

        licenses_query = self._get_licenses_query(library, vendor)
        licenses_query = licenses_query.filter(
            LicensePool.patrons_in_hold_queue > 5,
        )
        licenses = licenses_query.all()

        items = self._get_items_from_licenses(licenses)

        if items:
            exchange_api.send_items(cart_url, items, cart_name)
        else:
            logging.warning("No items found.")
