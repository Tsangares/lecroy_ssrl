import unittest
from driver import *

class Test_LecroySSRL(unittest.TestCase):
    def testConfig(self):
        print(LecroySSRL.getConfig())


if __name__=='__main__':
    unittest.main()
