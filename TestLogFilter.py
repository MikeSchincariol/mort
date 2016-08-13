import unittest
import logging

from LogFilter import Filter as lf

class TestLogFilter(unittest.TestCase):

    def setUp(self):
        # Create some fake log records to test the filter method with.

        self.record_ABC= logging.LogRecord("ABC",
                                      logging.DEBUG,
                                      "some/path",
                                      1,
                                      "message to log",
                                      None,
                                      None,
                                      None)

        self.record_ABC_DEF = logging.LogRecord("ABC.DEF",
                                           logging.DEBUG,
                                           "some/path",
                                           1,
                                           "message to log",
                                           None,
                                           None,
                                           None)

        self.record_ABC_DEF_GHI = logging.LogRecord("ABC.DEF.GHI",
                                               logging.DEBUG,
                                               "some/path",
                                               1,
                                               "message to log",
                                               None,
                                               None,
                                               None)

        self.record_ABC_DEF_IHG = logging.LogRecord("ABC.DEF.IHG",
                                               logging.DEBUG,
                                               "some/path",
                                               1,
                                               "message to log",
                                               None,
                                               None,
                                               None)

        self.record_AB_DEF_GHI = logging.LogRecord("AB.DEF.GHI",
                                                  logging.DEBUG,
                                                  "some/path",
                                                  1,
                                                  "message to log",
                                                  None,
                                                  None,
                                                  None)

        self.record_A_DEF_GHI = logging.LogRecord("A.DEF.GHI",
                                             logging.DEBUG,
                                             "some/path",
                                             1,
                                             "message to log",
                                             None,
                                             None,
                                             None)

        self.record_X_Y_Z = logging.LogRecord("X.Y.Z",
                                              logging.DEBUG,
                                              "some/path",
                                              1,
                                              "message to log",
                                              None,
                                              None,
                                              None)


    def test_constructor_no_params(self):
        """
        The filter should reject all log records.
        """
        inst = lf()

        self.assertEquals(inst.filter(self.record_ABC), 0)
        self.assertEquals(inst.filter(self.record_ABC_DEF), 0)
        self.assertEquals(inst.filter(self.record_ABC_DEF_GHI), 0)
        self.assertEquals(inst.filter(self.record_ABC_DEF_IHG), 0)
        self.assertEquals(inst.filter(self.record_AB_DEF_GHI), 0)
        self.assertEquals(inst.filter(self.record_A_DEF_GHI), 0)
        self.assertEquals(inst.filter(self.record_X_Y_Z), 0)


    def test_constructor_valid_params0(self):
        """
        The filter should reject all log records.
        """
        inst = lf("")
        self.assertEquals(inst.filter(self.record_ABC), 0)
        self.assertEquals(inst.filter(self.record_ABC_DEF), 0)
        self.assertEquals(inst.filter(self.record_ABC_DEF_GHI), 0)
        self.assertEquals(inst.filter(self.record_ABC_DEF_IHG), 0)
        self.assertEquals(inst.filter(self.record_AB_DEF_GHI), 0)
        self.assertEquals(inst.filter(self.record_A_DEF_GHI), 0)
        self.assertEquals(inst.filter(self.record_X_Y_Z), 0)


    def test_constructor_valid_params1(self):
        """
        The filter should reject messages from loggers, and their children,
        whose name starts with "X.Y"
        """
        inst = lf("X.Y")
        self.assertEquals(inst.filter(self.record_ABC), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_IHG), 1)
        self.assertEquals(inst.filter(self.record_AB_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_A_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_X_Y_Z), 0)


    def test_constructor_invalid_params(self):
        """
        Should raise an AssertionError
        """
        self.assertRaises(AssertionError,
                          lf,
                          5)


    def test_filtering0(self):
        """
        The filter should reject messages from loggers, and their children,
        whose name starts with "A"
        """
        inst = lf("A")
        self.assertEquals(inst.filter(self.record_ABC), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_IHG), 1)
        self.assertEquals(inst.filter(self.record_AB_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_A_DEF_GHI), 0)
        self.assertEquals(inst.filter(self.record_X_Y_Z), 1)


    def test_filtering1(self):
        """
        The filter should reject messages from loggers, and their children,
        whose name starts with "AB"
        """
        inst = lf("AB")
        self.assertEquals(inst.filter(self.record_ABC), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_IHG), 1)
        self.assertEquals(inst.filter(self.record_AB_DEF_GHI), 0)
        self.assertEquals(inst.filter(self.record_A_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_X_Y_Z), 1)


    def test_filtering2(self):
        """
        The filter should reject messages from loggers, and their children,
        whose name starts with "ABC"
        """
        inst = lf("ABC")
        self.assertEquals(inst.filter(self.record_ABC), 0)
        self.assertEquals(inst.filter(self.record_ABC_DEF), 0)
        self.assertEquals(inst.filter(self.record_ABC_DEF_GHI), 0)
        self.assertEquals(inst.filter(self.record_ABC_DEF_IHG), 0)
        self.assertEquals(inst.filter(self.record_A_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_X_Y_Z), 1)


    def test_filtering3(self):
        """
        The filter should reject messages from loggers, and their children,
        whose name starts with "ABC.D"
        """
        inst = lf("ABC.D")
        self.assertEquals(inst.filter(self.record_ABC), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_IHG), 1)
        self.assertEquals(inst.filter(self.record_A_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_X_Y_Z), 1)


    def test_filtering4(self):
        """
        The filter should reject messages from loggers, and their children,
        whose name starts with "ABC.DE"
        """
        inst = lf("ABC.DE")
        self.assertEquals(inst.filter(self.record_ABC), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_IHG), 1)
        self.assertEquals(inst.filter(self.record_A_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_X_Y_Z), 1)


    def test_filtering5(self):
        """
        The filter should reject messages from loggers, and their children,
        whose name starts with "ABC.DEF"
        """
        inst = lf("ABC.DEF")
        self.assertEquals(inst.filter(self.record_ABC), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF), 0)
        self.assertEquals(inst.filter(self.record_ABC_DEF_GHI), 0)
        self.assertEquals(inst.filter(self.record_ABC_DEF_IHG), 0)
        self.assertEquals(inst.filter(self.record_A_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_X_Y_Z), 1)


    def test_filtering6(self):
        """
        The filter should reject messages from loggers, and their children,
        whose name starts with "ABC.DEF.G"
        """
        inst = lf("ABC.DEF.G")
        self.assertEquals(inst.filter(self.record_ABC), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_IHG), 1)
        self.assertEquals(inst.filter(self.record_A_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_X_Y_Z), 1)


    def test_filtering7(self):
        """
        The filter should reject messages from loggers, and their children,
        whose name starts with "ABC.DEF.GH"
        """
        inst = lf("ABC.DEF.GH")
        self.assertEquals(inst.filter(self.record_ABC), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_IHG), 1)
        self.assertEquals(inst.filter(self.record_A_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_X_Y_Z), 1)


    def test_filtering8(self):
        """
        The filter should reject messages from loggers, and their children,
        whose name starts with "ABC.DEF.GHI"
        """
        inst = lf("ABC.DEF.GHI")
        self.assertEquals(inst.filter(self.record_ABC), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_GHI), 0)
        self.assertEquals(inst.filter(self.record_ABC_DEF_IHG), 1)
        self.assertEquals(inst.filter(self.record_A_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_X_Y_Z), 1)


    def test_filtering9(self):
        """
        The filter should reject messages from loggers, and their children,
        whose name starts with "ABC.DEF.IHG"
        """
        inst = lf("ABC.DEF.IHG")
        self.assertEquals(inst.filter(self.record_ABC), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_ABC_DEF_IHG), 0)
        self.assertEquals(inst.filter(self.record_A_DEF_GHI), 1)
        self.assertEquals(inst.filter(self.record_X_Y_Z), 1)




if __name__ == '__main__':
    unittest.main()
