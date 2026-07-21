# AIMart 配置文件（更新版）

agent_maturity:
  production_ready_only: true
  sandbox_for_new_agents: true

payment_protocols:
  enabled_protocols:
    - x402
    - ACP
    - SPT
  default_protocol: x402

compliance:
  gdpr_enabled: true
  pipl_enabled: true
  local_storage_required: true
