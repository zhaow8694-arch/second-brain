# AIMart 边界文件：参与者、角色、权限、业务领域
tags: [aimart, boundary, scope]

tags: [aimart, boundary, scope]
> 版本：v1.0 | 2026-06-07 | 状态：设计阶段
tags: [aimart, boundary, scope]

tags: [aimart, boundary, scope]
---
tags: [aimart, boundary, scope]

## 一、参与者定义

AIMart 生态中存在 7 类参与者，每类参与者的动机、行为模式和系统交互方式各不相同。

### 1.1 参与者总览

| ID | 参与者 | 定义 | 核心动机 | 是否为系统内主体 |
|----|--------|------|---------|----------------|
| P-01 | Agent Owner | Agent 的所有者（人类或组织），为 Agent 提供预算和策略 | 让 Agent 高效完成任务，控制成本 | 是 |
| P-02 | AI Agent | 自主执行任务的 AI 系统，是市场的主要买家 | 获取能力以完成任务 | 是（核心） |
| P-03 | Capability Provider | 能力商品卖家，提供模型/技能/专家/算力 | 出售能力获取收入 | 是 |
| P-04 | Platform Operator | AIMart 平台运营方 | 收取佣金和增值服务费 | 是 |
| P-05 | Certifier | 第三方认证机构，验证能力商品质量 | 提供认证服务获取认证费 | 是 |
| P-06 | Facilitator | 支付结算中间方（x402 架构角色），验证支付并代理链上结算 | 收取结算服务费 | 是 |
| P-07 | Regulator | 监管机构，监督市场合规运营 | 维护市场秩序和消费者权益 | 否（外部） |

### 1.2 参与者详细定义

#### P-01 Agent Owner（Agent 所有者）

```
唯一标识：owner_id (string, UUID)
属性：
  - name: 组织/个人名称
  - type: individual | enterprise | government
  - kyc_status: pending | verified | rejected
  - jurisdiction: 法域（CN/US/EU/...）
  - budget_pools: 关联的预算池列表
  - agents: 关联的 Agent 列表
  - created_at: 注册时间
  - risk_level: low | medium | high

行为边界：
  ✓ 创建和管理 Agent
  ✓ 设定预算池和消费策略
  ✓ 审批/拒绝 Agent 的大额交易请求
  ✓ 查看 Agent 的交易历史和效果报告
  ✓ 暂停/终止 Agent 的交易权限
  ✗ 代替 Agent 做购买决策（Agent 自主决策）
  ✗ 修改已完成的交易记录

约束：
  - 一个 Owner 可以拥有多个 Agent
  - Owner 对其 Agent 的所有交易承担法律责任
  - Owner 的 KYC 状态影响其 Agent 的交易权限上限
```

#### P-02 AI Agent（AI 代理）

```
唯一标识：agent_id (string, UUID)
属性：
  - name: Agent 名称
  - owner_id: 所属 Owner
  - framework: langchain | crewai | autogen | dify | coze | custom
  - capability_scope: Agent 当前已具备的能力范围
  - trust_score: 动态信任评分 (0-100)
  - spending_authority: 当前消费授权级别
  - status: active | suspended | terminated
  - created_at: 创建时间
  - last_active_at: 最后活跃时间

行为边界：
  ✓ 在预算池范围内自主搜索和购买能力
  ✓ 试用沙箱中的能力商品
  ✓ 回传使用效果评价（结构化数据）
  ✓ 通过 A2A 与其他 Agent 协商
  ✓ 在授权范围内自主完成微支付
  ✗ 超出预算池总额消费
  ✗ 绕过分层授权机制（越权交易）
  ✗ 修改自身 trust_score
  ✗ 访问其他 Agent 的私有上下文数据
  ✗ 执行未经验证的技能代码（非沙箱）

约束：
  - Agent 不具有法律主体地位，交易法律效果归属于 Owner
  - Agent 的所有交易行为必须可追溯至 Owner
  - Agent 的 trust_score 由平台基于历史行为动态计算，不可篡改
  - Agent 被暂停后，所有进行中的交易进入冻结状态
```

#### P-03 Capability Provider（能力提供方）

