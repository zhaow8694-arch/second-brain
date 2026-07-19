"""
💰 Financial Gateway (财务主权网关) — V2.8 核心组件

职责:
  1. 统一封装交易所 API，支持多交易所切换
  2. 双模运行: 虚拟模式 (virtual) / 实盘模式 (live)
  3. 自动检测 IS_TESTNET 环境变量，测试网自动切换端点
  4. 统一的订单接口: 查询余额 → 下单 → 查询持仓 → 撤单
  5. 智能仓位管理: 根据账户资金、风险比例、杠杆自动计算开仓数量
  6. 所有操作记录流水到 portfolio_log/ 和 SQLite 数据库

设计原则:
  - 上层代码不关心仓位计算，只需说"开多 BTC"
  - 网关内部自动计算: 数量 = (总资金 × 风险比例 × 杠杆) / 价格
  - 虚拟模式走本地 portfolio.json，实盘模式走交易所 API
"""
import os
import json
import time
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def get_mode() -> str:
    """获取当前网关运行模式

    每次调用都重新读取环境变量，支持运行时切换。
    - virtual: 虚拟模式，不连接交易所，走本地 portfolio.json
    - live: 实盘模式，连接交易所 API（测试网或主网由 IS_TESTNET 决定）
    """
    return os.getenv("GATEWAY_MODE", "virtual")


def is_testnet() -> bool:
    """判断是否测试网模式"""
    return os.getenv("IS_TESTNET", "True") == "True"


# ============================================================
# 仓位管理配置
# ============================================================
RISK_PER_TRADE = 0.10       # 单笔风险比例: 总资金的 10%
DEFAULT_LEVERAGE = 5         # 默认杠杆倍数


def set_risk_per_trade(ratio: float):
    """运行时调整风险比例"""
    global RISK_PER_TRADE
    RISK_PER_TRADE = max(0.01, min(0.50, ratio))


def get_risk_per_trade() -> float:
    """获取当前风险比例"""
    return RISK_PER_TRADE


def calculate_order_quantity(symbol: str, price: float = None) -> dict:
    """根据账户资金、风险比例、杠杆计算开仓数量

    公式:
      风险金额 = 账户总资金 × 风险比例
      仓位价值 = 风险金额 × 杠杆
      开仓数量 = 仓位价值 / 当前价格

    所有金额单位均为 USDT。

    Returns:
        {"quantity": float, "risk_amount": float, "position_value": float,
         "price": float, "total_equity": float, "leverage": int}
        或 {"error": "..."}
    """
    mode = get_mode()
    leverage = int(os.getenv("FUTURES_LEVERAGE", str(DEFAULT_LEVERAGE)))

    if mode == "virtual":
        from core.portfolio import get_portfolio_summary
        try:
            summary = get_portfolio_summary()
            total_equity = summary.get("total_equity", 100000)
        except Exception:
            total_equity = 100000
    else:
        try:
            client = _get_exchange()
            balance = client.fetch_balance()
            total_equity = balance.get("total", {}).get("USDT", 0)
        except Exception as e:
            return {"error": f"获取账户余额失败: {e}"}

    if price is None:
        try:
            ticker = _get_current_price(symbol)
            if ticker is None:
                return {"error": f"无法获取 {symbol} 当前价格"}
            price = ticker
        except Exception as e:
            return {"error": f"获取价格失败: {e}"}

    risk_amount = total_equity * RISK_PER_TRADE
    position_value = risk_amount * leverage
    quantity = position_value / price

    min_notional = 5.0
    if position_value < min_notional:
        quantity = min_notional / price

    if mode == "live":
        try:
            client = _get_exchange()
            quantity = client.adjust_quantity(symbol, quantity)
        except Exception:
            quantity = round(quantity, 6)

    return {
        "quantity": quantity,
        "risk_amount": round(risk_amount, 2),
        "position_value": round(position_value, 2),
        "price": round(price, 2),
        "total_equity": round(total_equity, 2),
        "leverage": leverage,
    }

