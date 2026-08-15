import unittest

from tools.structure_filter_model import score_breakout


class BreakoutScoreTests(unittest.TestCase):
    def test_scores_clean_breakout_without_follow_bonus(self):
        score = score_breakout(
            body_ratio=0.75,
            required_body_ratio=0.60,
            opposite_shadow_ratio=0.10,
            max_opposite_shadow=0.20,
            breakout_distance_atr=0.20,
            min_breakout_distance_atr=0.10,
            dangerous_candle=False,
            follow_through_required=False,
            has_follow_through=False,
        )

        self.assertEqual(score, 80.0)

    def test_dangerous_candle_penalty_reduces_score(self):
        score = score_breakout(
            body_ratio=0.75,
            required_body_ratio=0.60,
            opposite_shadow_ratio=0.10,
            max_opposite_shadow=0.20,
            breakout_distance_atr=0.20,
            min_breakout_distance_atr=0.10,
            dangerous_candle=True,
            follow_through_required=False,
            has_follow_through=False,
        )

        self.assertEqual(score, 50.0)

    def test_follow_through_can_lift_clean_breakout_to_full_score(self):
        score = score_breakout(
            body_ratio=0.75,
            required_body_ratio=0.60,
            opposite_shadow_ratio=0.10,
            max_opposite_shadow=0.20,
            breakout_distance_atr=0.20,
            min_breakout_distance_atr=0.10,
            dangerous_candle=False,
            follow_through_required=True,
            has_follow_through=True,
        )

        self.assertEqual(score, 100.0)

    def test_validates_descending_resistance_breakout_for_buy(self):
        from tools.structure_filter_model import Bar, find_valid_trendline

        bars = [
            Bar(open=104, high=107, low=101, close=103),
            Bar(open=106, high=110, low=102, close=105),
            Bar(open=103, high=106, low=100, close=102),
            Bar(open=102, high=105, low=99, close=101),
            Bar(open=104, high=108, low=101, close=103),
            Bar(open=101, high=104, low=98, close=100),
            Bar(open=100, high=103, low=97, close=99),
            Bar(open=102, high=106, low=99, close=101),
            Bar(open=100, high=102, low=97, close=99),
            Bar(open=104, high=107, low=101, close=106),
        ]

        trendline = find_valid_trendline(
            bars=bars,
            direction="buy",
            atr=5.0,
            swing_lookback=1,
            min_touches=3,
            touch_atr=0.25,
            min_breakout_distance_atr=0.10,
        )

        self.assertTrue(trendline.valid)
        self.assertEqual(trendline.touches, 3)
        self.assertGreaterEqual(trendline.breakout_distance_atr, 0.10)

    def test_rejects_buy_when_no_valid_structure_exists(self):
        from tools.structure_filter_model import Bar, find_valid_trendline

        bars = [
            Bar(open=100, high=102, low=99, close=101),
            Bar(open=101, high=103, low=100, close=102),
            Bar(open=102, high=104, low=101, close=103),
            Bar(open=103, high=105, low=102, close=104),
            Bar(open=104, high=106, low=103, close=105),
        ]

        trendline = find_valid_trendline(
            bars=bars,
            direction="buy",
            atr=5.0,
            swing_lookback=1,
            min_touches=3,
            touch_atr=0.25,
            min_breakout_distance_atr=0.10,
        )

        self.assertFalse(trendline.valid)


if __name__ == "__main__":
    unittest.main()