```
唯一标识：provider_id (string, UUID)
属性：
  - name: 提供方名称
  - type: individual | enterprise | research_org | open_source_community
  - kyc_status: pending | verified | rejected
  - jurisdiction: 法域
  - listing_count: 上架商品数
  - overall_rating: 综合评分 (0-5)
  - certification_status: uncertified | certified | premium_certified
  - dispute_count: 争议次数
  - created_at: 注册时间

行为边界：
  ✓ 上架能力商品（需通过平台验证）
  ✓ 设定商品定价和 SLA
  ✓ 更新商品版本（需重新验证）
  ✓ 查看商品的使用统计和评价
  ✓ 响应买方的协商请求（通过 A2A）
  ✗ 虚假声明商品能力
  ✗ 收集买方 Agent 的上下文数据（未经授权）
  ✗ 对评价数据进行刷分操作
  ✗ 在未通知的情况下下架有活跃订阅的商品

约束：
  - 上架商品必须提供基准测试结果
  - 商品能力声明与实际表现的偏差超过阈值时自动降级
  - 连续 N 次评价不达标的商品自动下架
  - 提供方需缴纳保证金（金额与商品定价等级挂钩）
```

#### P-04 Platform Operator（平台运营方）

```
唯一标识：platform_id (string, 固定为 "aimart-core")
属性：
  - version: 平台当前版本
  - protocol_versions: 各协议支持的版本
  - fee_schedule: 佣金费率表
  - feature_flags: 特性开关状态

行为边界：
  ✓ 管理平台规则和费率
  ✓ 审核上架商品
  ✓ 仲裁交易争议
  ✓ 暂停/封禁违规参与者
  ✓ 更新协议适配层
  ✗ 修改 Agent 的自主决策结果
  ✗ 动用买卖双方的冻结资金
  ✗ 在未授权情况下访问参与者私有数据
  ✗ 单方面修改已签订的 SLA

约束：
  - 平台规则变更需提前 30 天通知所有参与者
  - 佣金费率变更需提前 60 天通知
  - 争议仲裁需在 7 个工作日内给出裁决
  - 平台操作日志对所有参与者可审计
```

#### P-05 Certifier（认证机构）

```
唯一标识：certifier_id (string, UUID)
属性：
  - name: 机构名称
  - accreditation: 认可范围（model | skill | expert | compute）
  - authority_level: platform_certified | industry_certified | government_certified
  - certification_count: 已认证商品数

行为边界：
  ✓ 对商品进行独立基准测试
  ✓ 签发认证证书（含有效期）
  ✓ 撤销认证（当商品表现不达标时）
  ✗ 修改卖家的商品代码或模型权重
  ✗ 访问买方的交易数据

约束：
  - 认证结果必须公开可查
  - 认证有效期不超过 6 个月，到期需重新认证
  - 认证机构自身需通过平台或行业资质审核
```

#### P-06 Facilitator（支付结算中间方）

```
唯一标识：facilitator_id (string, UUID)
属性：
  - name: 机构名称
  - protocol: x402 | acp | ap2 | mpp
  - supported_chains: 支持的区块链网络
  - fee_rate: 结算费率
  - uptime_sla: 可用性承诺

行为边界：
  ✓ 验证支付凭证签名
  ✓ 代理客户端完成链上结算
  ✓ 返回交易哈希给服务端
  ✗ 拒绝合法的支付请求
  ✗ 延迟结算超过 SLA 承诺时间
  ✗ 访问交易的业务内容数据

约束：
  - 结算延迟不得超过 5 秒（x402 微支付场景）
  - Facilitator 不得持有客户资金超过结算周期
  - 需维持 99.9% 以上的可用性
```

---

## 二、角色与权限矩阵

### 2.1 资源权限矩阵

| 资源 \ 角色 | Agent Owner | AI Agent | Provider | Platform | Certifier | Facilitator |
|-------------|:-----------:|:--------:|:--------:|:--------:|:---------:|:-----------:|
| 预算池 | CRUD | R(受限) | — | R(审计) | — | — |
| Agent 配置 | CRUD | R(自身) | — | R(审计) | — | — |
| Agent 行为日志 | R | R(自身) | — | R | — | — |
| 商品列表 | R | R+Search | CRUD(自身) | R+审核 | R | — |
| 商品详情 | R | R | R(自身) | R | R | — |
| AgentCard | R | R | RW(自身) | R+验证 | RW(认证) | — |
| 交易订单 | R(所属Agent) | RW(自身) | R(自身) | R+仲裁 | — | R(结算) |
| 评价数据 | R | RW(回传) | R(自身) | R+审计 | R | — |
| 沙箱环境 | R | RW | RW(自身) | 管理 | R | — |
| 认证证书 | R | R | R(自身) | R | RW | — |
| 结算记录 | R | R(自身) | R(自身) | R | — | R+验证 |
| 平台规则 | R | R | R | CRUD | R | R |

> R = 读取, W = 写入, C = 创建, U = 更新, D = 删除, Search = 搜索, CRUD = 全部权限

### 2.2 操作权限矩阵