PORTFOLIO_DIR = "portfolio_log"
PORTFOLIO_FILE = f"{PORTFOLIO_DIR}/portfolio.json"


class _FuturesClient:
    """U本位合约 API 客户端（直接使用 requests，绕过 ccxt sandbox 限制）

    测试网: https://testnet.binancefuture.com
    主网:   https://fapi.binance.com
    """

    def __init__(self):
        import ccxt
        futures_key = os.getenv("BINANCE_FUTURES_TESTNET_KEY")
        futures_secret = os.getenv("BINANCE_FUTURES_TESTNET_SECRET")
        if futures_key and futures_secret:
            self.api_key = futures_key
            self.secret = futures_secret
        else:
            self.api_key = os.getenv("BINANCE_TESTNET_API_KEY") or os.getenv("BINANCE_API_KEY", "")
            self.secret = os.getenv("BINANCE_TESTNET_SECRET_KEY") or os.getenv("BINANCE_SECRET", "")

        self.base_url = "https://testnet.binancefuture.com" if is_testnet() else "https://fapi.binance.com"
        self._ccxt = None

    def _ccxt_exchange(self):
        """返回一个 ccxt exchange 实例（仅用于公开数据查询，不用于签名请求）"""
        if self._ccxt is None:
            import ccxt
            self._ccxt = ccxt.binance({
                "apiKey": self.api_key,
                "secret": self.secret,
                "enableRateLimit": True,
                "options": {"defaultType": "future"},
            })
        return self._ccxt

    def _sign(self, params: dict) -> str:
        from urllib.parse import urlencode
        import hmac, hashlib
        query_string = urlencode(params)
        return hmac.new(self.secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()

    def _request(self, method: str, path: str, params: dict = None):
        import requests
        timestamp = int(time.time() * 1000)
        if params is None:
            params = {}
        params["timestamp"] = timestamp
        params["recvWindow"] = 10000
        params["signature"] = self._sign(params)
        headers = {"X-MBX-APIKEY": self.api_key}
        url = f"{self.base_url}{path}"
        if method == "GET":
            r = requests.get(url, headers=headers, params=params, timeout=15)
        else:
            r = requests.post(url, headers=headers, data=params, timeout=15)
        if not r.ok:
            try:
                err = r.json()
                raise Exception(f"{r.status_code} {r.reason}: {err}")
            except ValueError:
                pass
            r.raise_for_status()
        return r.json()

    def fetch_balance(self) -> dict:
        data = self._request("GET", "/fapi/v2/account")
        assets = data.get("assets", [])
        total = {}
        free = {}
        for a in assets:
            coin = a.get("asset", "")
            if coin:
                total[coin] = float(a.get("walletBalance", 0))
                free[coin] = float(a.get("availableBalance", 0))
        return {"total": total, "free": free, "info": data}

    def fetch_positions(self) -> list:
        data = self._request("GET", "/fapi/v2/account")
        positions_raw = data.get("positions", [])
        positions = []
        for pos in positions_raw:
            if isinstance(pos, dict):
                amt = float(pos.get("positionAmt", 0))
                if amt != 0:
                    positions.append({
                        "symbol": pos.get("symbol", "unknown"),
                        "quantity": abs(amt),
                        "direction": "long" if amt > 0 else "short",
                        "entry_price": float(pos.get("entryPrice", 0)),
                        "unrealized_pnl": float(pos.get("unrealizedProfit", 0)),
                    })
        return positions

    def set_leverage(self, symbol: str, leverage: int = None):
        if leverage is None:
            leverage = int(os.getenv("FUTURES_LEVERAGE", "5"))
        try:
            self._request("POST", "/fapi/v1/leverage", {
                "symbol": symbol.replace("/", ""),
                "leverage": leverage,
            })
        except Exception:
            pass

    def create_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None) -> dict:
        self.set_leverage(symbol)
        is_market = order_type.lower() == "market"
        pos_side = "LONG" if side.upper() == "BUY" else "SHORT"
        params = {
            "symbol": symbol.replace("/", ""),
            "side": side.upper(),
            "type": "MARKET" if is_market else "LIMIT",
            "quantity": quantity,
            "positionSide": pos_side,
        }
        if not is_market and price:
            params["price"] = price
            params["timeInForce"] = "GTC"
        try:
            data = self._request("POST", "/fapi/v1/order", params)
            executed_qty = data.get("executedQty", "0")
            if isinstance(executed_qty, str):
                executed_qty = float(executed_qty) if executed_qty else 0.0
            order_price = data.get("price", "0")
            if isinstance(order_price, str):
                order_price = float(order_price) if order_price else 0.0
            cum_quote = data.get("cumQuote", "0")
            if isinstance(cum_quote, str):
                cum_quote = float(cum_quote) if cum_quote else 0.0
            return {
                "status": data.get("status", "FILLED").lower(),
                "symbol": symbol,
                "side": side,
                "quantity": executed_qty or quantity,
                "price": order_price or (price or 0),
                "cost": cum_quote,
                "order_id": str(data.get("orderId", "unknown")),
                "mode": "live",
            }
        except Exception as e:
            return {"error": str(e), "mode": "live"}

    def cancel_order(self, order_id: str, symbol: str) -> dict:
        try:
            data = self._request("POST", "/fapi/v1/cancelOrder", {
                "symbol": symbol.replace("/", ""),
                "orderId": order_id,
            })
            return {"status": "canceled", "order_id": order_id, "mode": "live"}
        except Exception as e:
            return {"error": str(e), "mode": "live"}

    def set_stop_loss_take_profit(self, symbol: str, entry_price: float, side: str, quantity: float,
                                   stop_loss_price: float = None, take_profit_price: float = None) -> dict:
        """开仓后自动挂止盈止损条件单

        主网：使用 /fapi/v1/algo/order/new 接口（Algo Order API），服务端执行，程序离线也生效
        测试网：测试网不支持 Algo Order API，SL/TP 由本地轮询守护线程处理

        Args:
            symbol: 交易对，如 "BTC/USDT"
            entry_price: 开仓价格
            side: "long" 或 "short"
            quantity: 持仓数量
            stop_loss_price: 止损触发价格（USDT），由量化部门提供
            take_profit_price: 止盈触发价格（USDT），由量化部门提供

        Returns:
            {"stop_loss_order_id": ..., "take_profit_order_id": ..., "mode": "live"}
            或 {"error": "..."}
        """
        ccxt_symbol = symbol.replace("/", "")
        results = {}

        stop_side = "SELL" if side == "long" else "BUY"
        tick_size = self._get_price_precision(ccxt_symbol)

        is_testnet = "testnet" in self.base_url.lower()

        if is_testnet:
            # 测试网不支持服务端条件单，启动本地轮询守护线程
            results["mode"] = "testnet_local_polling"
            results["stop_loss_price"] = stop_loss_price
            results["take_profit_price"] = take_profit_price
            results["message"] = "测试网使用本地轮询止损，程序退出后止损失效"
            self._start_local_sltp_monitor(symbol, side, stop_loss_price, take_profit_price)
            return results

        # ——— 主网：止损条件单（Algo Order API）———
        if stop_loss_price is not None:
            sl_price = round(stop_loss_price / tick_size) * tick_size
            try:
                sl_data = self._request("POST", "/fapi/v1/algo/order/new", {
                    "symbol": ccxt_symbol,
                    "side": stop_side,
                    "type": "STOP_MARKET",
                    "closePosition": True,
                    "stopPrice": sl_price,
                    "workingType": "MARK_PRICE",
                    "positionSide": "BOTH",
                })
                results["stop_loss_order_id"] = str(sl_data.get("orderId", "unknown"))
                results["stop_loss_price"] = sl_price
            except Exception as e:
                results["stop_loss_error"] = str(e)

        # ——— 主网：止盈条件单（Algo Order API）———
        if take_profit_price is not None:
            tp_price = round(take_profit_price / tick_size) * tick_size
            try:
                tp_data = self._request("POST", "/fapi/v1/algo/order/new", {
                    "symbol": ccxt_symbol,
                    "side": stop_side,
                    "type": "TAKE_PROFIT_MARKET",
                    "closePosition": True,
                    "stopPrice": tp_price,
                    "workingType": "MARK_PRICE",
                    "positionSide": "BOTH",
                })
                results["take_profit_order_id"] = str(tp_data.get("orderId", "unknown"))
                results["take_profit_price"] = tp_price
            except Exception as e:
                results["take_profit_error"] = str(e)

        results["mode"] = "live"
        return results

    def _start_local_sltp_monitor(self, symbol: str, side: str,
                                   stop_loss: float = None, take_profit: float = None):
        """启动本地轮询止损/止盈守护线程（仅测试网使用）"""
        import threading
        ccxt_symbol = symbol.replace("/", "")

        def _poll():
            import time
            import requests as req
            while True:
                try:
                    ticker = req.get(
                        f"{self.base_url}/fapi/v1/ticker/price?symbol={ccxt_symbol}",
                        timeout=10
                    ).json()
                    price = float(ticker.get("price", 0))

                    if side == "long":
                        if stop_loss and price <= stop_loss:
                            self._request("POST", "/fapi/v1/order", {
                                "symbol": ccxt_symbol,
                                "side": "SELL",
                                "type": "MARKET",
                                "quantity": 0,
                                "closePosition": True,
                                "positionSide": "BOTH",
                            })
                            print(f"   🔴 测试网本地止损触发: {ccxt_symbol} @ {price}")
                            break
                        if take_profit and price >= take_profit:
                            self._request("POST", "/fapi/v1/order", {
                                "symbol": ccxt_symbol,
                                "side": "SELL",
                                "type": "MARKET",
                                "quantity": 0,
                                "closePosition": True,
                                "positionSide": "BOTH",
                            })
                            print(f"   🟢 测试网本地止盈触发: {ccxt_symbol} @ {price}")
                            break
                    else:
                        if stop_loss and price >= stop_loss:
                            self._request("POST", "/fapi/v1/order", {
                                "symbol": ccxt_symbol,
                                "side": "BUY",
                                "type": "MARKET",
                                "quantity": 0,
                                "closePosition": True,
                                "positionSide": "BOTH",
                            })
                            print(f"   🔴 测试网本地止损触发: {ccxt_symbol} @ {price}")
                            break
                        if take_profit and price <= take_profit:
                            self._request("POST", "/fapi/v1/order", {
                                "symbol": ccxt_symbol,
                                "side": "BUY",
                                "type": "MARKET",
                                "quantity": 0,
                                "closePosition": True,
                                "positionSide": "BOTH",
                            })
                            print(f"   🟢 测试网本地止盈触发: {ccxt_symbol} @ {price}")
                            break
                except Exception:
                    pass
                time.sleep(5)

        t = threading.Thread(target=_poll, daemon=True)
        t.start()
        print(f"   🔄 测试网本地 SL/TP 监控已启动: {ccxt_symbol} (SL={stop_loss}, TP={take_profit})")

    def _get_price_precision(self, ccxt_symbol: str) -> float:
        """获取交易对的价格精度 tickSize"""
        import requests
        try:
            r = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=15)
            data = r.json()
            for s in data.get("symbols", []):
                if s["symbol"] == ccxt_symbol:
                    for f in s.get("filters", []):
                        if f["filterType"] == "PRICE_FILTER":
                            return float(f["tickSize"])
        except Exception:
            pass
        return 0.01

    def fetch_ticker(self, symbol: str) -> dict:
        import requests
        try:
            r = requests.get(f"{self.base_url}/fapi/v1/ticker", params={"symbol": symbol.replace("/", "")}, timeout=10)
            data = r.json()
            if isinstance(data, dict) and "lastPrice" in data:
                return {"last": float(data["lastPrice"]), "symbol": symbol}
        except Exception:
            pass
        ex = self._ccxt_exchange()
        return ex.fetch_ticker(symbol)

    def get_lot_size(self, symbol: str) -> dict:
        """获取交易对的精度信息（stepSize, minQty 等）"""
        import requests
        try:
            ccxt_symbol = symbol.replace("/", "")
            r = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=15)
            data = r.json()
            for s in data.get("symbols", []):
                if s["symbol"] == ccxt_symbol:
                    for f in s.get("filters", []):
                        if f["filterType"] == "LOT_SIZE":
                            return {
                                "step_size": float(f["stepSize"]),
                                "min_qty": float(f["minQty"]),
                                "max_qty": float(f["maxQty"]),
                            }
        except Exception:
            pass
        return {"step_size": 0.001, "min_qty": 0.001, "max_qty": 1000}

    def adjust_quantity(self, symbol: str, raw_qty: float) -> float:
        """根据交易对精度调整数量"""
        lot = self.get_lot_size(symbol)
        step = lot["step_size"]
        precision = 0
        if step < 1:
            precision = len(str(step).split(".")[1].rstrip("0"))
        adjusted = round(raw_qty - (raw_qty % step), precision)
        if adjusted < lot["min_qty"]:
            adjusted = lot["min_qty"]
        if adjusted > lot["max_qty"]:
            adjusted = lot["max_qty"]
        return adjusted

    def fetch_time(self) -> int:
        import requests
        try:
            r = requests.get(f"{self.base_url}/fapi/v1/time", timeout=10)
            return int(r.json()["serverTime"])
        except Exception:
            return int(time.time() * 1000)

    def load_markets(self):
        pass


