#!/usr/bin/env python3
"""Self-test Strategy Tester HTML report parser with synthetic fixtures."""

from pathlib import Path
import json
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
PARSER = ROOT_DIR / "tools" / "parse_strategy_tester_html_report.py"
PASS_TEXT = "Strategy Tester HTML parser self-test passed"
FAIL_TEXT = "Strategy Tester HTML parser self-test failed"


def synthetic_html(
    *,
    expert="TradingSystem",
    symbol="EURUSD",
    period="M5 (2024.01.01 - 2024.01.31)",
    include_expert=True,
    include_inp_enable_trading=True,
    inp_enable_trading="false",
    total_trades="0",
    total_deals="0",
    buy_trades="0 (0.00%)",
    sell_trades="0 (0.00%)",
    include_trade_stats=True,
    deposit="10 000.00",
):
    expert_row = f"<tr><td>专家:</td><td>{expert}</td></tr>" if include_expert else ""
    input_rows = [
        "InpEaName=TradingSystem_v0.1.7_core_signal_log_throttle",
        "InpEnableRiskObservation=true",
    ]
    if include_inp_enable_trading:
        input_rows.insert(1, f"InpEnableTrading={inp_enable_trading}")
    input_html = "<br>".join(input_rows)
    stats = ""
    if include_trade_stats:
        stats = f"""
        <tr><td>交易总计:</td><td>{total_trades}</td></tr>
        <tr><td>总成交:</td><td>{total_deals}</td></tr>
        <tr><td>买入交易:</td><td>{buy_trades}</td></tr>
        <tr><td>卖出交易:</td><td>{sell_trades}</td></tr>
        """

    return f"""<!doctype html>
    <html>
      <head><title>策略测试报告</title></head>
      <body>
        <h1>策略测试报告</h1>
        <div>MetaQuotes-Demo (Build 5836)</div>
        <table>
          <tr><th colspan="2">设置</th></tr>
          {expert_row}
          <tr><td>交易品种:</td><td>{symbol}</td></tr>
          <tr><td>期间:</td><td>{period}</td></tr>
          <tr><td>初始存款:</td><td>{deposit}</td></tr>
          <tr><td>杠杆:</td><td>1:100</td></tr>
          <tr><td>输入:</td><td>{input_html}</td></tr>
          {stats}
        </table>
      </body>
    </html>"""


def run_parser(html_text=None, extra_args=None, encoding="utf-8", raw_bytes=None):
    with tempfile.TemporaryDirectory() as temp_dir:
        html_path = Path(temp_dir) / "synthetic_strategy_tester.html"
        if raw_bytes is not None:
            html_path.write_bytes(raw_bytes)
        else:
            html_path.write_text(html_text, encoding=encoding)
        args = [sys.executable, str(PARSER), str(html_path)]
        if extra_args:
            args.extend(extra_args)
        return subprocess.run(args, capture_output=True, text=True)


def utf16_le_bom_bytes(html_text):
    return b"\xff\xfe" + html_text.encode("utf-16-le")


def utf16_be_bom_bytes(html_text):
    return b"\xfe\xff" + html_text.encode("utf-16-be")


def combined_output(result):
    return ((result.stdout or "") + "\n" + (result.stderr or "")).strip()


