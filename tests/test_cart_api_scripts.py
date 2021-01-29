from core.testing import DatabaseTest, create
from core.model.plugin_configuration import PluginConfiguration
from core.model.library import Library
from core.model.work import Work
from core.model.identifier import Identifier
from core.model.datasource import DataSource
from core.model.licensing import LicensePool
from core.model.collection import Collection, collections_libraries
from core.model.configuration import ExternalIntegration
from core.model import get_one_or_create

from mock import MagicMock, ANY

from cm_plugin_cart_api_exchange.cart_api_scripts import (
    CartApiScript,
    KEY_EXPIRED_FROM_DPLA,
    KEY_EXPIRED_FROM_ANY,
    KEY_EXPIRING_FROM_DPLA,
    KEY_EXPIRING_FROM_ANY,
    KEY_LONG_QUEUE_FROM_DPLA,
    KEY_LONG_QUEUE_FROM_ANY,
    TRUE_VALUE,
    FALSE_VALUE,
    DPLA,
)
from cm_plugin_cart_api_exchange.cart_api_operations import ExchangeApi


class TestCartApiScripts(DatabaseTest):
    def create_library_and_collection(self):
        self.plugin_name = "a-plugin"
        self.cart_script = CartApiScript(_db=self._db)
        self.exchange_api = ExchangeApi("user", "password")
        self.exchange_api.send_items = MagicMock()

        self.datasource, _ = get_one_or_create(self._db,
            DataSource, name="DPLA Exchange"
        )

        self.identifier, _ = get_one_or_create(self._db,
            Identifier, type="ISBN", identifier="1231231231231"
        )
        ext_integ, _ = create(
            self._db, ExternalIntegration, protocol="test", goal="licenses", name="TextInteg"
        )

        self.library, _ = create(
            self._db, Library, name="a-library", short_name="a-l"
        )

        self.collection, _ = create(
            self._db, Collection, name="a-collection", external_integration_id=ext_integ.id
        )

        ins = collections_libraries.insert().values(
            collection_id=self.collection.id, library_id=self.library.id
        )
        self._db.execute(ins)

    def test_run_with_config(self):
        cart_script = CartApiScript(_db=self._db)
        try:
            cart_script.run("a-plugin")
        except Exception as err:
            raise Exception("run raised %s unexpectedly!", err)

    def test_run_call_all_carts(self):
        plugin_name = "a-plugin"
        cart_script = CartApiScript(_db=self._db)
        cart_script._run_expired_items = MagicMock()
        cart_script._run_expiring_items = MagicMock()
        cart_script._run_long_queue_items = MagicMock()

        lib_id = 12
        # Create library
        library, ignore = create(
            self._db, Library, id=lib_id, name="a-library", short_name="a-l"
        )

        # Create plugin config entry
        create(
            self._db, PluginConfiguration, library_id=library.id,
            key=plugin_name+"."+KEY_EXPIRED_FROM_DPLA, _value=TRUE_VALUE
        )
        create(
            self._db, PluginConfiguration, library_id=library.id,
            key=plugin_name+"."+KEY_EXPIRED_FROM_ANY, _value=TRUE_VALUE
        )
        create(
            self._db, PluginConfiguration, library_id=library.id,
            key=plugin_name+"."+KEY_EXPIRING_FROM_DPLA, _value=TRUE_VALUE
        )
        create(
            self._db, PluginConfiguration, library_id=library.id,
            key=plugin_name+"."+KEY_EXPIRING_FROM_ANY, _value=TRUE_VALUE
        )
        create(
            self._db, PluginConfiguration, library_id=library.id,
            key=plugin_name+"."+KEY_LONG_QUEUE_FROM_DPLA, _value=TRUE_VALUE
        )
        create(
            self._db, PluginConfiguration, library_id=library.id,
            key=plugin_name+"."+KEY_LONG_QUEUE_FROM_ANY, _value=TRUE_VALUE
        )

        cart_script.run(plugin_name)

        # called twice, one for DPLA and one for ANY
        assert cart_script._run_expired_items.call_count == 2
        assert cart_script._run_expiring_items.call_count == 2
        assert cart_script._run_long_queue_items.call_count == 2

    def test_run_expired_items_with_cart_url(self):
        self.create_library_and_collection()
        internal_value = {KEY_EXPIRED_FROM_DPLA: "dpla-url", KEY_EXPIRED_FROM_ANY: "any-url"}

        # Create one work
        work, _ = create(
            self._db, Work,
        )
        # Create a open access license
        self.exchange_api.send_items.reset_mock()
        create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=True, licenses_available=0
        )
        self.cart_script._run_expired_items(self.exchange_api, internal_value, self.library, None)
        self.exchange_api.send_items.assert_not_called()

        # Create non expired license
        self.exchange_api.send_items.reset_mock()
        create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=False, licenses_available=10,
        )

        self.cart_script._run_expired_items(self.exchange_api, internal_value, self.library, None)
        self.exchange_api.send_items.assert_not_called()

        # Create with expired license
        self.exchange_api.send_items.reset_mock()
        license, _ = create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=False, licenses_available=0,
        )
        self.cart_script._run_expired_items(self.exchange_api, internal_value, self.library, None)
        called_url, called_items, _ = self.exchange_api.send_items.call_args[0]
        assert called_url == internal_value[KEY_EXPIRED_FROM_ANY]
        assert len(called_items) == 1
        assert license.identifier_id in called_items
        assert "copies" in called_items[license.identifier_id]
        assert "identifier" in called_items[license.identifier_id]

        # Create with expired license without being DPLA but filtering by DPLA
        self.exchange_api.send_items.reset_mock()
        create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=False, licenses_available=0,
        )
        self.cart_script._run_expired_items(self.exchange_api, internal_value, self.library, DPLA)
        self.exchange_api.send_items.assert_not_called()

        # Create with expired license being DPLA and filtering by DPLA
        self.exchange_api.send_items.reset_mock()
        create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=False, licenses_available=0,
            data_source_id=self.datasource.id
        )
        self.cart_script._run_expired_items(self.exchange_api, internal_value, self.library, DPLA)
        called_url, called_items, _ = self.exchange_api.send_items.call_args[0]
        assert called_url == internal_value[KEY_EXPIRED_FROM_DPLA]
        assert len(called_items) == 1

    def test_run_expiring_items_with_cart_url(self):
        self.create_library_and_collection()
        internal_value = {KEY_EXPIRING_FROM_DPLA: "dpla-url", KEY_EXPIRING_FROM_ANY: "any-url"}

        # Create one work
        work, _ = create(
            self._db, Work,
        )
        # Create a open access license
        self.exchange_api.send_items.reset_mock()
        create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=True, licenses_available=5
        )
        self.cart_script._run_expiring_items(self.exchange_api, internal_value, self.library, None)
        self.exchange_api.send_items.assert_not_called()

        # Create non expired licenses
        self.exchange_api.send_items.reset_mock()
        create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=False, licenses_available=0,
        )

        self.cart_script._run_expiring_items(self.exchange_api, internal_value, self.library, None)
        self.exchange_api.send_items.assert_not_called()

        # Create non expiring licenses
        self.exchange_api.send_items.reset_mock()
        create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=False, licenses_available=100,
        )

        self.cart_script._run_expiring_items(self.exchange_api, internal_value, self.library, None)
        self.exchange_api.send_items.assert_not_called()

        # Create with expiring license
        self.exchange_api.send_items.reset_mock()
        license, _ = create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=False, licenses_available=2,
        )
        self.cart_script._run_expiring_items(self.exchange_api, internal_value, self.library, None)
        called_url, called_items, _ = self.exchange_api.send_items.call_args[0]
        assert called_url == internal_value[KEY_EXPIRING_FROM_ANY]
        assert len(called_items) == 1
        assert license.identifier_id in called_items
        assert "copies" in called_items[license.identifier_id]
        assert "identifier" in called_items[license.identifier_id]

        # Create with expiring license without being DPLA but filtering by DPLA
        self.exchange_api.send_items.reset_mock()
        create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=False, licenses_available=2,
        )
        self.cart_script._run_expiring_items(self.exchange_api, internal_value, self.library, DPLA)
        self.exchange_api.send_items.assert_not_called()

        # Create with expiring license being DPLA and filtering by DPLA
        self.exchange_api.send_items.reset_mock()
        create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=False, licenses_available=2,
            data_source_id=self.datasource.id
        )
        self.cart_script._run_expiring_items(self.exchange_api, internal_value, self.library, DPLA)
        called_url, called_items, _ = self.exchange_api.send_items.call_args[0]
        assert called_url == internal_value[KEY_EXPIRING_FROM_DPLA]
        assert len(called_items) == 1

    def test_run_long_queue_items_with_cart_url(self):
        self.create_library_and_collection()
        internal_value = {KEY_LONG_QUEUE_FROM_DPLA: "dpla-url", KEY_LONG_QUEUE_FROM_ANY: "any-url"}

        # Create one work
        work, _ = create(
            self._db, Work,
        )
        # Create a open access license
        self.exchange_api.send_items.reset_mock()
        create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=True, patrons_in_hold_queue=10
        )
        self.cart_script._run_long_queue_items(self.exchange_api, internal_value, self.library, None)
        self.exchange_api.send_items.assert_not_called()

        # Create license without queue
        self.exchange_api.send_items.reset_mock()
        create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=False, patrons_in_hold_queue=0
        )

        self.cart_script._run_long_queue_items(self.exchange_api, internal_value, self.library, None)
        self.exchange_api.send_items.assert_not_called()

        # Create with long queue
        self.exchange_api.send_items.reset_mock()
        license, _ = create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=False, patrons_in_hold_queue=100,
        )
        self.cart_script._run_long_queue_items(self.exchange_api, internal_value, self.library, None)
        called_url, called_items, _ = self.exchange_api.send_items.call_args[0]
        assert called_url == internal_value[KEY_LONG_QUEUE_FROM_ANY]
        assert len(called_items) == 1
        assert license.identifier_id in called_items
        assert "copies" in called_items[license.identifier_id]
        assert "identifier" in called_items[license.identifier_id]

        # Create with long queue license without being DPLA but filtering by DPLA
        self.exchange_api.send_items.reset_mock()
        create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=False, patrons_in_hold_queue=100,
        )
        self.cart_script._run_long_queue_items(self.exchange_api, internal_value, self.library, DPLA)
        self.exchange_api.send_items.assert_not_called()

        # Create with long queue license being DPLA and filtering by DPLA
        self.exchange_api.send_items.reset_mock()
        create(
            self._db, LicensePool, work_id=work.id, collection_id=self.collection.id,
            identifier_id=self.identifier.id, open_access=False, patrons_in_hold_queue=100,
            data_source_id=self.datasource.id
        )
        self.cart_script._run_long_queue_items(self.exchange_api, internal_value, self.library, DPLA)
        called_url, called_items, _ = self.exchange_api.send_items.call_args[0]
        assert called_url == internal_value[KEY_LONG_QUEUE_FROM_DPLA]
        assert len(called_items) == 1

