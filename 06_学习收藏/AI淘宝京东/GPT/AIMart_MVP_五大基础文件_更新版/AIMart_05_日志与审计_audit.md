# AIMart 日志与审计文件（更新版）

## 新增审计事件
event_categories:
  agent_maturity:
    description: "AI Agent 成熟度检查事件"
    events:
      - "agent.maturity_check_passed"
      - "agent.maturity_check_failed"

  cross_border_compliance:
    description: "跨境数据访问与合规事件"
    events:
      - "cross_border_data_access_blocked"

  compute_financial:
    description: "算力金融化交易受限事件"
    events:
      - "compute_derivative_attempt_blocked"