_client_instance = None


def _get_exchange():
    """获取 U本位合约客户端实例（单例）"""
    global _client_instance
    if _client_instance is None:
        _client_instance = _FuturesClient()
    return _client_instance


def check_connection() -> dict:
    """测试交易所连接状态

    Returns:
        {"status": "ok", "mode": "virtual|live", "exchange_time": ..., "balance_preview": ...}
        或 {"status": "error", "message": ...}
    """
    mode = get_mode()
    if mode == "virtual":
        return {
            "status": "ok",
            "mode": "virtual",
            "message": "虚拟模式运行中，不连接交易所",
        }

    try:
        client = _get_exchange()
        client.load_markets()
        server_time = client.fetch_time()
        balance = client.fetch_balance()
        non_zero = {k: float(v) for k, v in balance.get("total", {}).items() if v and float(v) > 0}
        return {
            "status": "ok",
            "mode": "live",
            "exchange": "binance" + (" (testnet)" if is_testnet() else ""),
            "server_time": datetime.fromtimestamp(server_time / 1000).isoformat(),
            "balance_preview": non_zero,
        }
    except Exception as e:
        return {"status": "error", "mode": "live", "message": str(e)}


def fetch_balance() -> dict:
    """获取账户余额

    Returns:
        虚拟模式: 从 portfolio.json 读取
        实盘模式: 从交易所 API 获取
    """
    mode = get_mode()
    if mode == "virtual":
        return _load_virtual_balance()
    try:
        client = _get_exchange()
        balance = client.fetch_balance()
        return {
            "total": balance.get("total", {}),
            "free": balance.get("free", {}),
            "mode": "live",
        }
    except Exception as e:
        return {"error": str(e), "mode": "live"}