def positive_chinese_mt5_report_fixture():
    result = run_parser(synthetic_html(), ["--pretty"])
    output = combined_output(result)
    if result.returncode != 0:
        return ["positive Chinese MT5 report fixture failed", output]
    payload = json.loads(result.stdout)
    checks = {
        "expertName": payload.get("expertName") == "TradingSystem",
        "symbol": payload.get("symbol") == "EURUSD",
        "period": payload.get("period") == "M5",
        "dateFrom": payload.get("dateFrom") == "2024.01.01",
        "dateTo": payload.get("dateTo") == "2024.01.31",
        "build": payload.get("build") == "5836",
        "InpEnableTrading": payload.get("inputs", {}).get("InpEnableTrading") == "false",
        "totalTrades": payload.get("totalTrades") == 0,
        "totalDeals": payload.get("totalDeals") == 0,
        "buyTrades": payload.get("buyTrades") == 0,
        "sellTrades": payload.get("sellTrades") == 0,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        return ["positive Chinese MT5 report fixture mismatch", "\n".join(failed)]
    return []


def positive_utf8_bom_report_fixture():
    result = run_parser(raw_bytes=b"\xef\xbb\xbf" + synthetic_html().encode("utf-8"))
    output = combined_output(result)
    if result.returncode != 0:
        return ["positive UTF-8 BOM report fixture failed", output]
    payload = json.loads(result.stdout)
    if payload.get("expertName") != "TradingSystem" or payload.get("totalDeals") != 0:
        return ["positive UTF-8 BOM report fixture mismatch", result.stdout]
    return []


def positive_utf16_le_bom_report_fixture():
    result = run_parser(raw_bytes=utf16_le_bom_bytes(synthetic_html()))
    output = combined_output(result)
    if result.returncode != 0:
        return ["positive UTF-16-LE BOM report fixture failed", output]
    payload = json.loads(result.stdout)
    checks = {
        "expertName": payload.get("expertName") == "TradingSystem",
        "symbol": payload.get("symbol") == "EURUSD",
        "period": payload.get("period") == "M5",
        "dateFrom": payload.get("dateFrom") == "2024.01.01",
        "dateTo": payload.get("dateTo") == "2024.01.31",
        "InpEnableTrading": payload.get("inputs", {}).get("InpEnableTrading") == "false",
        "InpEnableRiskObservation": (
            payload.get("inputs", {}).get("InpEnableRiskObservation") == "true"
        ),
        "totalTrades": payload.get("totalTrades") == 0,
        "totalDeals": payload.get("totalDeals") == 0,
        "buyTrades": payload.get("buyTrades") == 0,
        "sellTrades": payload.get("sellTrades") == 0,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        return ["positive UTF-16-LE BOM report fixture mismatch", "\n".join(failed)]
    return []


def positive_utf16_be_bom_report_fixture():
    result = run_parser(raw_bytes=utf16_be_bom_bytes(synthetic_html()))
    output = combined_output(result)
    if result.returncode != 0:
        return ["positive UTF-16-BE BOM report fixture failed", output]
    payload = json.loads(result.stdout)
    if payload.get("expertName") != "TradingSystem" or payload.get("sellTrades") != 0:
        return ["positive UTF-16-BE BOM report fixture mismatch", result.stdout]
    return []


def positive_utf16_report_fixture():
    result = run_parser(synthetic_html(), encoding="utf-16")
    output = combined_output(result)
    if result.returncode != 0:
        return ["positive UTF-16 report fixture failed", output]
    payload = json.loads(result.stdout)
    if payload.get("expertName") != "TradingSystem" or payload.get("totalTrades") != 0:
        return ["positive UTF-16 report fixture mismatch", result.stdout]
    return []


def positive_allow_expert_custom_expert():
    result = run_parser(
        synthetic_html(expert="CustomEvidenceEA"),
        ["--allow-expert", "CustomEvidenceEA"],
    )
    if result.returncode != 0:
        return ["positive --allow-expert custom expert failed", combined_output(result)]
    payload = json.loads(result.stdout)
    if payload.get("expertName") != "CustomEvidenceEA":
        return ["positive --allow-expert custom expert mismatch", result.stdout]
    return []


def expect_failure(label, html_text, required_text, raw_bytes=None):
    result = run_parser(html_text, raw_bytes=raw_bytes)
    output = combined_output(result)
    if result.returncode == 0:
        return [f"{label} did not fail", output]
    if required_text not in output:
        return [f"{label} missing expected message", output]
    return []


def negative_missing_expert():
    return expect_failure(
        "negative missing expert",
        synthetic_html(include_expert=False),
        "missing required field: expertName",
    )


def negative_unrelated_expert_without_allow_expert():
    return expect_failure(
        "negative unrelated expert without --allow-expert",
        synthetic_html(expert="OtherEA"),
        "expertName must be",
    )


def negative_missing_inp_enable_trading():
    return expect_failure(
        "negative missing InpEnableTrading",
        synthetic_html(include_inp_enable_trading=False),
        "missing required input: InpEnableTrading",
    )


def negative_inp_enable_trading_true():
    return expect_failure(
        "negative InpEnableTrading=true",
        synthetic_html(inp_enable_trading="true"),
        "InpEnableTrading must be false",
    )


def negative_nonzero_total_trades():
    return expect_failure(
        "negative nonzero totalTrades",
        synthetic_html(total_trades="1"),
        "totalTrades must be 0",
    )


def negative_nonzero_total_deals():
    return expect_failure(
        "negative nonzero totalDeals",
        synthetic_html(total_deals="1"),
        "totalDeals must be 0",
    )


def negative_missing_trade_stats():
    return expect_failure(
        "negative missing trade stats",
        synthetic_html(include_trade_stats=False),
        "missing required field: totalTrades",
    )


def negative_invalid_undecodable_byte_stream():
    result = run_parser(raw_bytes=b"\xff\xfe\x00")
    output = combined_output(result)
    if result.returncode == 0:
        return ["negative invalid byte stream did not fail", output]
    if "could not decode HTML report" not in output:
        return ["negative invalid byte stream missing expected message", output]
    return []


def negative_utf16_inp_enable_trading_true():
    return expect_failure(
        "negative UTF-16 InpEnableTrading=true",
        synthetic_html(inp_enable_trading="true"),
        "InpEnableTrading must be false",
        raw_bytes=utf16_le_bom_bytes(synthetic_html(inp_enable_trading="true")),
    )


def negative_utf16_nonzero_total_trades():
    return expect_failure(
        "negative UTF-16 nonzero totalTrades",
        synthetic_html(total_trades="1"),
        "totalTrades must be 0",
        raw_bytes=utf16_le_bom_bytes(synthetic_html(total_trades="1")),
    )


def positive_number_normalization():
    result = run_parser(synthetic_html(deposit="10 000.00"))
    if result.returncode != 0:
        return ["positive number normalization failed", combined_output(result)]
    payload = json.loads(result.stdout)
    if payload.get("initialDeposit") != "10000.00":
        return ["positive number normalization mismatch", result.stdout]
    return []


def positive_buy_sell_percent_normalization():
    result = run_parser(
        synthetic_html(buy_trades="0 (0.00%)", sell_trades="0 (0.00%)")
    )
    if result.returncode != 0:
        return ["positive buy/sell normalization failed", combined_output(result)]
    payload = json.loads(result.stdout)
    if payload.get("buyTrades") != 0 or payload.get("sellTrades") != 0:
        return ["positive buy/sell normalization mismatch", result.stdout]
    return []


def positive_safety_notes_present():
    result = run_parser(synthetic_html())
    if result.returncode != 0:
        return ["positive safety notes failed", combined_output(result)]
    payload = json.loads(result.stdout)
    notes = "\n".join(payload.get("safetyNotes", []))
    for text in (
        "not live trading readiness",
        "not real trading permission",
        "not profitability claim",
    ):
        if text not in notes:
            return ["positive safety notes missing", notes]
    return []


def main():
    failures = []
    for test in (
        positive_chinese_mt5_report_fixture,
        positive_utf8_bom_report_fixture,
        positive_utf16_le_bom_report_fixture,
        positive_utf16_be_bom_report_fixture,
        positive_utf16_report_fixture,
        positive_allow_expert_custom_expert,
        negative_missing_expert,
        negative_unrelated_expert_without_allow_expert,
        negative_missing_inp_enable_trading,
        negative_inp_enable_trading_true,
        negative_nonzero_total_trades,
        negative_nonzero_total_deals,
        negative_missing_trade_stats,
        negative_invalid_undecodable_byte_stream,
        negative_utf16_inp_enable_trading_true,
        negative_utf16_nonzero_total_trades,
        positive_number_normalization,
        positive_buy_sell_percent_normalization,
        positive_safety_notes_present,
    ):
        result = test()
        if result:
            failures.append(result)

    if failures:
        print(FAIL_TEXT)
        for failure in failures:
            print(f"- {failure[0]}")
            if len(failure) > 1 and failure[1]:
                print(failure[1])
        return 1

    print(PASS_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
