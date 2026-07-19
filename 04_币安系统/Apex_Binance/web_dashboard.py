"""
Web 监控面板模块
提供实时可视化监控界面，在浏览器中查看交易系统状态
"""
import threading
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from datetime import datetime
from typing import Dict, Any, List, Optional


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """多线程HTTP服务器，避免GIL阻塞"""
    daemon_threads = True


# 共享状态（线程安全）
dashboard_state: Dict[str, Any] = {
    'running': True,
    'start_time': None,
    'current_equity': 0.0,
    'initial_equity': 0.0,
    'daily_pnl_pct': 0.0,
    'total_pnl_pct': 0.0,
    'positions': [],
    'risk_level': '低',
    'signal_count': 0,
    'total_trades': 0,
    'win_rate': 0.0,
    'last_update': '',
    'uptime': '',
    'cooldown_until': None,
    'errors': [],  # 最近错误
}
_state_lock = threading.Lock()


def update_state(**kwargs):
    """更新共享状态"""
    with _state_lock:
        dashboard_state.update(kwargs)


def get_state() -> Dict[str, Any]:
    """获取共享状态副本"""
    with _state_lock:
        return dict(dashboard_state)


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""

    def log_message(self, format, *args):
        pass  # 静默日志

    def do_GET(self):
        if self.path == '/api/state':
            self._send_json(get_state())
        else:
            self._send_html()

    def _send_json(self, data):
        body = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self):
        try:
            html = self._render_html()
        except Exception as e:
            html = f"<h1>500 Error</h1><pre>{e}</pre>"
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def _render_html(self):
        state = get_state()
        positions_html = self._render_positions(state.get('positions', []))
        errors_html = self._render_errors(state.get('errors', []))
        
        # 安全取值
        eq = state.get('current_equity') or 0.0
        init_eq = state.get('initial_equity') or 0.0
        tp = state.get('total_pnl_pct') or 0.0
        dp = state.get('daily_pnl_pct') or 0.0
        pos_count = len(state.get('positions', []))

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Guardian Earth 交易面板</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ 
    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; 
    background: #0d1117; color: #c9d1d9; padding: 20px;
    min-height: 100vh;
  }}
  .header {{ 
    text-align: center; padding: 20px 0; border-bottom: 1px solid #21262d; margin-bottom: 20px;
  }}
  .header h1 {{ color: #58a6ff; font-size: 24px; margin-bottom: 5px; }}
  .header .sub {{ color: #8b949e; font-size: 13px; }}
  .status-dot {{
    display: inline-block; width: 10px; height: 10px; border-radius: 50%;
    background: #3fb950; margin-right: 6px; animation: pulse 1.5s infinite;
  }}
  @keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.4}} }}
  .cards {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px; margin-bottom: 20px;
  }}
  .card {{
    background: #161b22; border: 1px solid #21262d; border-radius: 8px;
    padding: 16px; text-align: center;
  }}
  .card .label {{ color: #8b949e; font-size: 12px; text-transform: uppercase; margin-bottom: 6px; }}
  .card .value {{ font-size: 22px; font-weight: 700; }}
  .card .sub-value {{ font-size: 12px; color: #8b949e; margin-top: 4px; }}
  .green {{ color: #3fb950; }}
  .red {{ color: #f85149; }}
  .yellow {{ color: #d2991d; }}
  .blue {{ color: #58a6ff; }}
  .section {{
    background: #161b22; border: 1px solid #21262d; border-radius: 8px;
    padding: 16px; margin-bottom: 15px;
  }}
  .section h2 {{ color: #58a6ff; font-size: 16px; margin-bottom: 12px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ text-align: left; color: #8b949e; font-size: 12px; padding: 8px 6px; border-bottom: 1px solid #21262d; }}
  td {{ padding: 8px 6px; font-size: 13px; border-bottom: 1px solid #1a1f27; }}
  .badge {{
    display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px;
    font-weight: 600;
  }}
  .badge-long {{ background: #0d3320; color: #3fb950; }}
  .badge-short {{ background: #3d1214; color: #f85149; }}
  .badge-risk {{ background: #1c2333; color: #58a6ff; }}
  .badge-danger {{ background: #3d1214; color: #f85149; }}
  .badge-warn {{ background: #3d2e0b; color: #d2991d; }}
  .footer {{ text-align: center; color: #484f58; font-size: 11px; padding: 10px; }}
  .no-data {{ color: #484f58; text-align: center; padding: 20px; }}
  .error-row {{ background: #1a1215; }}
</style>
</head>
<body>
<div class="header">
  <h1><span class="status-dot"></span>Guardian Earth 交易系统</h1>
  <div class="sub" id="update_time">Z-Wei 智能交易 | 模拟模式 | 最后更新: {state.get('last_update', '--')} | 运行: {state.get('uptime', '--')}</div>
</div>

<div class="cards">
  <div class="card">
    <div class="label">账户权益</div>
    <div class="value blue" id="equity">{eq:.2f} USDT</div>
    <div class="sub-value" id="initial">初始: {init_eq:.2f}</div>
  </div>
  <div class="card">
    <div class="label">总收益</div>
    <div class="value {self._color_class(tp)}" id="total_pnl">{tp:+.2%}</div>
    <div class="sub-value">{self._pnl_usdt(state)}</div>
  </div>
  <div class="card">
    <div class="label">当日盈亏</div>
    <div class="value {self._color_class(dp)}" id="daily_pnl">{dp:+.2%}</div>
    <div class="sub-value">风险等级: {state.get('risk_level', '低')}</div>
  </div>
  <div class="card">
    <div class="label">持仓 / 上限</div>
    <div class="value" id="pos_count">{pos_count} / 6</div>
    <div class="sub-value">信号数: {state.get('signal_count', 0)}</div>
  </div>
  <div class="card">
    <div class="label">总交易 / 胜率</div>
    <div class="value" id="trades">{state.get('total_trades', 0)} / {state.get('win_rate', 0):.0%}</div>
    <div class="sub-value">冷却: {'是' if state.get('cooldown_until') else '否'}</div>
  </div>
</div>

<div class="section">
  <h2>当前持仓</h2>
  {positions_html}
</div>

{errors_html}

<div class="footer">Guardian Earth v1.0 | 自动刷新 5s | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
<script>
setInterval(function(){{ fetch('/api/state').then(r=>r.json()).then(d=>{{ 
  document.getElementById('equity').textContent=d.current_equity.toFixed(2)+' USDT';
  document.getElementById('initial').textContent='初始: '+d.initial_equity.toFixed(2);
  document.getElementById('total_pnl').textContent=(d.total_pnl_pct*100).toFixed(2)+'%';
  document.getElementById('daily_pnl').textContent=(d.daily_pnl_pct*100).toFixed(2)+'%';
  var pc=d.positions.length+' / 6'; document.getElementById('pos_count').textContent=pc;
  document.getElementById('trades').textContent=(d.total_trades||0)+' / '+((d.win_rate||0)*100).toFixed(0)+'%';
  document.getElementById('update_time').textContent='最后更新: '+d.last_update+' | 运行: '+d.uptime;
  var rows=''; (d.positions||[]).forEach(function(p){{
    var sc=p.side=='long'?'badge-long':'badge-short';
    var pc2=p.unrealized_pnl>=0?'green':'red';
    rows+='<tr><td>'+p.symbol+'</td><td><span class=\"badge '+sc+'\">'+p.side+'</span></td><td>'+p.size+'</td><td>'+p.entry_price+'</td><td>'+p.current_price+'</td><td class=\"'+pc2+'\">'+(p.unrealized_pnl>=0?'+':'')+p.unrealized_pnl.toFixed(2)+'</td><td class=\"'+pc2+'\">'+(p.unrealized_pnl_pct>=0?'+':'')+(p.unrealized_pnl_pct*100).toFixed(2)+'%</td><td>'+(p.stop_loss||0)+'</td></tr>';
  }});
  if(rows) document.getElementById('pos_rows').innerHTML=rows;
  else document.getElementById('pos_rows').innerHTML='<tr><td colspan=\"8\" style=\"text-align:center;color:#484f58\">暂无持仓</td></tr>';
}}).catch(function(){{}}); }},5000);
</script>
</body>
</html>"""

    def _render_positions(self, positions) -> str:
        if not positions:
            return '<div class="no-data">暂无持仓，等待交易信号...</div>'

        rows = []
        for p in positions:
            side_class = 'badge-long' if p.get('side') == 'long' else 'badge-short'
            pnl_class = self._color_class(p.get('unrealized_pnl', 0))
            rows.append(f"""<tr>
                <td>{p.get('symbol', '?')}</td>
                <td><span class="badge {side_class}">{p.get('side', '?')}</span></td>
                <td>{p.get('size', 0):.3f}</td>
                <td>{p.get('entry_price', 0):.4f}</td>
                <td>{p.get('current_price', 0):.4f}</td>
                <td class="{pnl_class}">{p.get('unrealized_pnl', 0):+.2f}</td>
                <td class="{pnl_class}">{p.get('unrealized_pnl_pct', 0):+.2%}</td>
                <td>{p.get('stop_price', 0):.4f}</td>
            </tr>""")

        return f"""<table>
            <thead><tr><th>交易对</th><th>方向</th><th>数量</th><th>入场价</th><th>当前价</th><th>未实现盈亏</th><th>盈亏%</th><th>止损价</th></tr></thead>
            <tbody id="pos_rows">
            {''.join(rows)}
            </tbody>
            </table>"""

    def _render_errors(self, errors) -> str:
        if not errors:
            return ''
        rows = []
        for e in errors[-5:]:
            rows.append(f'<tr class="error-row"><td>{e.get("time", "")}</td><td style="color:#f85149">{e.get("msg", "")}</td></tr>')
        return f"""<div class="section">
            <h2>最近错误</h2>
            <table><tr><th>时间</th><th>信息</th></tr>{''.join(rows)}</table>
            </div>"""

    def _color_class(self, value) -> str:
        if value > 0: return 'green'
        if value < 0: return 'red'
        return ''

    def _pnl_usdt(self, state) -> str:
        total = state['total_pnl_pct'] * state['initial_equity']
        color = 'green' if total >= 0 else 'red'
        return f'<span class="{color}">{total:+.2f} USDT</span>'


def start_dashboard(port: int = 8080):
    """启动 Web 监控服务器"""
    import logging
    log = logging.getLogger(__name__)
    server = ThreadingHTTPServer(('0.0.0.0', port), DashboardHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    log.info(f"Web面板线程已启动，端口: {port}")
    return server