def _load_virtual_balance() -> dict:
    """从本地 portfolio.json 加载虚拟余额"""
    if not os.path.exists(PORTFOLIO_FILE):
        return {
            "total": {"USDT": 100000},
            "free": {"USDT": 100000},
            "mode": "virtual",
        }
    try:
        with open(PORTFOLIO_FILE, "r") as f:
            pf = json.load(f)
        cash = pf.get("cash", 100000)
        positions = pf.get("positions", {})
        total_equity = cash
        for key, pos in positions.items():
            total_equity += pos["quantity"] * pos.get("current_price", pos["entry_price"])
        return {
            "total": {"USDT": round(total_equity, 2)},
            "free": {"USDT": round(cash, 2)},
            "mode": "virtual",
        }
    except Exception:
        return {"total": {"USDT": 100000}, "free": {"USDT": 100000}, "mode": "virtual"}


def create_order(symbol: str, side: str, order_type: str, quantity: float = None, price: float = None,
                 stop_loss_price: float = None, take_profit_price: float = None) -> dict:
    """创建订单（统一接口）

    支持两种调用方式:
      1. 传入 quantity: 使用指定数量
      2. 不传 quantity: 自动根据仓位管理模型计算

    止盈止损:
      - 实盘模式下，传入 stop_loss_price/take_profit_price 会自动挂条件单
      - 传入的是具体价格（USDT 计价），由量化部门计算，网关只负责执行

    Args:
        symbol: 交易对，如 "BTC/USDT"
        side: "buy" 或 "sell"
        order_type: "market" 或 "limit"
        quantity: 数量（为 None 时自动计算）
        price: 限价单价格（市价单不需要）
        stop_loss_price: 止损触发价格（USDT），由量化部门提供
        take_profit_price: 止盈触发价格（USDT），由量化部门提供

    Returns:
        订单结果字典（含止盈止损订单 ID）
    """
    if quantity is None:
        calc = calculate_order_quantity(symbol, price)
        if "error" in calc:
            return {"error": calc["error"], "mode": get_mode()}
        quantity = calc["quantity"]
        print(f"   📐 仓位计算: 总资金 ${calc['total_equity']:.2f} × {RISK_PER_TRADE*100:.0f}% × {calc['leverage']}x = "
              f"${calc['position_value']:.2f} → {quantity} 单位 @ ${calc['price']:.2f}")

    mode = get_mode()
    if mode == "virtual":
        return _virtual_create_order(symbol, side, order_type, quantity, price)

    result = _live_create_order(symbol, side, order_type, quantity, price)
    if "error" not in result and (stop_loss_price is not None or take_profit_price is not None):
        entry_price = price or _get_current_price(symbol) or 0
        if entry_price == 0:
            print("   ⚠️ 无法获取开仓价格，跳过止盈止损设置")
            return result
        direction = "long" if side == "buy" else "short"
        sltp = _get_exchange().set_stop_loss_take_profit(
            symbol, entry_price, direction, quantity,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
        )
        result["stop_loss"] = sltp.get("stop_loss_order_id", sltp.get("stop_loss_error", "failed"))
        result["take_profit"] = sltp.get("take_profit_order_id", sltp.get("take_profit_error", "failed"))
        if sltp.get("stop_loss_order_id"):
            print(f"   🛡️ 止损已挂: ${sltp['stop_loss_price']:.2f} | "
                  f"止盈已挂: ${sltp['take_profit_price']:.2f}")

    # 写入实盘交易记录到数据库
    if "error" not in result:
        _save_live_trade_to_db(symbol, side, order_type, quantity, result, stop_loss_price, take_profit_price)

    return result


