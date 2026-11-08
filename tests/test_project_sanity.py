"""Offline sanity checks; these tests do not contact 12306 or place orders."""
import unittest

import TickerConfig
from config.urlConf import urls


class ProjectSanityTests(unittest.TestCase):
    def test_runtime_configuration_has_expected_types(self):
        self.assertIsInstance(TickerConfig.STATION_DATES, list)
        self.assertIsInstance(TickerConfig.STATION_TRAINS, list)
        self.assertIsInstance(TickerConfig.TICKET_PEOPLES, list)
        self.assertIsInstance(TickerConfig.EMAIL_CONF, dict)
        self.assertIsInstance(TickerConfig.SERVER_CHAN_CONF, dict)

    def test_endpoint_definitions_are_well_formed(self):
        self.assertTrue(urls)
        for name, config in urls.items():
            with self.subTest(endpoint=name):
                self.assertIn("req_url", config)
                self.assertTrue(config["req_url"].startswith("/"))
                self.assertIn(config.get("req_type", "get"), ("get", "post"))
                self.assertIsInstance(config.get("re_try", 0), int)
                self.assertGreaterEqual(config.get("re_try", 0), 0)

    def test_credentials_are_not_committed_as_defaults(self):
        self.assertEqual(TickerConfig.USER, "")
        self.assertEqual(TickerConfig.PWD, "")
        self.assertEqual(TickerConfig.EMAIL_CONF.get("password", ""), "")
        self.assertEqual(TickerConfig.SERVER_CHAN_CONF.get("secret", ""), "")


if __name__ == "__main__":
    unittest.main()
