#!/usr/bin/env python3
"""Self-test MT5 log no-trade summary parser with synthetic fixtures."""

from pathlib import Path
import tempfile
import sys

import parse_mt5_log_no_trade_summary as parser


PASS_TEXT = "MT5 log no-trade parser self-test passed"
FAIL_TEXT = "MT5 log no-trade parser self-test failed"


def synthetic_log(
    *,
    expert="TradingSystem",
    include_expert=True,
    symbol="EURUSD",
    period="M5",
    include_symbol_period=True,
    include_inp_enable_trading=True,
    inp_enable_trading="false",
    observation_mode=False,
    include_risk_counters=True,
    risk_approved="0",
    execution_attempts="0",
    risk_rejected="6047",
    risk_reject_trading_disabled="6047",
    risk_reject_observation_mode=None,
    total_trades="0",
    total_deals="0",
    extra_lines=None,
):
    lines = []
    if include_expert:
        lines.append(
            f"testing of Experts\\{expert}\\{expert}.ex5 from 2024.01.01 00:00 to 2024.01.31 00:00"
        )
    if include_symbol_period:
        lines.append(f"{symbol},{period}")

    lines.append("InpEaName=TradingSystem_v0.1.7_core_signal_log_throttle")
    if include_inp_enable_trading:
        lines.append(f"InpEnableTrading={inp_enable_trading}")
    lines.append("InpEnableRiskObservation=true")
    lines.append("RiskManager initialized")
    if observation_mode:
        lines.append("Risk observation mode blocks all real trading")
        lines.append("RISK_REJECT_OBSERVATION_MODE")
    else:
        lines.append("RISK_REJECT_TRADING_DISABLED")

    if include_risk_counters:
        lines.append(f"riskRejected={risk_rejected}")
        lines.append(f"riskApproved={risk_approved}")
        lines.append(f"executionAttempts={execution_attempts}")
        if risk_reject_trading_disabled is not None:
            lines.append(f"riskRejectTradingDisabled={risk_reject_trading_disabled}")
        if risk_reject_observation_mode is not None:
            lines.append(f"riskRejectObservationMode={risk_reject_observation_mode}")

    lines.append(f"total trades={total_trades}")
    lines.append(f"total deals={total_deals}")
    if extra_lines:
        lines.extend(extra_lines)
    return "\n".join(lines) + "\n"


def parse_temp_log(log_text, expected_expert="TradingSystem"):
    with tempfile.TemporaryDirectory() as temp_dir:
        log_path = Path(temp_dir) / "synthetic_mt5.log"
        log_path.write_text(log_text, encoding="utf-8")
        return parser.parse_log_file(log_path, expected_expert=expected_expert)


