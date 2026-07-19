from core.battle_log import write_log
from core.cost_watchdog import record_call
from core.model_router import get_llm_config
from langchain_openai import ChatOpenAI


def _make_llm(tier: str = "low", temperature: float = 0.3):
    """从 model_router 统一获取 LLM 实例，内置降级与计费接管。"""
    cfg = get_llm_config(tier)
    return ChatOpenAI(
        model=cfg["model"],
        api_key=cfg["api_key"],
        base_url=cfg["base_url"],
        temperature=temperature,
    )


def run_dashboard_mission(session_id: str):
    """全军战力看板 — 实时显示各部门状态"""
    from core.dashboard import print_dashboard, generate_dashboard_report

    print("\n📊 全军战力看板启动 — 实时状态汇总")
    print_dashboard()

    save = input("\n💾 是否保存看板报告到文件? (y/n): ").strip().lower()
    if save == "y":
        report_file = generate_dashboard_report(session_id)
        print(f"   报告已保存: {report_file}")

    record_call("全军看板", 0, 0)
    write_log(session_id, "DASHBOARD", "全军状态", "看板已生成")
    return "全军战力看板已展示"


def run_campaign_execute_mission(session_id: str):
    """战役自动执行 — 按模板自动调用各部门作战函数"""
    from command.campaign import list_templates, execute_campaign

    print("\n⚡ 战役自动执行启动 — 按模板自动调用各部门")

    templates = list_templates()
    print("\n📋 可用战役模板:")
    template_list = list(templates.keys())
    for i, (name, info) in enumerate(templates.items(), 1):
        print(f"  {i}. {name} ({info['phases']} 个阶段) — {info['description']}")

    choice = input("\n🎯 请选择战役模板: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(template_list):
            template_name = template_list[idx]
        else:
            template_name = template_list[0]
    except ValueError:
        template_name = template_list[0]

    target = input("🎯 输入战役目标（可选）: ").strip()

    print(f"\n⚡ 开始自动执行战役: {template_name}...")
    report_file = execute_campaign(session_id, template_name, target)
    print(f"\n✅ 战役执行完成! 报告已保存: {report_file}")

    record_call("战役自动执行", 0, 0.05)
    write_log(session_id, "CAMPAIGN_EXECUTE", template_name, f"战役自动执行完成: {report_file}")
    return f"战役自动执行完成: {report_file}"


def run_identity_mission(session_id: str):
    """影子特工处 — 数字身份管理"""
    from core.identity_manager import (
        init_default_identities, get_identity_health, use_identity,
        add_identity, remove_identity, get_identity_status,
    )

    print("\n🎭 影子特工处启动 — 数字身份管理")

    init_default_identities()
    health = get_identity_health()
    print(f"   身份池健康度: {health['status']}")
    print(f"   总身份数: {health['total_identities']}")
    print(f"   覆盖平台: {health['platforms']}")

    print("\n📋 平台身份分布:")
    for platform, stats in health.get("platform_stats", {}).items():
        print(f"   {platform}: {stats['count']} 个身份, 语言: {', '.join(stats['languages'])}")

    print("\n🎯 可执行操作:")
    print("   1. 使用一个身份（模拟发布）")
    print("   2. 添加新身份")
    print("   3. 查看完整状态")

    op = input("\n请选择: ").strip()
    if op == "1":
        platform = input("平台 (twitter/reddit/telegram): ").strip() or "twitter"
        lang = input("语言 (en/zh/ja/id): ").strip() or "en"
        result = use_identity(session_id, platform, lang)
        print(f"   ✅ 使用身份: {result['identity']['name']}")
        print(f"   🖥️  模拟指纹: {result['fingerprint']['user_agent'][:50]}...")
    elif op == "2":
        platform = input("平台: ").strip()
        name = input("身份名称: ").strip()
        lang = input("语言: ").strip() or "en"
        bio = input("简介: ").strip() or "AI Agent"
        add_identity(platform, name, lang, bio)
        print(f"   ✅ 已添加身份: {name}")
    else:
        status = get_identity_status()
        print(f"\n📊 影子特工处状态:")
        print(f"   总身份数: {status['total_identities']}")
        print(f"   覆盖平台: {status['platforms']}")
        print(f"   健康度: {status['status']}")

    record_call("影子特工处", 0, 0)
    write_log(session_id, "IDENTITY", "身份管理", "影子特工处操作完成")
    return "影子特工处操作完成"


def run_guard_dog_mission(session_id: str):
    """物理防火墙 — 系统安全巡逻"""
    from core.guard_dog import patrol, get_guard_dog_status, trigger_meltdown, release_meltdown, is_meltdown_active

    print("\n🐕 物理防火墙 (Guard Dog) 启动 — 系统安全巡逻")

    status = get_guard_dog_status()
    meltdown_icon = "🔴" if status["meltdown_active"] else "🟢"
    print(f"   熔断状态: {meltdown_icon} {'已触发' if status['meltdown_active'] else '正常'}")
    print(f"   上次巡逻: {status['last_patrol_time']}")
    print(f"   历史事件: {status['total_incidents']} 次")

    print("\n🔍 执行安全巡逻...")
    report = patrol()
    status_icon = {"healthy": "🟢", "alert": "🟡", "meltdown": "🔴"}.get(report["status"], "⚪")
    print(f"   巡逻状态: {status_icon} {report['status']}")

    for check in report["checks"]:
        check_icon = "✅" if check["passed"] else "⚠️"
        print(f"   {check_icon} {check['message']}")

    if report["alerts"]:
        print(f"\n⚠️  发现 {len(report['alerts'])} 个告警:")
        for alert in report["alerts"]:
            print(f"   - {alert}")

        action = input("\n🛑 是否触发熔断? (y/n): ").strip().lower()
        if action == "y":
            trigger_meltdown("Guard Dog 巡逻发现异常")
            print("   🔴 熔断已触发! 系统将停止所有任务。")
            print("   解除熔断请运行: python -c \"from core.guard_dog import release_meltdown; release_meltdown()\"")
    else:
        print("\n✅ 系统安全，无异常")

    record_call("物理防火墙", 0, 0)
    write_log(session_id, "GUARD_DOG", "安全巡逻", f"巡逻状态: {report['status']}")
    return f"Guard Dog 巡逻完成: {report['status']}"


def run_rag_mission(session_id: str):
    """中央知识库 — 知识管理与检索"""
    from core.rag_engine import (
        add_knowledge, search_knowledge, get_knowledge_stats,
        learn_from_failure, learn_from_success, get_rag_status,
    )

    print("\n📚 中央知识库 (RAG) 启动 — 知识管理与检索")

    stats = get_knowledge_stats()
    print(f"   总知识条目: {stats['total_entries']}")
    print(f"   分类: {stats['categories']}")
    print(f"   来源: {stats['sources']}")

    print("\n🎯 可执行操作:")
    print("   1. 搜索知识库")
    print("   2. 添加知识条目")
    print("   3. 查看完整状态")

    op = input("\n请选择: ").strip()
    if op == "1":
        query = input("🔍 搜索关键词: ").strip()
        results = search_knowledge(query)
        print(f"\n   找到 {len(results)} 条匹配结果:")
        for i, r in enumerate(results, 1):
            print(f"   {i}. [{r.get('category', '未分类')}] {r.get('content', '')[:80]}...")
            print(f"      来源: {r.get('source', '未知')} | 标签: {', '.join(r.get('tags', [])[:3])}")
    elif op == "2":
        source = input("来源 (如: 金融重击/兵工厂/宣发军): ").strip()
        content = input("知识内容: ").strip()
        category = input("分类 (失败经验/成功经验/策略/规则): ").strip() or "经验"
        add_knowledge(source, content, category, session_id)
        print(f"   ✅ 知识已添加")
    else:
        status = get_rag_status()
        print(f"\n📊 中央知识库状态:")
        print(f"   总条目: {status['total_entries']}")
        print(f"   分类: {status['categories']}")
        print(f"   来源: {status['sources']}")
        print(f"   热门标签: {[t['tag'] for t in status.get('top_tags', [])[:5]]}")

    record_call("中央知识库", 0, 0)
    write_log(session_id, "RAG", "知识管理", "中央知识库操作完成")
    return "中央知识库操作完成"


def run_financial_mission(session_id: str, symbols: list = None):
    import os
    from datetime import datetime
    from dotenv import load_dotenv
    load_dotenv()
    from crewai import Agent, Task, Crew, Process
    from langchain_openai import ChatOpenAI
    from core.market_data import get_price, get_historical_data, SYMBOL_CONFIG, get_macro_data
    from core.backtester import run_backtest, get_available_strategies
    from core.portfolio import open_position, get_portfolio_summary
    from core.tools import get_market_summary_for_agent, macro_environment_tool, available_symbols_tool, get_macro_tool, get_available_symbols_tool, get_market_history_tool
    import signal

    all_symbols = list(SYMBOL_CONFIG.keys())

    if symbols is None:
        print(f"\n📋 可选标的 ({len(all_symbols)} 个):")
        for i, s in enumerate(all_symbols, 1):
            print(f"   {i:2d}. {s:12s} — {SYMBOL_CONFIG[s]['name']}")
        print(f"   {len(all_symbols)+1:2d}. 全部分析")
        raw = input("\n🎯 请选择要分析的标的（输入编号，逗号分隔）: ").strip()
        try:
            indices = [int(x.strip()) for x in raw.split(",") if x.strip()]
            if len(all_symbols) + 1 in indices:
                symbols = all_symbols
            else:
                symbols = [all_symbols[i-1] for i in indices if 1 <= i <= len(all_symbols)]
        except (ValueError, IndexError):
            symbols = all_symbols
        if not symbols:
            symbols = all_symbols
    else:
        symbols = [s for s in symbols if s in all_symbols]
        if not symbols:
            print(f"   ⚠️ 指定的标的均不可用，使用全部标的")
            symbols = all_symbols

    print(f"\n📡 监控目标: {len(symbols)} 个标的")
    for i, s in enumerate(symbols, 1):
        print(f"   {i:2d}. {s:12s} — {SYMBOL_CONFIG[s]['name']}")

    print("\n📡 正在获取实时行情数据...")
    market_data = {}
    for symbol in symbols:
        try:
            price_data = get_price(symbol)
            if "error" not in price_data:
                market_data[symbol] = price_data
                config = SYMBOL_CONFIG.get(symbol, {})
                print(f"   {config.get('name', symbol):8s}: ${price_data['price']:<10.2f} ({price_data.get('change_24h', 0):+.2f}%)")
            else:
                print(f"   {symbol}: ⚠️ {price_data['error']}")
        except Exception as e:
            print(f"   {symbol}: ❌ 获取失败 - {e}")

    print("\n📊 正在获取历史数据并运行回测...")
    backtest_results = {}
    for symbol in symbols:
        try:
            history = get_historical_data(symbol, days=60)
            if history and len(history) >= 20:
                result = run_backtest(symbol, "ma_cross", history)
                backtest_results[symbol] = result
                icon = "✅" if result.get("passed") else "⚠️"
                print(f"   {icon} {symbol:12s}: 胜率 {result.get('win_rate', 0):.1f}% | 收益 {result.get('total_return', 0):+.2f}% | 回撤 {result.get('max_drawdown', 0):.1f}%")
            else:
                print(f"   ⚠️ {symbol}: 历史数据不足 ({len(history) if history else 0} 条)，跳过回测")
        except Exception as e:
            print(f"   {symbol}: ❌ 回测失败 - {e}")

    print("\n🌍 正在获取宏观市场环境数据...")
    macro_data = get_macro_data()
    for sym, data in macro_data.items():
        if "error" not in data:
            print(f"   {data['name']:12s}: {data['price']} ({data.get('change_24h', 0):+.2f}%)")
        else:
            print(f"   {data['name']:12s}: ⚠️ {data['error']}")

    # ============================================================
    # 精简版：2 Agent + 代码自动计算
    # Agent 1: 宏观分析师（1 个任务）
    # Agent 2: 交易决策官（1 个任务，一次性处理所有标的）
    # 止损止盈由代码自动计算，不依赖 Agent 输出格式
    # ============================================================

    macro_context = "\n".join(
        f"  {data['name']}: {data.get('price', 'N/A')} ({data.get('change_24h', 0):+.2f}%)"
        for sym, data in macro_data.items() if "error" not in data
    ) if macro_data else "  宏观数据不可用"

    market_context_lines = []
    for s in symbols:
        p = market_data.get(s, {})
        b = backtest_results.get(s, {})
        if p and "error" not in p:
            bt_str = f"回测胜率{b.get('win_rate', 'N/A')}% 收益{b.get('total_return', 'N/A')}%" if b else "回测数据不可用"
            market_context_lines.append(f"  {s}: ${p['price']} ({p.get('change_24h', 0):+.2f}%) | {bt_str}")
    market_context = "\n".join(market_context_lines)

    macro_agent = Agent(
        role="宏观环境分析师",
        goal="分析当前宏观市场环境，判断风险偏好或避险模式",
        backstory="""你是远征军的首席宏观策略师，拥有15年全球宏观经济分析经验。""",
        verbose=True,
        tools=[get_macro_tool(), get_available_symbols_tool()],
        llm=_make_llm("low", 0.3),
    )

    decision_agent = Agent(
        role="交易决策官",
        goal="基于宏观环境和市场数据，直接给出每个标的的交易决策",
        backstory="""你是远征军的交易决策官，拥有20年实战经验。
你擅长快速做出交易决策，不拖泥带水。
你严格遵循风控纪律，止损超过5%的方案直接否决。""",
        verbose=True,
        llm=_make_llm("low", 0.3),
    )

    macro_task = Task(
        description=f"""分析当前宏观市场环境。

宏观数据：
{macro_context}

请执行以下操作：
1. 分析 VIX、DXY、US10Y 的联动关系
2. 判断 Risk-On 还是 Risk-Off 模式
3. 给出交易环境评级

使用 Macro_Environment 工具获取最新的宏观数据。""",
        expected_output="宏观环境分析结论，包含 Risk-On/Risk-Off 判断和交易环境评级",
        agent=macro_agent,
    )

    decision_task = Task(
        description=f"""你是远征军的交易决策官。以下是当前所有可交易标的的实时数据和宏观环境。

宏观环境：
{macro_context}

标的实时数据：
{market_context}

请为每个标的做出交易决策。对于每个标的，必须给出：
1. **方向**：做多 / 做空 / 观望
2. **入场价**：必须接近当前实时价格（偏差不超过 2%）
3. **止损价**：具体 USDT 价格，止损占比不得超过 5%
4. **止盈价**：具体 USDT 价格
5. **决策理由**：一句话说明

=== 重要格式要求 ===
在报告末尾，必须严格按照以下格式输出机器可解析的数据块（不要有逗号分隔千位数）：
【执行数据】
BTC/USDT | 方向: 做空 | 入场: 78000 | 止损: 79500 | 止盈: 76100
ETH/USDT | 方向: 观望 | 入场: 0 | 止损: 0 | 止盈: 0
...（其他标的类似）
【执行数据结束】

注意：如果某个标的决定"观望"，方向填"观望"，入场/止损/止盈填 0。""",
        expected_output="""每个标的的交易决策，包含方向、入场价、止损价、止盈价。
末尾必须包含【执行数据】块。""",
        agent=decision_agent,
    )

    all_tasks = [macro_task, decision_task]

    crew = Crew(
        agents=[macro_agent, decision_agent],
        tasks=all_tasks,
        process=Process.sequential,
        verbose=True,
        max_rpm=30,
    )
    print("\n🔥 精简双Agent快速决策...")
    try:
        raw_output = crew.kickoff()
        if hasattr(raw_output, 'raw'):
            final_output = raw_output.raw
        elif hasattr(raw_output, 'final_output'):
            final_output = raw_output.final_output
        else:
            final_output = str(raw_output)
    except Exception as e:
        import traceback
        print(f"\n   ❌ CrewAI 执行中断: {e}")
        traceback.print_exc()
        final_output = f"金融任务部分完成（行情+回测），Agent 分析跳过"
        print("   已跳过 Agent 分析，保留行情和回测数据")

    print("\n💼 自动执行作战方案 (U本位合约, 智能仓位 + 强制止盈止损)...")

    import re
    trade_plans = {}
    if final_output:
        clean_output = final_output.replace(",", "").replace("，", "")
        exec_block = re.search(r'【执行数据】\s*(.*?)\s*【执行数据结束】', clean_output, re.DOTALL)
        if exec_block:
            block_text = exec_block.group(1)
            for s in symbols:
                line_pat = rf'{re.escape(s)}\s*\|(.+?)(?:\n|$)'
                line_m = re.search(line_pat, block_text, re.IGNORECASE)
                if line_m:
                    line = line_m.group(1)
                    direction_m = re.search(r'方向[:\s]*(\S+)', line)
                    entry_m = re.search(r'入场[:\s]*(\d+\.?\d*)', line)
                    sl_m = re.search(r'止损[:\s]*(\d+\.?\d*)', line)
                    tp_m = re.search(r'止盈[:\s]*(\d+\.?\d*)', line)
                    direction = direction_m.group(1) if direction_m else None
                    sl = float(sl_m.group(1)) if sl_m else None
                    tp = float(tp_m.group(1)) if tp_m else None
                    entry = float(entry_m.group(1)) if entry_m else None
                    if direction and direction.lower() in ("观望", "watch", "skip", "none", "无"):
                        continue
                    if direction and sl and tp and sl > 0 and tp > 0:
                        trade_plans[s] = {"direction": direction, "sl": sl, "tp": tp, "entry": entry}

    # 如果 Agent 没有给出方案，使用代码自动计算
    if not trade_plans:
        print("   ⚠️ Agent 未给出有效交易方案，使用代码自动计算...")
        for symbol in symbols:
            price_data = market_data.get(symbol)
            if price_data and "error" not in price_data:
                price = price_data["price"]
                change = price_data.get("change_24h", 0)
                # 简单策略：跌幅超过 2% 开多，跌幅超过 5% 开空
                if change <= -5:
                    direction = "做空"
                    sl = round(price * 1.03, 2)
                    tp = round(price * 0.95, 2)
                    trade_plans[symbol] = {"direction": direction, "sl": sl, "tp": tp, "entry": price}
                    print(f"   📐 自动决策: {symbol} 跌幅{change:.1f}% > 5% → 做空")
                elif change >= 2:
                    direction = "做多"
                    sl = round(price * 0.97, 2)
                    tp = round(price * 1.05, 2)
                    trade_plans[symbol] = {"direction": direction, "sl": sl, "tp": tp, "entry": price}
                    print(f"   📐 自动决策: {symbol} 涨幅{change:.1f}% > 2% → 做多")
                else:
                    print(f"   ⏭️ 自动决策: {symbol} 涨跌{change:.1f}% 在 -2%~-5% 之间 → 观望")

    executed = 0
    for symbol in symbols:
        try:
            price_data = market_data.get(symbol)
            if price_data and "error" not in price_data:
                price = price_data["price"]
                from core.financial_gateway import create_order, get_mode, calculate_order_quantity
                mode = get_mode()
                calc = calculate_order_quantity(symbol, price)
                if "error" in calc:
                    print(f"   ⚠️ {symbol}: 仓位计算失败 - {calc['error']}")
                    continue
                qty = calc["quantity"]

                plan = trade_plans.get(symbol)

                if plan is None:
                    print(f"   ⏭️ {symbol}: 无作战方案，跳过交易")
                    continue

                sl_price = plan["sl"]
                tp_price = plan["tp"]

                direction = plan.get("direction")
                if direction is None:
                    print(f"   ⏭️ {symbol}: 总参谋长未给出方向，跳过交易")
                    continue

                direction_lower = direction.lower().strip()
                if direction_lower in ("做多", "long", "buy", "多头", "多"):
                    side = "buy"
                    dir_label = "开多"
                elif direction_lower in ("做空", "short", "sell", "空头", "空"):
                    side = "sell"
                    dir_label = "开空"
                else:
                    print(f"   ⏭️ {symbol}: 总参谋长方向 '{direction}' 无法识别，跳过交易")
                    continue

                sl_str = f"止损 ${sl_price:.2f}"
                tp_str = f"止盈 ${tp_price:.2f}"
                print(f"   📐 总参谋长指令: {dir_label} | {sl_str} | {tp_str}")

                order = create_order(symbol, side, "market", qty, price,
                                     stop_loss_price=sl_price, take_profit_price=tp_price)
                if "error" in order:
                    print(f"   ⚠️ {symbol}: {dir_label}失败 - {order['error']}")
                else:
                    pv = calc["position_value"]
                    print(f"   ✅ {symbol}: {dir_label} ${pv:.2f} @ ${order.get('price', price):.2f} "
                          f"(风险 ${calc['risk_amount']:.2f} × {calc['leverage']}x)")
                    executed += 1
        except Exception as e:
            print(f"   ⚠️ {symbol}: 开仓异常 - {e}")

    if executed == 0:
        print("   ℹ️ 无符合条件的标的，全部现金持有")

    try:
        summary = get_portfolio_summary()
        print(f"\n📊 投资组合摘要:")
        print(f"   总权益: ${summary['total_equity']:.2f}")
        print(f"   持仓数: {summary['position_count']}")
        print(f"   浮动盈亏: ${summary['unrealized_pnl']:+.2f}")
    except Exception as e:
        print(f"   ⚠️ 组合摘要获取失败: {e}")

    write_log(session_id, "FINAL_REPORT", "ALL", str(final_output)[:500])
    record_call("金融重击", 0, 0.01)

    report_file = f"chief_log/FINANCIAL_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    os.makedirs("chief_log", exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(str(final_output))
    print(f"\n📁 完整分析报告已保存: {report_file}")

    return final_output


def run_arsenal_mission(session_id: str):
    from arsenal.product_blueprints import PRODUCT_BLUEPRINTS
    from arsenal.code_generator import generate_product

    print("\n🏭 数字兵工厂启动 — 可选产品线:")
    products = list(PRODUCT_BLUEPRINTS.keys())
    for i, name in enumerate(products, 1):
        bp = PRODUCT_BLUEPRINTS[name]
        print(f"  {i}. {name} ({bp['type']}) — {bp['description']}")
    print(f"  {len(products)+1}. 全部生产")

    prod_choice = input("\n🎯 请选择要生产的产品: ").strip()
    try:
        idx = int(prod_choice) - 1
        if idx < len(products):
            selected = [products[idx]]
        else:
            selected = products
    except ValueError:
        selected = [products[0]]

    for product_name in selected:
        print(f"\n🔧 开始生产: {product_name}...")
        generate_product(session_id, product_name, PRODUCT_BLUEPRINTS[product_name])
        print(f"✅ {product_name} 生产完成")
        record_call("数字兵工厂", 0, 0.02)

    return f"兵工厂完成生产: {', '.join(selected)}"


def run_marketing_mission(session_id: str):
    from marketing.content_factory import create_post

    product_name = input("\n📱 输入要推广的产品名称: ").strip() or "默认产品"
    product_desc = input("📝 输入产品描述: ").strip() or "一款实用的工具应用"
    platforms = ["twitter", "reddit", "telegram"]
    languages = ["en", "zh", "id", "ja"]

    print(f"\n🌊 流量宣传军启动 — 目标: {product_name}")
    print(f"   平台: {', '.join(platforms)}")
    print(f"   语言: {', '.join(languages)}")

    for platform in platforms:
        for lang in languages:
            print(f"\n   📝 生成 {platform} ({lang})...")
            create_post(session_id, product_name, product_desc, platform, lang)
            record_call("流量宣传", 0, 0.01)

    return f"流量宣传完成: {product_name} 覆盖 {len(platforms)} 平台 x {len(languages)} 语言"


def run_total_war(session_id: str):
    from arsenal.product_blueprints import PRODUCT_BLUEPRINTS
    from arsenal.code_generator import generate_product
    from marketing.content_factory import create_post

    print("\n🌍 全域总攻启动 — 兵工厂 → 流量推广 全自动流水线")

    platforms = ["twitter", "reddit", "telegram"]
    languages = ["en", "zh", "id", "ja"]

    for product_name, blueprint in PRODUCT_BLUEPRINTS.items():
        print(f"\n{'='*50}")
        print(f"  🔧 阶段1: 生产 {product_name}")
        print(f"{'='*50}")
        generate_product(session_id, product_name, blueprint)
        record_call("全域总攻-兵工厂", 0, 0.02)

        print(f"\n{'='*50}")
        print(f"  🌊 阶段2: 推广 {product_name}")
        print(f"{'='*50}")
        for platform in platforms:
            for lang in languages:
                create_post(session_id, product_name, blueprint["description"], platform, lang)
                record_call("全域总攻-推广", 0, 0.01)

    return "全域总攻完成: 所有产品已生产并推广"


def run_academy_mission(session_id: str):
    from core.academy import scan_battle_logs, analyze_failures, get_academy_status

    print("\n🎓 远征军教导团启动 — 作战复盘与战力优化")

    status = get_academy_status()
    print(f"   历史复盘报告: {status['total_reports']} 份")

    print("\n📋 扫描作战日志中的失败记录...")
    failures = scan_battle_logs()

    if not failures:
        print("   本次无失败记录，全军表现良好！")
        result = "远征军教导团: 无失败记录，无需优化"
    else:
        print(f"   发现 {len(failures)} 条失败/驳回记录")
        for f in failures[:5]:
            print(f"   - [{f['session']}] {f['timestamp']}: {f['content'][:60]}...")

        print("\n📊 正在生成复盘报告...")
        report = analyze_failures(session_id, failures)
        print(f"   报告已保存至 evolution_log/ 目录")
        result = f"远征军教导团: 分析完成，发现 {len(failures)} 条失败记录"

    record_call("远征军教导团", 0, 0.01)
    write_log(session_id, "ACADEMY", "全军复盘", result)
    return result


def run_logistics_mission(session_id: str):
    from core.logistics import get_logistics_status, generate_finance_report, suggest_budget_adjustment

    print("\n🔧 后勤保障处启动 — 财务报告与预算分析")

    status = get_logistics_status()
    print(f"   累计收入: ${status['total_profit']}")
    print(f"   累计支出: ${status['total_cost']}")
    print(f"   净利润: ${status['net_profit']}")

    adj = suggest_budget_adjustment()
    print(f"\n📈 预算建议: {adj['action']}")
    print(f"   建议日预算: ${adj['suggested_budget']}")
    print(f"   理由: {adj['reason']}")

    print("\n📋 生成财务报告...")
    report_file = generate_finance_report(session_id)
    print(f"   报告已保存: {report_file}")

    record_call("后勤保障处", 0, 0.01)
    write_log(session_id, "LOGISTICS", "财务报告", f"净利润 ${status['net_profit']}")
    return f"后勤报告已生成: {report_file}"


def run_campaign_mission(session_id: str):
    from command.campaign import list_templates, create_campaign, get_campaign_status

    print("\n🔄 联合战役编排启动 — 跨部门协同作战计划")

    templates = list_templates()
    print("\n📋 可用战役模板:")
    template_list = list(templates.keys())
    for i, (name, info) in enumerate(templates.items(), 1):
        print(f"  {i}. {name} ({info['phases']} 个阶段) — {info['description']}")

    choice = input("\n🎯 请选择战役模板: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(template_list):
            template_name = template_list[idx]
        else:
            template_name = template_list[0]
    except ValueError:
        template_name = template_list[0]

    target = input("🎯 输入战役目标（可选）: ").strip()

    print(f"\n📝 创建战役计划书...")
    plan_file = create_campaign(session_id, template_name, target)
    print(f"   计划书已生成: {plan_file}")

    record_call("联合战役编排", 0, 0.01)
    write_log(session_id, "CAMPAIGN", template_name, f"战役计划书: {plan_file}")
    return f"战役计划书已生成: {plan_file}"


def run_shadow_test_mission(session_id: str):
    """影子测试 — 在沙箱中验证 Agent 指令"""
    from core.academy import run_shadow_batch, get_academy_status

    print("\n🔬 影子测试系统启动 — 沙箱验证 Agent 指令")

    status = get_academy_status()
    print(f"   历史影子测试: {status['total_shadow_tests']} 次")

    print("\n🎯 选择测试模式:")
    print("   1. 测试所有 Agent（批量）")
    print("   2. 测试指定 Agent")

    op = input("\n请选择: ").strip()
    if op == "2":
        agent = input("Agent 名称 (financial_intel/financial_quant/financial_mp/arsenal_coder/arsenal_qa/marketing_writer): ").strip()
        result = run_shadow_batch(agent)
    else:
        result = run_shadow_batch()

    all_passed = result.get("all_passed", False)
    icon = "✅" if all_passed else "❌"
    print(f"\n{icon} 批量测试结果: {'全部通过' if all_passed else '有未通过项'}")

    for agent_name, agent_result in result.get("results", {}).items():
        if isinstance(agent_result, dict) and "pass_rate" in agent_result:
            rate_icon = "✅" if agent_result["passed"] else "❌"
            print(f"   {rate_icon} {agent_name}: {agent_result['pass_rate']}% ({agent_result['passed_count']}/{agent_result['test_count']})")
        elif isinstance(agent_result, dict) and "error" in agent_result:
            print(f"   ⚠️  {agent_name}: {agent_result['error']}")

    record_call("影子测试", 0, 0)
    write_log(session_id, "SHADOW_TEST", "指令验证", f"影子测试完成: {'全部通过' if all_passed else '有未通过项'}")
    return f"影子测试完成: {'全部通过' if all_passed else '有未通过项'}"


def run_resume_mission(session_id: str):
    """断点恢复 — 扫描并恢复未完成任务"""
    from core.battle_log import get_unfinished_sessions, load_snapshot, get_session_summary

    print("\n🔄 断点恢复系统启动 — 扫描未完成任务")

    unfinished = get_unfinished_sessions()

    if not unfinished:
        print("   ✅ 无未完成任务，系统状态干净")
        return "无未完成任务"

    print(f"\n   📋 发现 {len(unfinished)} 个未完成任务:")
    for i, u in enumerate(unfinished, 1):
        print(f"   {i}. [{u['session_id']}] 最后阶段: {u['last_stage']} @ {u['snapshot_time']}")

    choice = input("\n🔄 是否恢复第一个未完成任务? (y/n): ").strip().lower()
    if choice != "y":
        return "跳过断点恢复"

    target = unfinished[0]
    snapshots = load_snapshot(target["session_id"])
    last_context = snapshots.get(target["last_stage"], {}).get("context", {})

    print(f"\n   🔄 恢复会话: {target['session_id']}")
    print(f"   最后阶段: {target['last_stage']}")
    print(f"   上下文数据: {list(last_context.keys()) if last_context else '无'}")

    print("\n   ✅ 断点恢复完成 — 可继续执行未完成任务")

    record_call("断点恢复", 0, 0)
    write_log(session_id, "RESUME", target["session_id"], f"断点恢复: {target['session_id']} 从 {target['last_stage']} 恢复")
    return f"断点恢复完成: {target['session_id']}"


def run_market_data_mission(session_id: str):
    """行情数据引擎 — 获取实时市场数据"""
    from core.market_data import get_price, get_all_prices, get_historical_data, SYMBOL_CONFIG, get_market_status

    print("\n📡 行情数据引擎启动 — 实时市场数据")

    status = get_market_status()
    print(f"   监控标的: {', '.join(status['symbols'])}")
    print(f"   缓存有效期: {status['cache_duration_seconds']} 秒")

    print("\n📡 正在获取所有标的实时价格...")
    prices = get_all_prices()

    print(f"\n{'='*50}")
    print("  实时行情")
    print(f"{'='*50}")
    for symbol, data in prices.items():
        if "error" not in data:
            config = SYMBOL_CONFIG.get(symbol, {})
            change = data.get("change_24h", 0)
            arrow = "🟢" if change >= 0 else "🔴"
            print(f"  {config.get('name', symbol)} ({symbol})")
            print(f"    价格: ${data['price']}")
            print(f"    24h: {arrow} {change:+.2f}%")
            print(f"    来源: {data.get('source', 'N/A')}")
        else:
            print(f"  {symbol}: ⚠️ {data['error']}")

    print(f"\n{'='*50}")
    print("  历史数据 (近 30 日)")
    print(f"{'='*50}")
    for symbol in status["symbols"]:
        history = get_historical_data(symbol, days=30)
        if history:
            closes = [c["close"] for c in history]
            print(f"  {symbol}: {len(history)} 条 | 最高 ${max(closes):.2f} | 最低 ${min(closes):.2f} | 最新 ${closes[-1]:.2f}")
        else:
            print(f"  {symbol}: 历史数据不可用")

    record_call("行情数据", 0, 0)
    write_log(session_id, "MARKET_DATA", "行情", f"获取 {len(prices)} 个标的实时数据")
    return "行情数据已获取"


def run_backtest_mission(session_id: str):
    """策略回测 — 用历史数据验证交易策略"""
    from core.market_data import get_historical_data, SYMBOL_CONFIG
    from core.backtester import run_backtest, get_available_strategies, get_backtest_status
    import json

    print("\n📊 策略回测系统启动 — 历史数据验证策略")

    strategies = get_available_strategies()
    print("\n📋 可用策略:")
    strategy_list = list(strategies.keys())
    for i, (name, info) in enumerate(strategies.items(), 1):
        print(f"  {i}. {info['name']} — {info['description']}")

    strat_choice = input("\n🎯 选择策略: ").strip()
    try:
        idx = int(strat_choice) - 1
        strategy = strategy_list[idx] if 0 <= idx < len(strategy_list) else strategy_list[0]
    except ValueError:
        strategy = strategy_list[0]

    print(f"\n📋 可选标的:")
    symbols = list(SYMBOL_CONFIG.keys())
    for i, s in enumerate(symbols, 1):
        config = SYMBOL_CONFIG.get(s, {})
        print(f"  {i}. {config.get('name', s)} ({s})")

    sym_choice = input("\n🎯 选择标的: ").strip()
    try:
        idx = int(sym_choice) - 1
        symbol = symbols[idx] if 0 <= idx < len(symbols) else symbols[0]
    except ValueError:
        symbol = symbols[0]

    days = input("📅 回测天数 (默认 30): ").strip()
    try:
        days = int(days) if days else 30
    except ValueError:
        days = 30

    print(f"\n📥 正在获取 {symbol} 近 {days} 日历史数据...")
    history = get_historical_data(symbol, days=days)

    if not history:
        print(f"   ❌ 无法获取 {symbol} 历史数据")
        return f"回测失败: {symbol} 历史数据不可用"

    print(f"   ✅ 获取到 {len(history)} 条 K 线数据")
    print(f"\n⚙️  运行 {strategies[strategy]['name']} 回测...")

    result = run_backtest(symbol, strategy, history)

    if "error" in result:
        print(f"   ❌ 回测失败: {result['error']}")
        return f"回测失败: {result['error']}"

    print(f"\n{'='*50}")
    print(f"  回测结果: {symbol} | {strategies[strategy]['name']}")
    print(f"{'='*50}")
    print(f"  总收益率: {result['total_return']:+.2f}%")
    print(f"  胜率: {result['win_rate']:.1f}%")
    print(f"  总交易次数: {result['total_trades']}")
    print(f"  盈利次数: {result['wins']}")
    print(f"  亏损次数: {result['losses']}")
    print(f"  平均盈利: {result['avg_win']:+.2f}%")
    print(f"  平均亏损: {result['avg_loss']:.2f}%")
    print(f"  最大回撤: {result['max_drawdown']:.2f}%")
    print(f"  盈亏比: {result['profit_factor']}")
    verdict = "✅ 回测通过" if result.get("passed") else "❌ 回测未通过"
    print(f"  裁决: {verdict}")

    record_call("策略回测", 0, 0)
    write_log(session_id, "BACKTEST", symbol, json.dumps({
        "strategy": strategy, "win_rate": result["win_rate"], "passed": result["passed"],
    }, ensure_ascii=False))
    return f"回测完成: {symbol} {strategies[strategy]['name']} 胜率 {result['win_rate']}%"


def run_portfolio_mission(session_id: str):
    """投资组合 — 查看虚拟仓位与盈亏"""
    from core.portfolio import get_portfolio_summary, get_portfolio_status

    print("\n💼 投资组合管理启动 — 虚拟仓位与盈亏")

    summary = get_portfolio_summary()

    print(f"\n{'='*50}")
    print(f"  投资组合摘要")
    print(f"{'='*50}")
    print(f"  总权益: ${summary['total_equity']:.2f}")
    print(f"  现金: ${summary['cash']:.2f}")
    print(f"  持仓市值: ${summary['position_value']:.2f}")
    print(f"  浮动盈亏: ${summary['unrealized_pnl']:+.2f}")
    print(f"  已实现盈亏: ${summary['realized_pnl']:+.2f}")
    print(f"  总盈亏: ${summary['total_pnl']:+.2f}")
    print(f"  总交易次数: {summary['total_trades']}")

    if summary["positions"]:
        print(f"\n{'='*50}")
        print(f"  当前持仓")
        print(f"{'='*50}")
        for pos in summary["positions"]:
            direction_icon = "🟢" if pos["direction"] == "long" else "🔴"
            pnl_icon = "🟢" if pos["unrealized_pnl"] >= 0 else "🔴"
            print(f"  {direction_icon} {pos['symbol']} ({pos['direction']})")
            print(f"     数量: {pos['quantity']}")
            print(f"     成本: ${pos['entry_price']:.2f}")
            print(f"     现价: ${pos['current_price']:.2f}")
            print(f"     盈亏: {pnl_icon} ${pos['unrealized_pnl']:+.2f} ({pos['unrealized_pnl_pct']:+.2f}%)")
    else:
        print(f"\n   📭 无持仓")

    if summary["recent_orders"]:
        print(f"\n{'='*50}")
        print(f"  最近交易")
        print(f"{'='*50}")
        for order in summary["recent_orders"][-5:]:
            print(f"  [{order['time'][:19]}] {order['type']} {order['symbol']} @ ${order['price']}")

    record_call("投资组合", 0, 0)
    write_log(session_id, "PORTFOLIO", "查看", f"总权益 ${summary['total_equity']:.2f}, 持仓 {summary['position_count']} 个")
    return f"投资组合查看完成: 总权益 ${summary['total_equity']:.2f}"


def run_chief_of_staff_mission(session_id: str):
    """👑 AI 总参谋长 — 一句话命令，自动协调各部门"""
    from command.chief_of_staff import execute_command, list_departments, list_task_templates

    print("\n" + "=" * 60)
    print("  👑 AI 总参谋长 (Chief of Staff) 启动")
    print("  " + "=" * 60)
    print("  你可以说一句话命令，总参谋长会自动拆解并协调各部门执行。")
    print()
    print("  📋 示例命令:")
    print('    "分析黄金行情"')
    print('    "生产一个外汇计算器并推广到东南亚"')
    print('    "检查全系统状态"')
    print('    "把最近的失败经验沉淀到知识库"')
    print()

    depts = list_departments()
    print(f"  🏛️  可调用的部门 ({len(depts)} 个):")
    for name, info in depts.items():
        print(f"     - {name}: {info['description']}")
    print()

    templates = list_task_templates()
    print(f"  📋 可匹配的任务模板 ({len(templates)} 个):")
    for name, info in templates.items():
        print(f"     - {name}: {info['description']} ({info['steps']} 个阶段)")
    print()

    command = input("🎯 总司令，请下达命令: ").strip()
    if not command:
        print("   ⚠️  命令不能为空，返回主菜单")
        return "总参谋长: 命令为空"

    print(f"\n  👑 总参谋长正在理解命令...")
    report_file = execute_command(session_id, command)

    record_call("总参谋长", 0, 0.01)
    write_log(session_id, "CHIEF_OF_STAFF", command, f"总参谋长执行完成: {report_file}")
    return f"总参谋长执行完成: {report_file}"


def run_scheduler_mission(session_id: str):
    """⏰ 定时调度器 — 自动循环执行金融任务"""
    from core.scheduler import start, stop, get_status, run_once

    print("\n" + "=" * 60)
    print("  ⏰ 定时调度器")
    print("=" * 60)
    print()
    print("  1. 启动定时调度器（每 4 小时自动执行一轮）")
    print("  2. 立即执行一轮")
    print("  3. 查看调度器状态")
    print("  4. 停止调度器")
    print("  0. 返回主菜单")
    print()

    choice = input("🎯 请选择: ").strip()

    if choice == "1":
        start()
        print("\n⏰ 调度器已在后台运行，你可以返回主菜单做其他操作")
        print("   调度器会自动循环执行，无需干预")
    elif choice == "2":
        print("\n⏰ 立即执行一轮...")
        run_once()
    elif choice == "3":
        status = get_status()
        print(f"\n  运行中: {'✅ 是' if status['active'] else '❌ 否'}")
        print(f"  当前周期: {status['current_cycle']}")
        print(f"  上次执行: {status['last_run'] or '无'}")
        print(f"  下次执行: {status['next_run'] or '无'}")
        print(f"  正在执行: {'✅ 是' if status['is_executing'] else '❌ 否'}")
        print(f"  扫描标的: {status['tradable_symbols']} 个")
    elif choice == "4":
        stop()
    else:
        print("  返回主菜单")

    record_call("定时调度器", 0, 0)
    write_log(session_id, "SCHEDULER", choice, "调度器操作完成")
    return "调度器操作完成"
