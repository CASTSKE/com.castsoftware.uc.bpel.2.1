import os
import unittest
from cast.analysers.test import UATestAnalysis


class BpelTest(unittest.TestCase):
    def test_RegisterPlugin(self):
        print (os.getcwd())
        #print("Hello Test")
        analysis = UATestAnalysis('BPEL')
        #analysis.add_selection("AmericanAirline")
        #analysis.add_selection("IVRTnStatus")
        analysis.add_selection("MasterprovideChangeModule")
        #analysis.add_selection("MasterprovideChangeModule")
        analysis.set_verbose()
        analysis.run()
if __name__ == "__main__":
    unittest.main()