def positive_disabled_trading_log():
    payload, issues = parse_temp_log(synthetic_log())
    if issues:
        return ["positive disabled trading log failed", "\n".join(issues)]

    checks = {
        "expertName": payload.get("expertName") == "TradingSystem",
        "symbol": payload.get("symbol") == "EURUSD",
        "period": payload.get("period") == "M5",
        "dateFrom": payload.get("dateFrom") == "2024.01.01",
        "dateTo": payload.get("dateTo") == "2024.01.31",
        "InpEnableTrading": payload.get("inputs", {}).get("InpEnableTrading") == "false",
        "riskApproved": payload.get("riskApproved") == 0,
        "executionAttempts": payload.get("executionAttempts") == 0,
        "riskRejected": payload.get("riskRejected") == 6047,
        "riskRejectTradingDisabled": payload.get("riskRejectTradingDisabled") == 6047,
        "totalTrades": payload.get("totalTrades") == 0,
        "totalDeals": payload.get("totalDeals") == 0,
        "passed": payload.get("noTradeAssertions", {}).get("passed") is True,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        return ["positive disabled trading log mismatch", "\n".join(failed)]
    return []


def positive_observation_mode_log():
    payload, issues = parse_temp_log(
        synthetic_log(
            observation_mode=True,
            inp_enable_trading="true",
            risk_rejected="94013",
            risk_reject_trading_disabled=None,
            risk_reject_observation_mode="94013",
        )
    )
    if issues:
        return ["positive observation-mode log failed", "\n".join(issues)]
    if payload.get("riskRejectObservationMode") != 94013:
        return ["positive observation-mode log mismatch", str(payload)]
    if payload.get("noTradeAssertions", {}).get("passed") is not True:
        return ["positive observation-mode no-trade assertion mismatch", str(payload)]
    return []


def positive_allow_expert_custom_expert():
    payload, issues = parse_temp_log(
        synthetic_log(expert="CustomEvidenceEA"),
        expected_expert="CustomEvidenceEA",
    )
    if issues:
        return ["positive --allow-expert custom expert failed", "\n".join(issues)]
    if payload.get("expertName") != "CustomEvidenceEA":
        return ["positive --allow-expert custom expert mismatch", str(payload)]
    return []


def expect_failure(label, log_text, required_text):
    payload, issues = parse_temp_log(log_text)
    del payload
    output = "\n".join(issues)
    if not issues:
        return [f"{label} did not fail", ""]
    if required_text not in output:
        return [f"{label} missing expected message", output]
    return []


def negative_missing_expert():
    return expect_failure(
        "negative missing expert",
        synthetic_log(include_expert=False),
        "missing required field: expertName",
    )


def negative_unrelated_expert_without_allow_expert():
    return expect_failure(
        "negative unrelated expert without --allow-expert",
        synthetic_log(expert="OtherEA"),
        "expertName must be",
    )


def negative_missing_risk_approved_execution_attempts():
    return expect_failure(
        "negative missing riskApproved / executionAttempts",
        synthetic_log(include_risk_counters=False),
        "missing required fields: riskApproved and executionAttempts",
    )


def negative_risk_approved_nonzero():
    return expect_failure(
        "negative riskApproved nonzero",
        synthetic_log(risk_approved="1"),
        "riskApproved must be 0",
    )


def negative_execution_attempts_nonzero():
    return expect_failure(
        "negative executionAttempts nonzero",
        synthetic_log(execution_attempts="1"),
        "executionAttempts must be 0",
    )


def negative_order_send_evidence():
    return expect_failure(
        "negative OrderSend evidence",
        synthetic_log(extra_lines=["OrderSend request sent"]),
        "forbidden real trading evidence found: OrderSend",
    )


def negative_buy_evidence():
    return expect_failure(
        "negative Buy( evidence",
        synthetic_log(extra_lines=["trade.Buy(0.10, _Symbol)"]),
        "forbidden real trading evidence found: Buy(",
    )


def negative_sell_evidence():
    return expect_failure(
        "negative Sell( evidence",
        synthetic_log(extra_lines=["trade.Sell(0.10, _Symbol)"]),
        "forbidden real trading evidence found: Sell(",
    )


def positive_direction_buy_sell_not_trade_api():
    payload, issues = parse_temp_log(
        synthetic_log(extra_lines=["Signal direction=BUY", "Signal direction=SELL"])
    )
    if issues:
        return ["positive direction BUY/SELL false positive", "\n".join(issues)]
    if payload.get("buySellEvidence") is not False:
        return ["positive direction BUY/SELL evidence mismatch", str(payload)]
    return []


def positive_negative_evidence_wording_allowed():
    payload, issues = parse_temp_log(
        synthetic_log(extra_lines=["no OrderSend / Buy / Sell evidence"])
    )
    if issues:
        return ["positive negative evidence wording failed", "\n".join(issues)]
    if payload.get("orderSendEvidence") is not False:
        return ["positive negative evidence wording mismatch", str(payload)]
    return []


def positive_safety_notes_present():
    payload, issues = parse_temp_log(synthetic_log())
    if issues:
        return ["positive safety notes failed", "\n".join(issues)]
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
        positive_disabled_trading_log,
        positive_observation_mode_log,
        positive_allow_expert_custom_expert,
        negative_missing_expert,
        negative_unrelated_expert_without_allow_expert,
        negative_missing_risk_approved_execution_attempts,
        negative_risk_approved_nonzero,
        negative_execution_attempts_nonzero,
        negative_order_send_evidence,
        negative_buy_evidence,
        negative_sell_evidence,
        positive_direction_buy_sell_not_trade_api,
        positive_negative_evidence_wording_allowed,
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