| 操作 | Agent Owner | AI Agent | Provider | Platform | Certifier |
|------|:-----------:|:--------:|:--------:|:--------:|:---------:|
| 搜索能力商品 | — | ✓ | — | — | — |
| 试用能力商品 | — | ✓ | — | — | — |
| 购买能力商品（微额） | 设置策略 | ✓ | — | — | — |
| 购买能力商品（小额） | 收到通知 | ✓ | — | — | — |
| 购买能力商品（大额） | 审批 | 申请 | — | — | — |
| 上架能力商品 | — | — | ✓ | 审核 | — |
| 下架能力商品 | — | — | ✓ | 审核 | — |
| 回传使用效果 | — | ✓ | — | — | — |
| 发起争议 | ✓ | ✓ | ✓ | 仲裁 | — |
| 认证商品 | — | — | — | — | ✓ |
| 暂停参与者 | — | — | — | ✓ | — |
| 修改平台规则 | — | — | — | ✓ | — |
| 调整 Agent 预算 | ✓ | — | — | — | — |
| 暂停 Agent 交易 | ✓ | — | — | ✓ | — |

---

## 三、业务领域定义

### 3.1 领域划分

AIMart 的业务领域划分为 5 个核心域 + 2 个支撑域：

```
┌──────────────────────────────────────────────┐
│                 AIMart 业务领域                │
├──────────────────────────────────────────────┤
│                                              │
│  核心域：                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ 商品域    │ │ 交易域    │ │ 支付域    │      │
│  │ Catalog  │ │ Exchange │ │ Payment  │      │
│  └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐ ┌──────────┐                    │
│  │ 信任域    │ │ 搜索域    │                    │
│  │ Trust    │ │ Search   │                    │
│  └──────────┘ └──────────┘                    │
│                                              │
│  支撑域：                                     │
│  ┌──────────┐ ┌──────────┐                    │
│  │ 身份域    │ │ 审计域    │                    │
│  │ Identity │ │ Audit    │                    │
│  └──────────┘ └──────────┘                    │
│                                              │
└──────────────────────────────────────────────┘
```

### 3.2 领域详细定义

#### 商品域（Catalog Domain）

```
领域 ID：D-CATALOG
职责：管理四类能力商品的全生命周期

核心实体：
  - CapabilityItem：能力商品（模型/技能/专家/算力）
  - AgentCard：机器可读的能力声明（详见能力文件）
  - CapabilityVersion：商品版本
  - PricingPlan：定价方案

子领域：
  D-CATALOG-MODEL：模型商品管理
  D-CATALOG-SKILL：技能商品管理
  D-CATALOG-EXPERT：专家商品管理
  D-CATALOG-COMPUTE：算力商品管理

边界：
  - 入口：Provider 上架 / 平台审核 / 版本更新 / 下架
  - 出口：搜索域查询 / 交易域引用 / 信任域评价
  - 不涉及：支付流程 / Agent 决策逻辑
```

#### 交易域（Exchange Domain）

```
领域 ID：D-EXCHANGE
职责：管理能力商品的搜索、匹配、试用、购买、交付全流程

核心实体：
  - SearchQuery：搜索请求（Agent 发起）
  - SearchResult：搜索结果（含匹配度排序）
  - TrialSession：试用会话
  - Order：交易订单
  - Delivery：能力交付记录

状态机（Order）：
  created → matched → authorized → paid → delivering → completed
                                                      → disputed → arbitrated
         → rejected
         → expired

边界：
  - 入口：Agent 发起搜索 / Agent 确认购买 / Agent 回传效果
  - 出口：支付域发起结算 / 信任域更新评分 / 审计域记录日志
  - 不涉及：预算管理 / 商品上架
```

#### 支付域（Payment Domain）

```
领域 ID：D-PAYMENT
职责：管理预算、授权、结算、担保交易全流程

核心实体：
  - BudgetPool：预算池
  - SpendingPolicy：消费策略
  - Authorization：消费授权
  - Transaction：支付交易
  - EscrowAccount：担保账户

子领域：
  D-PAYMENT-BUDGET：预算管理
  D-PAYMENT-AUTH：授权管理
  D-PAYMENT-SETTLE：结算执行（x402/ACP/AP2/MPP）
  D-PAYMENT-ESCROW：担保交易

边界：
  - 入口：交易域发起支付请求 / Owner 充值预算 / Owner 调整策略
  - 出口：交易域返回支付结果 / 审计域记录结算日志
  - 不涉及：商品搜索 / 效果评价
```

#### 信任域（Trust Domain）

