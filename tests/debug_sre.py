import sys
sys.path.append('d:/DubaiMatrixASI')
from tests.verify_soros_reflexivity import TestSorosReflexivityEngine

t = TestSorosReflexivityEngine()
t.setUp()
try:
    t.test_soros_squeeze_bull_inversion()
except AssertionError as e:
    decision = t.trinity.last_decision
    print(f"SRE VETO REASON: {decision.reasoning}")

try:
    t.test_entropic_vacuum_harvester()
except AssertionError as e:
    decision = t.trinity.last_decision
    print(f"EVH VETO REASON: {decision.reasoning}")
