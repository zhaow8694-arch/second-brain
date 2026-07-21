# AIMart 约束文件（更新版）：交易、预算、风险、安全、SLA

## Agent 成熟度约束
agent_maturity_constraints:
  production_ready_only: true
  allowed_capabilities:
    - low
    - medium
  max_concurrent_execution: 5
  sandbox_required_for_new_agents: true

## 跨境数据合规
cross_border_data_handling:
  allow_cross_border: false
  region_storage_required: true
  gdpr_compliance: true
  pipl_compliance: true

## 算力金融化
compute_derivatives:
  allow_trading: false
  require_financial_license: true
