from core.model.plugin import Plugin
from core.model.library import Library
from core.model.identifier import Identifier
from core.model.licensing import LicensePool
from core.model.datasource import DataSource
from core.model.collection import Collection, collections_libraries
from core.scripts import Script
from cart_api_operations import ExchangeApi


KEY_USER = "user"
KEY_PASSWORD = "password"
KEY_EXPIRED_FROM_DPLA = "expired-from-dpla"
KEY_EXPIRED_FROM_ANY = "expired-from-any"
KEY_EXPIRING_FROM_DPLA = "expiring-from-dpla"
KEY_EXPIRING_FROM_ANY = "expiring-from-any"
KEY_LONG_QUEUE_FROM_DPLA= "long-queue-from-dpla"
KEY_LONG_QUEUE_FROM_ANY = "long-queue-from-any"
TRUE_VALUE = "true"
FALSE_VALUE = "false"
DPLA = "DPLA"

INTERNAL = "_internal."

class CartApiScript(Script):
    def __init__(self, _db=None):
        super(CartApiScript, self).__init__(_db=_db)

    def run(self, plugin_name):
        plugin_model = Plugin()
        internal_plugin_name = INTERNAL+plugin_name

        libraries = self._db.query(Library).all()

        for library in libraries:
            values = Plugin().get_saved_values(
                self._db, library.short_name, plugin_name
            )
            
            user = None
            user_config = values.get(KEY_USER)
            if user_config:
                user = user_config._value

            pwd = None
            pwd_config = values.get(KEY_PASSWORD)
            if pwd_config:
                pwd = pwd_config._value
            exchange_api = ExchangeApi(user, pwd)

            internal_values = plugin_model.get_saved_values(
                self._db, library.short_name, internal_plugin_name
            )

            if values.get(KEY_EXPIRED_FROM_DPLA) and \
                values[KEY_EXPIRED_FROM_DPLA]._value == TRUE_VALUE:
                    self._run_expired_items(
                        exchange_api, internal_values, library, vendor=DPLA
                    )
                    plugin_model.save_values(
                        self._db, library.short_name, internal_plugin_name, internal_values
                    )
            if values.get(KEY_EXPIRED_FROM_ANY) and \
                values[KEY_EXPIRED_FROM_ANY]._value == TRUE_VALUE:
                    self._run_expired_items(
                        exchange_api, internal_values, library
                    )
                    plugin_model.save_values(
                        self._db, library.short_name, internal_plugin_name, internal_values
                    )
            if values.get(KEY_EXPIRING_FROM_DPLA) and \
                values[KEY_EXPIRING_FROM_DPLA]._value == TRUE_VALUE:
                    self._run_expiring_items(
                        exchange_api, internal_values, library, vendor=DPLA
                    )
                    plugin_model.save_values(
                        self._db, library.short_name, internal_plugin_name, internal_values
                    )
            if values.get(KEY_EXPIRING_FROM_ANY) and \
                values[KEY_EXPIRING_FROM_ANY]._value == TRUE_VALUE:
                    self._run_expiring_items(
                        exchange_api, internal_values, library
                    )
                    plugin_model.save_values(
                        self._db, library.short_name, internal_plugin_name, internal_values
                    )
            if values.get(KEY_LONG_QUEUE_FROM_DPLA) and \
                values[KEY_LONG_QUEUE_FROM_DPLA]._value == TRUE_VALUE:
                    self._run_long_queue_items(
                        exchange_api, internal_values, library, vendor=DPLA
                    )
                    plugin_model.save_values(
                        self._db, library.short_name, internal_plugin_name, internal_values
                    )
            if values.get(KEY_LONG_QUEUE_FROM_ANY) and \
                values[KEY_LONG_QUEUE_FROM_ANY]._value == TRUE_VALUE:
                    self._run_long_queue_items(
                        exchange_api, internal_values, library
                    )
                    plugin_model.save_values(
                        self._db, library.short_name, internal_plugin_name, internal_values
                    )

    def _run_expired_items(self, exchange_api, internal_values, library, vendor=None):
        if vendor == DPLA:
            cart_key = KEY_EXPIRED_FROM_DPLA
        elif not vendor:
            cart_key = KEY_EXPIRED_FROM_ANY
        else:
            raise NotImplementedError

        cart_name = library.name + " " + cart_key
        cart_url = internal_values.get(cart_key)
        if not cart_url:
            cart_url = exchange_api.create_cart(cart_name)
            internal_values[cart_key] = cart_url
            try:
                self._db.commit()
            except Exception as ex:
                self._db.rollback()

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
            LicensePool.licenses_available == 0,
        ).filter(
            LicensePool.collection_id.in_([t[0].id for t in target_collections])
        )
        
        if vendor == DPLA:
            dpla_datasource = self._db.query(
                DataSource
            ).filter(
                DataSource.name != None
            ).filter(
                DataSource.name == "DPLA Exchange"
            ).first()

            licenses_query = licenses_query.filter(
                LicensePool.data_source_id == dpla_datasource.id
            )
        
        licenses = licenses_query.all()
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

        if items:
            exchange_api.send_items(cart_url, items, cart_name)


    def _run_expiring_items(self, exchange_api, internal_values, library, vendor=None):
        if vendor == DPLA:
            cart_key = KEY_EXPIRING_FROM_DPLA
        elif not vendor:
            cart_key = KEY_EXPIRING_FROM_ANY
        else:
            raise NotImplementedError

        cart_name = library.name + " " + cart_key
        cart_url = internal_values.get(cart_key)
        if not cart_url:
            cart_url = exchange_api.create_cart(cart_name)
            internal_values[cart_key] = cart_url
            try:
                self._db.commit()
            except Exception as ex:
                self._db.rollback()

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
            LicensePool.licenses_available > 0,
        ).filter(
            LicensePool.licenses_available <= 5,
        ).filter(
            LicensePool.collection_id.in_([t[0].id for t in target_collections])
        )

        if vendor == DPLA:
            dpla_datasource = self._db.query(
                DataSource
            ).filter(
                DataSource.name == "DPLA Exchange"
            ).first()

            licenses_query = licenses_query.filter(
                LicensePool.data_source_id == dpla_datasource.id
            )
        
        licenses = licenses_query.all()
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

        if items:
            exchange_api.send_items(cart_url, items, cart_name)


    def _run_long_queue_items(self, exchange_api, internal_values, library, vendor=None):
        if vendor == DPLA:
            cart_key = KEY_LONG_QUEUE_FROM_DPLA
        elif not vendor:
            cart_key = KEY_LONG_QUEUE_FROM_ANY
        else:
            raise NotImplementedError

        cart_name = library.name + " " + cart_key
        cart_url = internal_values.get(cart_key)
        if not cart_url:
            cart_url = exchange_api.create_cart(cart_name)
            internal_values[cart_key] = cart_url
            try:
                self._db.commit()
            except Exception as ex:
                self._db.rollback()

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
            LicensePool.patrons_in_hold_queue > 5,
        ).filter(
            LicensePool.collection_id.in_([t[0].id for t in target_collections])
        )

        if vendor == DPLA:
            dpla_datasource = self._db.query(
                DataSource
            ).filter(
                DataSource.name == "DPLA Exchange"
            ).first()

            licenses_query = licenses_query.filter(
                LicensePool.data_source_id == dpla_datasource.id
            )
        
        licenses = licenses_query.all()
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

        if items:
            exchange_api.send_items(cart_url, items, cart_name)