def _save_live_trade_to_db(symbol: str, side: str, order_type: str, quantity: float,
                            result: dict, stop_loss_price: float = None, take_profit_price: float = None):
    """将实盘交易记录写入 SQLite 数据库"""
    try:
        from core.database import get_connection
        conn = get_connection()
        trade_id = result.get("order_id", str(uuid.uuid4()))
        conn.execute(
            """INSERT OR REPLACE INTO live_trades
               (id, session_id, symbol, side, order_type, quantity, price, cost, status,
                stop_loss_price, take_profit_price, stop_loss_order_id, take_profit_order_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                trade_id,
                f"gateway_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                symbol,
                side,
                order_type,
                quantity,
                result.get("price"),
                result.get("cost"),
                result.get("status", "filled"),
                stop_loss_price,
                take_profit_price,
                result.get("stop_loss"),
                result.get("take_profit"),
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"   ⚠️ 写入交易记录到数据库失败: {e}")


def _virtual_create_order(symbol: str, side: str, order_type: str, quantity: float, price: float = None) -> dict:
    """虚拟模式下单 — 直接操作 portfolio.json"""
    from core.portfolio import open_position, close_position

    session_id = f"gateway_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if side == "buy":
        entry_price = price or _get_current_price(symbol)
        if entry_price is None:
            return {"error": f"无法获取 {symbol} 当前价格", "mode": "virtual"}
        result = open_position(session_id, symbol, "long", quantity, entry_price)
        if "error" in result:
            return {"error": result["error"], "mode": "virtual"}
        return {
            "status": "filled",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": entry_price,
            "cost": round(quantity * entry_price, 2),
            "mode": "virtual",
            "order_id": result.get("position_id", "virtual"),
        }
    elif side == "sell":
        exit_price = price or _get_current_price(symbol)
        if exit_price is None:
            return {"error": f"无法获取 {symbol} 当前价格", "mode": "virtual"}
        pf_path = os.path.join(PORTFOLIO_DIR, "portfolio.json")
        direction = "long"
        if os.path.exists(pf_path):
            try:
                with open(pf_path) as f:
                    pf = json.load(f)
                if f"{symbol}_short" in pf.get("positions", {}):
                    direction = "short"
            except Exception:
                pass
        result = close_position(session_id, symbol, direction, exit_price, quantity)
        if "error" in result:
            return {"error": result["error"], "mode": "virtual"}
        return {
            "status": "filled",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": exit_price,
            "pnl": result.get("pnl", 0),
            "mode": "virtual",
            "order_id": f"close_{int(time.time())}",
        }
    return {"error": f"不支持的交易方向: {side}", "mode": "virtual"}


def _live_create_order(symbol: str, side: str, order_type: str, quantity: float, price: float = None) -> dict:
    """实盘模式下单 — 通过 _FuturesClient 调用交易所 API (U本位合约)"""
    client = _get_exchange()
    return client.create_order(symbol, side, order_type, quantity, price)


def _get_current_price(symbol: str) -> float:
    """获取当前价格（用于虚拟模式下单）"""
    try:
        from core.market_data import get_price
        data = get_price(symbol)
        if "error" not in data:
            return data["price"]
    except Exception:
        pass
    try:
        client = _get_exchange()
        ticker = client.fetch_ticker(symbol)
        return ticker["last"]
    except Exception:
        return None


def get_positions() -> list:
    """获取当前持仓

    Returns:
        持仓列表
    """
    mode = get_mode()
    if mode == "virtual":
        return _get_virtual_positions()
    return _get_live_positions()


def _get_virtual_positions() -> list:
    """从 portfolio.json 获取虚拟持仓"""
    from core.portfolio import get_portfolio_summary
    try:
        summary = get_portfolio_summary()
        return summary.get("positions", [])
    except Exception:
        return []


def _get_live_positions() -> list:
    """从交易所 API 获取实盘持仓 (U本位合约)"""
    try:
        client = _get_exchange()
        positions = client.fetch_positions()
        for p in positions:
            p["mode"] = "live"
        return positions
    except Exception as e:
        return [{"error": str(e)}]


def cancel_order(order_id: str, symbol: str = None) -> dict:
    """撤销订单

    Args:
        order_id: 订单 ID
        symbol: 交易对（实盘模式需要）

    Returns:
        撤单结果
    """
    mode = get_mode()
    if mode == "virtual":
        return {"status": "canceled", "order_id": order_id, "mode": "virtual"}
    if symbol is None:
        return {"error": "实盘模式撤单需要指定 symbol", "mode": "live"}
    try:
        client = _get_exchange()
        return client.cancel_order(order_id, symbol)
    except Exception as e:
        return {"error": str(e), "mode": "live"}


def get_gateway_status() -> dict:
    """获取网关状态摘要（供 dashboard 使用）"""
    mode = get_mode()
    balance = fetch_balance()
    if "error" in balance:
        return {"mode": mode, "error": balance["error"]}
    return {
        "mode": mode,
        "is_testnet": is_testnet(),
        "total_usdt": balance.get("total", {}).get("USDT", 0),
        "free_usdt": balance.get("free", {}).get("USDT", 0),
    }
