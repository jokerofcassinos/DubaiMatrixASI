import asyncio
import unittest
import time
from market.data_engine import DataEngine

class TestFractalIngestion(unittest.TestCase):
    """
    [Ω-GAUNTLET] Fractal Sensory Integrity (1m -> 1H).
    """

    def test_resampling_integrity(self):
        """[V001-V004] Validates OHLC aggregation."""
        engine = DataEngine("BTCUSD")
        
        # 1. Simulate 305 ticks (5 minutes and 5 seconds total)
        # Using 1-second intervals for test speed
        start_ts = 1711800000.0 # Arbitrary timestamp
        
        # We need to fill at least 300 seconds to close the first 5m candle
        for i in range(305):
            engine.update({
                "time": start_ts + i,
                "price": 65000.0 + i,
                "volume": 0.1
            })
            
        # 2. Check 5m buffer [V007-V009]
        self.assertEqual(len(engine.tf_buffers["5m"]), 1, "Should have 1 closed 5m candle.")
        
        candle = engine.tf_buffers["5m"][0]
        self.assertEqual(candle["open"], 65000.0)
        self.assertEqual(candle["high"], 65299.0)
        self.assertEqual(candle["close"], 65299.0)
        # Fix precision for volume
        self.assertAlmostEqual(candle["volume"], 30.0, places=5, msg="Total volume for 300 ticks (0.1 each).")

    def test_multitemporal_bias(self):
        """[V021-V027] Validates HTF Trend identification."""
        engine = DataEngine("BTCUSD")
        
        # Start with an uptrend (Close > Open)
        start_ts = 1711800000.0
        for i in range(301):
            engine.update({"time": start_ts + i, "price": 60000 + i, "volume": 1.0})
            
        snap = engine.get_snapshot()
        self.assertEqual(snap.metadata["5m_bias"], 1.0, "5m bias should be bullish.")

if __name__ == '__main__':
    unittest.main()
