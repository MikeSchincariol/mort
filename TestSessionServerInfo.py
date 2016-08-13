import unittest
import datetime

from SessionServerInfo import SessionServerInfo as ssi

class TestSessionServerInfo(unittest.TestCase):


    def test_constructor_no_params(self):
        """
        Create an instance and check the relevant fields are "None"
        """
        inst = ssi()

        self.assertIsNone(inst.hostname)
        self.assertIsNone(inst.ip_address)
        self.assertIsNone(inst.port)
        self.assertIsNone(inst.last_seen)


    def test_constructor_valid_params(self):
        """
        Create an instance and check the relevant fields are set
        to the values passed into the constructor
        """
        inst = ssi("test_session_server",
                   "192.168.7.220",
                   42124,
                   datetime.datetime.now())

        self.assertIsInstance(inst.hostname, str)
        self.assertIsInstance(inst.ip_address, str)
        self.assertIsInstance(inst.port, int)
        self.assertIsInstance(inst.last_seen, datetime.datetime)


    def test_constructor_invalid_hostname(self):
        """
        Check the an invalid type for the hostname member causes an assertion error.
        """
        self.assertRaises(AssertionError,
                          ssi,
                          22, "192.168.7.220", 42124, datetime.datetime.now())



    def test_constructor_invalid_ip_address(self):
        """
        Check the an invalid type for the ip_address member causes an assertion error.
        """
        self.assertRaises(AssertionError,
                          ssi,
                          "test_session_server", 1921687220, 42124, datetime.datetime.now())


    def test_constructor_invalid_port(self):
        """
        Check the an invalid type for the port member causes an assertion error.
        """
        self.assertRaises(AssertionError,
                          ssi,
                          "test_session_server", "192.168.7.220", "42124", datetime.datetime.now())

    def test_constructor_invalid_last_seen(self):
        """
        Check the an invalid type for the last_seen member causes an assertion error.
        """
        self.assertRaises(AssertionError,
                          ssi,
                          "test_session_server", "192.168.7.220", 42124, "Aug 3 2016")


    def test_property_valid_hostname(self):
        """
        Create an instance and try get/set the hostname property only.
        """
        inst = ssi()

        inst.hostname = "test_session_server"

        self.assertEquals(inst.hostname, "test_session_server")
        self.assertIsNone(inst.ip_address)
        self.assertIsNone(inst.port)
        self.assertIsNone(inst.last_seen)


    def test_property_invalid_hostname(self):
        """
        Create an instance and try set the hostname property with an invalid type.
        """
        inst = ssi()

        self.assertRaises(AssertionError, inst.hostname,  22)



    def test_property_ip_address(self):
        """
        Create an instance and try get/set the ip_address property only.
        """
        inst = ssi()

        inst.ip_address = "192.168.7.220"

        self.assertIsNone(inst.hostname)
        self.assertEquals(inst.ip_address, "192.168.7.220")
        self.assertIsNone(inst.port)
        self.assertIsNone(inst.last_seen)


    def test_property_invalid_ip_address(self):
        """
        Create an instance and try get/set the ip_address property only.
        """
        inst = ssi()

        self.assertRaises(AssertionError, inst.ip_address,  1921687220)


    def test_property_port(self):
        """
        Create an instance and try get/set the port property only.
        """
        inst = ssi()

        inst.port = 42124

        self.assertIsNone(inst.hostname)
        self.assertIsNone(inst.ip_address)
        self.assertEquals(inst.port, 42124)
        self.assertIsNone(inst.last_seen)


    def test_property_invalid_port(self):
        """
        Create an instance and try get/set the port property only.
        """
        inst = ssi()

        self.assertRaises(AssertionError, inst.port, "42124")


    def test_property_last_seen(self):
        """
        Create an instance and try get/set the last_seen property only.
        """
        inst = ssi()

        expected_time = datetime.datetime.now()

        inst.last_seen = expected_time

        self.assertIsNone(inst.hostname)
        self.assertIsNone(inst.ip_address)
        self.assertIsNone(inst.port)
        self.assertEquals(inst.last_seen, expected_time)


    def test_property_invalid_last_seen(self):
        """
            Create an instance and try get/set the last_seen property only.
            """
        inst = ssi()

        self.assertRaises(AssertionError, inst.last_seen, "Aug 3 2016")