```
领域 ID：D-TRUST
职责：管理动态信任评分、效果回传、评价、争议处理

核心实体：
  - TrustScore：动态信任评分
  - EffectReport：效果回传报告
  - Review：评价记录
  - Dispute：争议工单
  - Arbitration：仲裁结果

信任评分来源（权重）：
  - 基准测试结果（30%）
  - 实际使用效果回传（50%）
  - Agent 间口碑传播（15%）
  - 认证机构背书（5%）

评分更新频率：实时（每次效果回传触发增量更新）

边界：
  - 入口：Agent 回传效果 / Agent 提交争议 / 认证结果更新
  - 出口：搜索域排序参考 / 交易域授权参考 / 商品域上下架触发
  - 不涉及：支付金额 / 搜索匹配算法
```

#### 搜索域（Search Domain）

```
领域 ID：D-SEARCH
职责：处理 Agent 的能力需求描述，返回匹配的能力商品列表

核心实体：
  - CapabilityQuery：结构化能力需求描述
  - MatchResult：匹配结果（含匹配度、排序、推荐理由）
  - SearchIndex：搜索索引

搜索输入格式（JSON）：
  {
    "task_description": "审查中文法律合同的合规性",
    "required_capabilities": ["legal", "contract_review", "chinese"],
    "performance_constraints": {
      "latency_ms": 2000,
      "accuracy_min": 0.85
    },
    "cost_constraints": {
      "max_per_call": 0.01,
      "currency": "CNY"
    },
    "preferred_delivery": "api_call",
    "trust_score_min": 60
  }

匹配算法：
  - 硬过滤：性能约束、成本约束、信任评分阈值
  - 软排序：匹配度评分（能力+性能+成本+信任的加权综合）

边界：
  - 入口：Agent 提交搜索请求
  - 出口：交易域创建订单 / 信任域参考评分
  - 不涉及：支付 / 效果评价
```

#### 身份域（Identity Domain）

```
领域 ID：D-IDENTITY
职责：管理所有参与者的身份认证、密钥管理、访问控制

核心实体：
  - Identity：参与者身份
  - Credential：认证凭证（API Key / OAuth2 Token / mTLS Certificate）
  - AccessPolicy：访问控制策略
  - AuditLog：身份操作日志

边界：
  - 入口：参与者注册 / 登录 / 密钥轮换 / 权限变更
  - 出口：所有域的身份验证和授权检查
  - 不涉及：业务逻辑
```

#### 审计域（Audit Domain）

```
领域 ID：D-AUDIT
职责：记录和存储所有操作的审计日志，确保可追溯

核心实体：
  - AuditEntry：审计条目（详见日志与审计文件）

边界：
  - 入口：所有域的操作事件
  - 出口：合规报告 / 争议证据 / 监管查询
  - 不涉及：业务逻辑修改
```

---

## 四、参与者-领域交互边界

### 4.1 交互矩阵

| 参与者 \ 领域 | 商品域 | 交易域 | 支付域 | 信任域 | 搜索域 | 身份域 | 审计域 |
|-------------|:------:|:------:|:------:|:------:|:------:|:------:|:------:|
| Agent Owner | R | R(所属) | CRUD | R | — | CRUD | R(所属) |
| AI Agent | R | RW | R(受限) | RW | RW | R(自身) | — |
| Provider | CRUD(自身) | R(自身) | R(自身) | R(自身) | — | CRUD(自身) | R(自身) |
| Platform | 全部 | 全部 | R+仲裁 | 全部 | R | 全部 | 全部 |
| Certifier | RW(认证) | — | — | RW | — | R | R |
| Facilitator | — | R(结算) | RW(结算) | — | — | R | R |

### 4.2 跨域交互规则

1. **商品域 → 搜索域**：商品上架/更新时，自动同步到搜索索引；下架时自动从索引移除
2. **搜索域 → 交易域**：Agent 基于搜索结果发起购买，搜索结果作为订单的匹配依据
3. **交易域 → 支付域**：订单创建后触发支付请求，支付结果决定订单状态流转
4. **交易域 → 信任域**：交易完成后 Agent 回传效果，触发信任评分更新
5. **信任域 → 搜索域**：信任评分变化影响搜索排序权重
6. **信任域 → 商品域**：信任评分低于阈值时自动触发商品下架
7. **支付域 → 审计域**：所有结算操作必须写入审计日志
8. **身份域 → 所有域**：所有操作必须经过身份验证和授权检查

### 4.3 禁止的交互

1. Agent **不可**直接修改预算池（只有 Owner 可以）
2. Provider **不可**直接修改评价数据（只有 Agent 回传和平台仲裁可以）
3. Facilitator **不可**访问业务内容数据（只能看到结算相关信息）
4. 任何参与者 **不可**跨过身份域直接操作其他域
5. Agent **不可**在未搜索匹配的情况下直接创建订单（必须经过搜索域）
