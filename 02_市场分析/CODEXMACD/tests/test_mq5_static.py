from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EA = ROOT / "SniperTrendEA_v8.6.mq5"


class Mq5StaticTests(unittest.TestCase):
    def read_ea(self) -> str:
        self.assertTrue(EA.exists(), "SniperTrendEA_v8.6.mq5 must exist")
        return EA.read_text(encoding="utf-8")

    def test_v86_file_has_version_and_comment(self):
        source = self.read_ea()
        self.assertIn('#property version   "8.60"', source)
        self.assertIn('input string InpComment        = "SniperEA_v8.6";', source)
        self.assertIn("SniperTrendEA v8.6", source)

    def test_v86_structure_inputs_exist(self):
        source = self.read_ea()
        required_inputs = [
            "InpUseStructureFilter",
            "InpSwingLookback",
            "InpStructureScanBars",
            "InpMinTrendlineTouches",
            "InpTrendlineTouchATR",
            "InpMinBreakoutDistanceATR",
            "InpMinBreakoutScore",
            "InpRejectNoStructure",
            "InpShowStructureDebug",
        ]
        for name in required_inputs:
            self.assertIn(name, source)

    def test_high_risk_recovery_patterns_are_not_added(self):
        source = self.read_ea().lower()
        banned_tokens = ["martingale", "grid", "averaging down", "recovery multiplier"]
        for token in banned_tokens:
            self.assertNotIn(token, source)

    def test_structure_helper_functions_exist(self):
        source = self.read_ea()
        required_snippets = [
            "struct STrendlineInfo",
            "void ResetTrendlineInfo",
            "double ClampDouble",
            "bool IsSwingHigh",
            "bool IsSwingLow",
            "double LineValueAtShift",
            "int CountTrendlineTouches",
            "bool FindValidatedTrendline",
            "double CalculateBreakoutScore",
            "bool PassStructureFilter",
        ]
        for snippet in required_snippets:
            self.assertIn(snippet, source)

    def test_structure_filter_is_called_for_buy_and_sell_entries(self):
        source = self.read_ea()
        self.assertIn("PassStructureFilter(true, atr1, dangerCandle, structure)", source)
        self.assertIn("PassStructureFilter(false, atr1, dangerCandle, structure)", source)
        self.assertIn("【结构过滤-多】评分不足或无有效结构，放弃", source)
        self.assertIn("【结构过滤-空】评分不足或无有效结构，放弃", source)

    def test_debug_comment_includes_v86_structure_state(self):
        source = self.read_ea()
        self.assertIn("Structure Filter:", source)
        self.assertIn("InpUseStructureFilter ? \"ON\" : \"OFF\"", source)


if __name__ == "__main__":
    unittest.main()
