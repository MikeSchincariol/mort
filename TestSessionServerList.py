import unittest
import datetime

from SessionServerInfo import SessionServerInfo as ssi
from SessionServerList import SessionServerList as sslist

class TestSessionServerList(unittest.TestCase):
    """
    These test cases check the functionality added to the list base class,
    by the SessionServerList class.
    """

    def setUp(self):
        # Create some dummy SessionServerInfo objects that can be used
        # for testing
        self.ssi0 = ssi("a.b.c", "192.168.7.220", 42124, datetime.datetime.now())
        self.ssi1 = ssi("m.n.o", "192.168.7.100", 51662, datetime.datetime.now())
        self.ssi2 = ssi("x.y.z", "192.168.5.40", 47756, datetime.datetime.now())

    def test_constructor_with_no_iterable(self):
        """
        Create an instance without passing in an iterable and confirm
        it gets created without any items in it
        """
        inst = sslist()
        self.assertListEqual(inst, [])

    def test_constructor_with_valid_iterable(self):
        """
        Create an instance with and pass some initial values in via the
        constructors iterable argument. Check that the list is sorted
        correctly.
        """
        inst = sslist((self.ssi2, self.ssi1, self.ssi0))
        self.assertListEqual(inst, [self.ssi0, self.ssi1, self.ssi2])


    def test_constructor_with_invalid_iterable(self):
        """
        Create an instance with and pass some initial values in via the
        constructors iterable argument with are of an invalid type. Check that
        the list raises the assertion exception correctly.
        """
        self.assertRaises(AssertionError,
                          sslist,
                          (0, 1, 2))

    def test_append(self):
        inst = sslist()

        # Append an item
        inst.append(self.ssi1)
        self.assertListEqual(inst, [self.ssi1])

        # Append another item that should sort ahead of the first item
        inst.append(self.ssi0)
        self.assertListEqual(inst, [self.ssi0, self.ssi1])

        # Append another item that should sort behind the first item
        inst.append(self.ssi2)
        self.assertListEqual(inst, [self.ssi0, self.ssi1,self.ssi2])


    def test_extend(self):
        inst = sslist()

        # Append a single item
        inst.append(self.ssi1)
        self.assertListEqual(inst, [self.ssi1])

        # Extend the list with 2 items, one that sorts behind and,
        # the other that sorts ahead of, the first item added to
        # the list.
        inst.extend([self.ssi2, self.ssi0])
        self.assertListEqual(inst, [self.ssi0, self.ssi1, self.ssi2])

    def test_insert_not_implemented(self):
        inst = sslist()

        # Try and insert an item and check it throws a NotImplementedError exception
        self.assertRaises(NotImplementedError,
                          sslist().insert,
                          0, self.ssi0)

    def test_reverse_not_implemented(self):
        inst = sslist()

        # Try and insert an item and check it throws a NotImplementedError exception
        self.assertRaises(NotImplementedError,
                          sslist().reverse)


    def test_sort_not_implemented(self):
        inst = sslist()

        # Try and insert an item and check it throws a NotImplementedError exception
        self.assertRaises(NotImplementedError,
                          sslist().sort)

