MENU_OPTIONS = {
    "1": {
        "label": "金融重击 — 多标的交易策略分析",
        "module": "operations",
        "function": "run_financial_mission",
    },
    "2": {
        "label": "数字兵工厂 — AI 批量生产小程序/小游戏",
        "module": "operations",
        "function": "run_arsenal_mission",
    },
    "3": {
        "label": "流量宣传 — 多语言推广内容生成",
        "module": "operations",
        "function": "run_marketing_mission",
    },
    "4": {
        "label": "全域总攻 — 兵工厂生产 → 流量推广 全自动流水线",
        "module": "operations",
        "function": "run_total_war",
    },
    "5": {
        "label": "远征军教导团 — AI 复盘失败记录，优化全军战力",
        "module": "operations",
        "function": "run_academy_mission",
    },
    "6": {
        "label": "后勤保障处 — 财务报告与预算建议",
        "module": "operations",
        "function": "run_logistics_mission",
    },
    "7": {
        "label": "联合战役编排 — 创建跨部门协同作战计划",
        "module": "operations",
        "function": "run_campaign_mission",
    },
    "8": {
        "label": "⚡ 战役自动执行 — 按模板自动调用各部门作战",
        "module": "operations",
        "function": "run_campaign_execute_mission",
    },
    "9": {
        "label": "📊 全军战力看板 — 实时显示各部门 KPI",
        "module": "operations",
        "function": "run_dashboard_mission",
    },
    "10": {
        "label": "🎭 影子特工处 — 数字身份管理与指纹模拟",
        "module": "operations",
        "function": "run_identity_mission",
    },
    "11": {
        "label": "🐕 物理防火墙 (Guard Dog) — 系统安全巡逻",
        "module": "operations",
        "function": "run_guard_dog_mission",
    },
    "12": {
        "label": "📚 中央知识库 (RAG) — 知识管理与检索",
        "module": "operations",
        "function": "run_rag_mission",
    },
    "13": {
        "label": "🔬 影子测试 — 沙箱验证 Agent 指令（进化红线）",
        "module": "operations",
        "function": "run_shadow_test_mission",
    },
    "14": {
        "label": "🔄 断点恢复 — 扫描并恢复未完成任务",
        "module": "operations",
        "function": "run_resume_mission",
    },
    "15": {
        "label": "📡 行情数据引擎 — 获取实时市场数据与历史 K 线",
        "module": "operations",
        "function": "run_market_data_mission",
    },
    "16": {
        "label": "📊 策略回测 — 用历史数据验证交易策略",
        "module": "operations",
        "function": "run_backtest_mission",
    },
    "17": {
        "label": "💼 投资组合 — 查看虚拟仓位与盈亏",
        "module": "operations",
        "function": "run_portfolio_mission",
    },
    "18": {
        "label": "👑 AI 总参谋长 — 一句话命令，自动协调各部门",
        "module": "operations",
        "function": "run_chief_of_staff_mission",
    },
    "19": {
        "label": "⏰ 定时调度器 — 自动循环执行金融任务",
        "module": "operations",
        "function": "run_scheduler_mission",
    },
}


def show_menu():
    print("\n" + "=" * 60)
    print("  📋 统帅部作战选项:")
    for key, opt in MENU_OPTIONS.items():
        print(f"  {key:>2}. {opt['label']}")
    print("=" * 60)


def get_choice() -> str:
    return input("\n🎯 总司令，请选择作战任务 (1-19): ").strip()
