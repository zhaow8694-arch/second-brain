# Forward Test Checklist

## Before attaching EA
- Confirm account is demo/forward-test account, not full live account.
- Confirm symbol is XAUUSD and timeframe is H4.
- Confirm EA version is v8.67 production-ready or approved v8.66 robust line.
- Confirm set file is robust main case0010 lineage.
- Confirm aggressive set is not loaded.
- Confirm risk is reduced for any micro-live observation.
- Confirm AutoTrading status.
- Confirm VPS/time/data feed are stable.

## After attaching EA
- Check Experts and Journal tabs for errors.
- Confirm magic number and comment.
- Confirm no unexpected positions are opened.
- Record initial balance/equity in daily equity CSV.

## Daily check
- Record balance/equity/open positions.
- Record abnormal spread or connection events.
- Confirm no manual intervention unless documented.

## Weekly check
- Compare actual trade frequency with expected H4 behavior.
- Review losing streak and floating drawdown.
- Export account statement if trades occurred.

## Emergency stop conditions
- EA opens unexpected symbol/timeframe trades.
- Equity drawdown exceeds predefined limit.
- Multiple order errors occur.
- VPS/data feed instability occurs.
- Spread/slippage looks abnormal.

## Do-not-trade conditions
- Major platform/data issue.
- Wrong set file.
- Unverified EA build.
- Aggressive set accidentally loaded.