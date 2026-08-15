# 中亚短剧平台 — 全自动开发规格书（BUILD）

> **文档类型**：AI Agent 唯一执行源（Single Source of Truth）  
> **版本**：BUILD-1.3
> **日期**：2026-07-07  
> **目标**：无需人工审核，Agent 读取本文档后**全程自动实现**，交付可运行的最终产品（MVP + 商用核心功能）  
> **执行者**：Grok / GPT Codex / 任意 Coding Agent  
> **产品代号**：`Korotko`（哈萨克语「Қысқа」= 简短；品牌名保留 Korotko）  
> **工作目录**：**由用户指定，本文档不写死路径**（见 §0.4）

---

## §0 执行契约（Agent 必须遵守）

### 0.1 自动化原则

```
┌─────────────────────────────────────────────────────────────┐
│  禁止行为                                                    │
│  ✗ 向用户询问确认、选型、审核                                 │
│  ✗ 因缺少 API Key 而停止（使用 Mock 适配器继续）              │
│  ✗ 输出「建议你运行」而不亲自执行                             │
│  ✗ 跳过测试或构建验证                                        │
│  ✗ 留 TODO/FIXME 作为终态交付                                │
├─────────────────────────────────────────────────────────────┤
│  必须行为                                                    │
│  ✓ 按 §8 阶段顺序执行，每阶段结束运行 §9 验证清单             │
│  ✓ 遇到歧义采用 §2 锁定默认值                                 │
│  ✓ 测试失败则自动修复，最多重试 5 轮后继续下一阶段              │
│  ✓ 每阶段完成后 git commit（若目录是 git repo）               │
│  ✓ 终态交付 §10 全部 Done 条件                                │
└─────────────────────────────────────────────────────────────┘
```

### 0.2 执行命令

用户触发语（任一即可启动）：

- `执行 BUILD 规格书`
- `/execute-plan E:\知识库\02_市场分析\短剧出海\中亚短剧平台_全自动开发规格书_BUILD.md`
- `按 BUILD.md 全自动完成 Korotko App`

Agent 收到后：**不得回复「是否开始」**，先解析 §0.4 工作目录，再创建仓库并进入 Phase 0。

### 0.3 关联背景文档（只读参考，冲突以本文为准）

| 文档 | 用途 |
|:-----|:-----|
| `中亚短剧平台_核心人群与Tab结构_v2.md` | Tab 与人群 |
| `中亚短剧平台_App整体框架与大纲_v1.md` | 架构 |
| `中亚短剧平台_全流程执行方案_v3.md` | 业务规则 |
| `中亚短剧平台_核心人群与Tab结构_v2.md` | 红果式 Tab 与人群 |

### 0.4 工作目录解析（用户指定，禁止写死）

Agent 启动时按以下**优先级**确定 `WORKSPACE_ROOT`（ monorepo 根目录）：

```
1. 用户触发语中显式给出的绝对路径
   例：「在 D:\projects\my-drama 执行 BUILD」
2. 环境变量 KOROTKO_WORKSPACE 或 BUILD_WORKSPACE_ROOT
3. 当前 Shell 的 cwd（若已是项目根或用户刚 cd 进去的目录）
4. Git 仓库根目录（git rev-parse --show-toplevel）
```

**规则**：

- 本文档凡出现 `{WORKSPACE_ROOT}`，均替换为上述解析结果。
- **禁止** Agent 自行选择 `E:\`、`C:\Users\...` 等未在 1–4 中出现的目录。
- 若路径不存在，在 `WORKSPACE_ROOT` 下创建 monorepo；若已存在且含 `apps/api`，则**续建**而非覆盖删除。
- `BUILD_SPEC_PATH` 默认为本文档路径，不随工作目录变化。

**用户指定示例**（推荐随启动命令一并给出）：

```
在 E:\my-work\drama-app 执行 BUILD 规格书
KOROTKO_WORKSPACE=D:\code\korotko 执行 BUILD
```

---

## §1 最终产品定义（Done = 什么）

### 1.1 交付物清单

| # | 交付物 | 路径 | 验收 |
|:-:|:-------|:-----|:-----|
| 1 | Flutter 移动端（Android 可构建 APK） | `apps/mobile/` | `flutter build apk` 成功 |
| 2 | Node.js API 服务 | `apps/api/` | 健康检查 200 + 全套集成测试通过 |
| 3 | 运营 CMS 后台（Web） | `apps/admin/` | 可上传剧集、管理内容 |
| 4 | PostgreSQL Schema + Seed | `infra/db/` | migrate + seed 一键完成 |
| 5 | Docker Compose 本地全栈 | `docker-compose.yml` | `docker compose up` 后 App 可连 API |
| 6 | 内置 3 部样例短剧（各 5 集 HLS） | seed 数据 | App 内可播放 |
| 7 | 网赚+提现（Mock 支付可演示） | API + App | 签到→看剧→提现流程跑通 |
| 8 | 广告解锁（Mock 广告 SDK） | App | 激励视频解锁下一集 |
| 9 | README + `.env.example` | 根目录 | 新人 15 分钟内本地跑起 |

### 1.2 功能范围（P0+P1 全做，P2 不做）

**包含**：4 Tab（首页/福利/追剧/我的）、竖屏播放（倍速/选集/追剧/点赞/分享/长按快进）、广告解锁、金币系统（签到连击、红包雨、开宝箱、吃饭任务、看剧存币进度条）、邀请码、提现（Mock+真实适配器，提现前激励广告）、CMS（含分集日更、版权分账字段）、**哈萨克语 UI 默认**（`kk` 主路径全覆盖 + 设置页可切俄语 `ru`）、用户协议/隐私政策哈语版、基础反作弊、观看进度、榜单与分类推荐。

**不包含（明确排除）**：Telegram Mini App、直播、网文、SVOD 订阅、GhostCut 生产流水线、AIFC 法律实体、应用商店上架代提交。

### 1.3 产品定位（实现时必须体现）

- **主产品**：免费短剧内容平台（首页默认、点击即播）
- **留存工具**：福利 Tab（金币+Kaspi/Uzum 提现），不做网赚 App 视觉

---

## §2 锁定技术决策（禁止重新选型）

| 项 | 锁定值 |
|:---|:-------|
| 移动端 | Flutter 3.24+，Dart 3.5+ |
| 视频播放 | `video_player` + `chewie` 或 `better_player`（HLS） |
| 状态管理 | `riverpod` 2.x |
| 路由 | `go_router` |
| 后端 | Node.js 20 + **Fastify** 4.x + TypeScript |
| ORM | **Prisma** 5.x |
| 数据库 | PostgreSQL 16 |
| 缓存 | Redis 7 |
| 对象存储 | 本地开发：**MinIO**；生产适配器：S3 兼容 API |
| 转码 | FFmpeg（Docker 内），输出 HLS `.m3u8` + `.ts` |
| CMS 前端 | **React 18 + Vite + Ant Design 5** |
| 鉴权 | JWT（access 7d + refresh 30d） |
| 国际化 | **哈萨克语 `kk` 默认**；俄语 `ru` 备选；`flutter_localizations` + ARB 或等价 i18n；设置页 `kk`/`ru` 切换 |
| 用户协议 | 哈萨克语为主文档；俄语版同路径可读（`?lang=ru` 或设置切换） |
| 包管理 | 根目录 `pnpm` workspace |
| 测试 | API: `vitest`；Flutter: `flutter test` |
| 项目名 | monorepo 名 `korotko-platform` |
| App 显示名 | `Korotko` / `Қысқа`（`kk`）；`Korotko` / `Коротко`（`ru`） |
| API 端口 | `3000` |
| Admin 端口 | `5173` |
| MinIO 端口 | `9000` |

### 2.1 外部服务缺 Key 时的策略

| 服务 | 无 Key 时 |
|:-----|:----------|
| Yandex Ads / AdMob | 使用 `MockAdService`：固定 3 秒倒计时后回调 `onRewarded` |
| Kaspi / Uzum | 使用 `MockPayoutProvider`：提现 2 秒后状态变 `success` |
| Firebase FCM | 跳过推送，接口留空实现 |
| 短信验证码 | **开发模式固定验证码 `000000`** |

---

## §3 仓库结构（必须严格创建）

```
{WORKSPACE_ROOT}/
├── apps/
│   ├── mobile/                 # Flutter App
│   │   ├── lib/
│   │   │   ├── main.dart
│   │   │   ├── app.dart
│   │   │   ├── core/           # theme, router, dio, i18n
│   │   │   ├── features/
│   │   │   │   ├── home/
│   │   │   │   ├── player/
│   │   │   │   ├── welfare/    # 福利 Tab
│   │   │   │   ├── following/  # 追剧 Tab
│   │   │   │   ├── profile/    # 我的 Tab
│   │   │   │   └── auth/
│   │   │   └── shared/
│   │   └── pubspec.yaml
│   ├── api/                    # Fastify API
│   │   ├── src/
│   │   │   ├── index.ts
│   │   │   ├── plugins/
│   │   │   ├── routes/
│   │   │   ├── services/
│   │   │   └── adapters/       # mock/real 广告、支付
│   │   ├── prisma/
│   │   │   └── schema.prisma
│   │   └── package.json
│   └── admin/                  # React CMS
│       ├── src/
│       └── package.json
├── packages/
│   └── shared-types/           # 共享 TS 类型（可选）
├── infra/
│   ├── db/
│   │   ├── migrations/
│   │   └── seed.ts
│   ├── ffmpeg/
│   │   └── transcode.sh
│   └── nginx/                  # 可选反向代理
├── scripts/
│   ├── setup.ps1               # Windows 一键初始化
│   ├── dev.ps1                 # 启动全栈
│   └── verify.ps1              # §9 验证
├── docker-compose.yml
├── pnpm-workspace.yaml
├── .env.example
├── README.md
└── AGENTS.md                   # 指向本 BUILD 文档
```

---

## §4 数据模型（Prisma Schema — 完整实现）

```prisma
// apps/api/prisma/schema.prisma — Agent 照抄并实现 migrate

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum DramaStatus { draft review published banned }
enum DramaLevel { S A B }
enum UnlockType { free ad coin }
enum WithdrawStatus { pending processing success failed }
enum WithdrawChannel { kaspi uzum mock }
enum CoinType {
  checkin checkin_streak watch watch_progress ad invite register bonus
  red_packet treasure_box meal breakfast lunch dinner snack withdraw_ad
}
enum DramaPreference { female male mixed }
enum EpisodeStatus { draft scheduled published }
enum ReleaseMode { all_at_once daily drip }
enum RankType { hot new completed }

model User {
  id               String          @id @default(uuid())
  phone            String?         @unique
  nickname         String?
  lang             String          @default("kk")
  dramaPreference  DramaPreference @default(mixed)
  personalizedAds  Boolean         @default(true)
  checkinStreak    Int             @default(0)
  lastCheckinDate  DateTime?       @db.Date
  inviteCode       String          @unique
  invitedById      String?
  invitedBy        User?           @relation("Invite", fields: [invitedById], references: [id])
  invitees         User[]          @relation("Invite")
  riskScore        Int             @default(80)
  deviceId         String?
  createdAt        DateTime        @default(now())
  coinAccount      CoinAccount?
  histories        WatchHistory[]
  favorites        Favorite[]
  follows          DramaFollow[]
  likes            EpisodeLike[]
  withdraws        WithdrawOrder[]
  coinTxs          CoinTransaction[]
  taskProgress     UserTaskProgress[]
  checkins         CheckinRecord[]
}

model Category {
  id       Int     @id @default(autoincrement())
  slug     String  @unique
  nameRu   String
  nameKk   String
  dramas   Drama[]
}

model Drama {
  id                    String      @id @default(uuid())
  titleRu               String
  titleKk               String
  descriptionRu         String?
  coverUrl              String
  categoryId            Int
  category              Category    @relation(fields: [categoryId], references: [id])
  totalEpisodes         Int
  publishedEpisodeCount Int         @default(0)   // 已放出集数（日更模式）
  freeEpisodes          Int         @default(2)
  level                 DramaLevel  @default(A)
  status                DramaStatus @default(draft)
  releaseMode           ReleaseMode @default(daily)
  dailyReleaseCount     Int         @default(3)   // 日更模式下每日放出集数
  publisherName         String?                   // 版权方名称（CMS）
  revenueSharePct       Decimal?    @db.Decimal(5, 2) // 分账比例 %
  minGuaranteeUsd       Decimal?    @db.Decimal(10, 2) // 保底金额 USD
  playCount             Int         @default(0)
  tags                  String[]
  genderTag             String?     // female | male | mixed — 影响推荐
  episodes              Episode[]
  favorites             Favorite[]
  follows               DramaFollow[]
  histories             WatchHistory[]
  createdAt             DateTime    @default(now())
  publishedAt           DateTime?
  lastEpisodeReleasedAt DateTime?
}

model Episode {
  id           String        @id @default(uuid())
  dramaId      String
  drama        Drama         @relation(fields: [dramaId], references: [id])
  episodeNum   Int
  durationSec  Int
  hlsUrl       String
  unlockType   UnlockType    @default(free)
  coinCost     Int           @default(0)
  status       EpisodeStatus @default(draft)
  releaseAt    DateTime?     // 定时发布（日更）
  likeCount    Int           @default(0)
  likes        EpisodeLike[]
  @@unique([dramaId, episodeNum])
}

model DramaFollow {
  id              String   @id @default(uuid())
  userId          String
  user            User     @relation(fields: [userId], references: [id])
  dramaId         String
  drama           Drama    @relation(fields: [dramaId], references: [id])
  lastEpisodeNum  Int      @default(0)
  hasUpdate       Boolean  @default(false)  // 有新集更新时标红
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt
  @@unique([userId, dramaId])
}

model EpisodeLike {
  id         String   @id @default(uuid())
  userId     String
  user       User     @relation(fields: [userId], references: [id])
  episodeId  String
  episode    Episode  @relation(fields: [episodeId], references: [id])
  createdAt  DateTime @default(now())
  @@unique([userId, episodeId])
}

model UserTaskProgress {
  id          String   @id @default(uuid())
  userId      String
  user        User     @relation(fields: [userId], references: [id])
  taskKey     String   // red_packet | treasure_box | breakfast | lunch | dinner | snack | watch_daily
  completedAt DateTime @default(now())
  amount      Int
  @@index([userId, taskKey, completedAt])
}

model CheckinRecord {
  id        String   @id @default(uuid())
  userId    String
  user      User     @relation(fields: [userId], references: [id])
  date      DateTime @db.Date
  streakDay Int      // 1-7 循环
  amount    Int
  @@unique([userId, date])
}

model WatchHistory {
  id             String   @id @default(uuid())
  userId         String
  user           User     @relation(fields: [userId], references: [id])
  dramaId        String
  drama          Drama    @relation(fields: [dramaId], references: [id])
  episodeId      String
  progressSec    Int      @default(0)
  completed      Boolean  @default(false)
  updatedAt      DateTime @updatedAt
  @@unique([userId, dramaId])
}

model Favorite {
  id        String   @id @default(uuid())
  userId    String
  user      User     @relation(fields: [userId], references: [id])
  dramaId   String
  drama     Drama    @relation(fields: [dramaId], references: [id])
  createdAt DateTime @default(now())
  @@unique([userId, dramaId])
}

model CoinAccount {
  userId          String @id
  user            User   @relation(fields: [userId], references: [id])
  balance         Int    @default(0)
  totalEarned     Int    @default(0)
  totalWithdrawn  Int    @default(0)
}

model CoinTransaction {
  id        String   @id @default(uuid())
  userId    String
  user      User     @relation(fields: [userId], references: [id])
  amount    Int
  type      CoinType
  refId     String?
  createdAt DateTime @default(now())
}

model WithdrawOrder {
  id          String          @id @default(uuid())
  userId      String
  user        User            @relation(fields: [userId], references: [id])
  amountCoins Int
  amountUsd   Decimal         @db.Decimal(10, 2)
  channel     WithdrawChannel
  status      WithdrawStatus  @default(pending)
  externalId  String?
  createdAt   DateTime        @default(now())
  processedAt DateTime?
}

model AdConfig {
  id                Int  @id @default(1)
  interstitialEvery Int  @default(2)
  rewardUnlockCount Int  @default(3)
  freeEpisodes      Int  @default(2)
}

model AdminUser {
  id           String @id @default(uuid())
  email        String @unique
  passwordHash String
}
```

### 4.1 金币经济常量（硬编码在 `apps/api/src/config/economy.ts`）

```typescript
// 中亚版经济：1000 币 = $1（红果约 33000:1，本项目刻意更慷慨以利冷启动）
export const ECONOMY = {
  COINS_PER_USD: 1000,
  REGISTER_BONUS: 500,
  CHECKIN: 50,
  CHECKIN_STREAK_7: 500,       // 连续 7 天额外奖励
  WATCH_EPISODE: 20,
  WATCH_DAILY_CAP: 200,
  WATCH_PROGRESS_PER_MIN: 5,   // 看剧存币进度条：每分钟 +5 币
  WATCH_PROGRESS_DAILY_CAP: 100,
  AD_REWARD: 30,
  AD_DAILY_CAP: 150,
  AD_TASK_SLOTS: 9,              // 对标红果「小视频任务」9 格
  RED_PACKET_BASE: 150,
  RED_PACKET_AD_DOUBLE: 300,
  RED_PACKET_COOLDOWN_MIN: 30,
  TREASURE_BOX_BASE: 80,
  TREASURE_BOX_AD_DOUBLE: 160,
  TREASURE_BOX_COOLDOWN_MIN: 15,
  MEAL_BREAKFAST: 40,            // 06:00–09:00 UTC+5
  MEAL_LUNCH: 40,                // 11:00–13:00
  MEAL_DINNER: 40,               // 17:00–20:00
  MEAL_SNACK: 30,                // 21:00–23:00
  INVITE: 500,
  INVITE_FIRST_WITHDRAW: 1000,
  MIN_WITHDRAW: 2000,
  WITHDRAW_REQUIRES_AD: true,    // 提现前必须完整看 1 条激励广告
  NEW_USER_DAILY_WITHDRAW_USD: 5,
  TRUSTED_DAILY_WITHDRAW_USD: 20,
} as const;
```

---

## §5 API 规格（完整路由 — 必须全部实现）

**Base URL**：`http://localhost:3000/api/v1`  
**Auth Header**：`Authorization: Bearer <access_token>`

### 5.0 本地化响应规则（BUILD-1.3）

- App 面向用户的 `title` / `name` / `description` 按 `User.lang` 返回（**默认 `kk`**）
- 响应体同时保留 `titleKk` / `titleRu`（及 `nameKk` / `nameRu`）供客户端切换
- `/dramas/search?q=` 同时匹配 `titleKk` 与 `titleRu`（大小写不敏感）
- Seed、CMS 录入：**哈萨克语标题/分类名为必填**；俄语为必填备选字段
- 新用户 / 游客默认 `lang=kk`

### 5.1 Auth

| Method | Path | Body | Response |
|:-------|:-----|:-----|:---------|
| POST | `/auth/sms/send` | `{ phone }` | `{ ok: true }` |
| POST | `/auth/sms/login` | `{ phone, code, deviceId? }` | `{ accessToken, refreshToken, user, isNew }` |
| POST | `/auth/refresh` | `{ refreshToken }` | `{ accessToken }` |
| POST | `/auth/guest` | `{ deviceId }` | 游客模式，播放 3 集后强制登录 |

### 5.2 Drama & Play

| Method | Path | 说明 |
|:-------|:-----|:-----|
| GET | `/dramas` | query: `category,page,limit,sort=hot\|new,gender=female\|male` |
| GET | `/dramas/:id` | 剧集详情 + 分集列表（含 unlock / releaseAt 状态） |
| GET | `/dramas/search?q=` | 搜索 |
| GET | `/dramas/rank/:type` | `type=hot\|new\|completed` 榜单（首页区块） |
| GET | `/categories` | 分类列表（霸总/甜宠/战神/逆袭/悬疑/穿越） |
| GET | `/play/url/:episodeId` | 返回 `{ hlsUrl, expiresAt }` 签名 URL |
| POST | `/play/progress` | `{ dramaId, episodeId, progressSec, completed }` |
| POST | `/play/unlock/ad` | `{ episodeId }` 广告解锁后续 N 集 |
| POST | `/play/unlock/coin` | `{ episodeId }` 金币解锁 |
| POST | `/play/follow/:dramaId` | 追剧（加入「在看」） |
| DELETE | `/play/follow/:dramaId` | 取消追剧 |
| POST | `/play/like/:episodeId` | 点赞 |
| DELETE | `/play/like/:episodeId` | 取消点赞 |
| GET | `/play/continue` | 继续观看（首页置顶） |
| POST | `/play/share/:dramaId` | 生成分享 deep link（返回 `shareUrl`） |

### 5.3 Following（追剧 Tab — 三子 Tab 分离）

| Method | Path | 说明 |
|:-------|:-----|:-----|
| GET | `/following/watching` | 正在追（含 `hasUpdate` 红点） |
| GET | `/following/favorites` | 我的收藏 |
| GET | `/following/history` | 观看历史（按 `updatedAt` 倒序） |
| GET | `/following/recommend` | 猜你喜欢（流失召回） |
| POST | `/favorites/:dramaId` | 收藏 |
| DELETE | `/favorites/:dramaId` | 取消收藏 |
| POST | `/following/clear-update/:dramaId` | 用户点开更新后清除红点 |

### 5.4 Welfare（福利 Tab — 对标红果任务体系）

| Method | Path | 说明 |
|:-------|:-----|:-----|
| GET | `/welfare/summary` | 余额、今日已赚、全部任务状态（含冷却倒计时） |
| POST | `/welfare/checkin` | 签到（含连续 7 天 streak 逻辑） |
| POST | `/welfare/red-packet` | 红包雨领取；query `?withAd=true` 广告翻倍 |
| POST | `/welfare/treasure-box` | 开宝箱；开宝箱后可选 `withAd` 再看广告翻倍 |
| POST | `/welfare/meal/:slot` | `slot=breakfast\|lunch\|dinner\|snack`，时段校验 |
| POST | `/welfare/watch-reward` | body: `{ episodeId }` 完播发币 |
| POST | `/welfare/watch-progress` | body: `{ watchedSec }` 看剧存币进度条 tick |
| POST | `/welfare/ad-reward` | 广告完播发币（9 格任务槽，每日上限 AD_DAILY_CAP） |
| GET | `/welfare/transactions` | 金币流水 |
| POST | `/withdraw/apply` | `{ amountCoins, channel, adWatched: true }` — 未看广告返回 `WITHDRAW_AD_REQUIRED` |
| GET | `/withdraw/orders` | 提现记录 |

### 5.5 Invite

| Method | Path | 说明 |
|:-------|:-----|:-----|
| GET | `/invite/code` | 我的邀请码 |
| POST | `/invite/bind` | `{ code }` 绑定邀请关系 |

### 5.6 User

| Method | Path | 说明 |
|:-------|:-----|:-----|
| GET | `/user/profile` | 含 `dramaPreference`, `personalizedAds`, `checkinStreak` |
| PUT | `/user/profile` | `{ nickname, lang, dramaPreference, personalizedAds }` |
| dramaPreference | `female \| male \| mixed` | 影响首页/榜单推荐权重 |
| personalizedAds | `boolean` | 关闭后 MockAd 仍展示但不采集画像 |

### 5.7 Admin（CMS，独立 JWT）

| Method | Path | 说明 |
|:-------|:-----|:-----|
| POST | `/admin/login` | |
| GET | `/admin/dramas` | |
| POST | `/admin/dramas` | 创建剧集元数据 |
| PUT | `/admin/dramas/:id` | |
| POST | `/admin/dramas/:id/episodes` | 上传分集（multipart 或 hlsUrl） |
| PUT | `/admin/episodes/:id/schedule` | `{ releaseAt }` 单集定时发布 |
| POST | `/admin/dramas/:id/release-batch` | 日更模式：放出下一批 N 集 |
| POST | `/admin/dramas/:id/publish` | 发布（含 `releaseMode`, `publisherName`, `revenueSharePct`, `minGuaranteeUsd`） |
| GET | `/admin/stats/overview` | DAU、广告、提现、版权分账预估汇总 |

### 5.8 统一响应格式

```typescript
// 成功
{ "ok": true, "data": { ... } }
// 失败
{ "ok": false, "error": { "code": "INSUFFICIENT_COINS", "message": "..." } }
```

---

## §6 Flutter App 规格

### 6.1 Tab 结构（严格 4 Tab，顺序固定）

| Index | Tab | Icon | 默认 |
|:-----:|:----|:-----|:----:|
| 0 | Басты 首页 | home | ✅ |
| 1 | Сыйлықтар 福利 | card_giftcard | |
| 2 | Сериалдарым 追剧 | play_circle | |
| 3 | Профиль 我的 | person | |

**禁止**：赚钱/金币作为主 Tab 图标动画；首页禁止满屏金币。

### 6.2 屏幕清单（每个必须有路由）

| Screen | Route | 功能 |
|:-------|:------|:-----|
| SplashScreen | `/` | 检查 token，跳首页 |
| HomeScreen | `/home` | 搜索栏+继续观看置顶+推荐流（点击即播）+分类横滑+三榜单+专题位 |
| PlayerScreen | `/play/:dramaId` | 全屏竖屏，上下滑切集，见 §6.3 |
| SearchScreen | `/search` | 热搜 + 结果列表，点击即播 |
| WelfareScreen | `/welfare` | 余额卡+提现 CTA+签到+红包雨+宝箱+吃饭任务+看剧进度条+9 格广告任务 |
| FollowingScreen | `/following` | 子 Tab：在看 / 收藏 / 历史 + 猜你喜欢 |
| ProfileScreen | `/profile` | 账号+看剧偏好+邀请+语言+通知+协议 |
| SettingsScreen | `/settings` | 广告个性化开关、省流模式 |
| LoginSheet | modal | 看满 3 集后弹出 |
| WithdrawScreen | `/withdraw` | 提现前强制激励广告 |
| InviteScreen | `/invite` | 邀请码 + 分享 |
| EpisodePickerSheet | modal | 播放器内选集面板 |
| SpeedPickerSheet | modal | 倍速 1.0 / 1.25 / 1.5 / 2.0 |

### 6.3 播放器行为（必须实现 — 对标红果）

```
进入播放（首页推荐点击封面直达，无详情页中转）
  → 加载 HLS，默认 1.0x 倍速
  → 右侧浮层：追剧❤️ / 点赞👍 / 分享↗ / 选集≡ / 倍速1.0x
  → 第 1–2 集免费连播
  → 第 3 集前：RewardedAdDialog「看 30 秒解锁 3 集」
      → MockAdService 3 秒倒计时 → POST /play/unlock/ad
  → 每 2 集插屏（Mock Interstitial 1 秒）
  → 播放进度每 10 秒 POST /play/progress
  → 同时每 60 秒 POST /welfare/watch-progress（看剧存币进度条）
  → 完播（>80%）POST /welfare/watch-reward + 底部轻条「+20 монета」（`kk`）/「+20 монет」（`ru`）
  → 上滑下一集 / 下滑上一集
  → 长按屏幕右侧区域：2.0x 快进（松手恢复）
  → 双击暂停/播放
  → 追剧按钮：POST /play/follow/:dramaId；已追显示实心
  → 分享：POST /play/share → 系统分享面板
```

### 6.3.1 首页信息架构（Tab 1）

```
首页 / Басты
├── 顶部搜索栏 → /search
├── 继续观看（GET /play/continue，横向卡片，点击即播）
├── 分类横滑（GET /categories：ceo/sweet/warrior/revenge/suspense/isekai）
├── 推荐流（竖屏封面瀑布流，点击即播，无中间详情页）
├── 榜单区（GET /dramas/rank/:type × 3：热门/新剧/完结）
├── 专题运营位（seed 1 个 banner）
└── 底部低干扰横幅（Mock Banner，可关）
```

### 6.3.2 福利页信息架构（Tab 2）

```
福利 / Сыйлықтар
├── 金币余额 + 今日已赚（静态卡片，禁止全屏金币动画）
├── 一键提现 CTA → /withdraw（提现前激励广告）
├── 连续签到（7 天格子，第 7 天高亮 +500）
├── 红包雨（冷却倒计时，领取后可「看广告翻倍」）
├── 开宝箱（15 分钟冷却，开后再看广告翻倍）
├── 吃饭任务（早/午/晚/夜宵 4 时段，未到时灰色）
├── 看剧存币进度条（今日上限 100 币，播放时实时涨）
├── 9 格激励视频任务（每格 +30，每日上限 5 次有效）
├── 邀请好友入口
└── 金币流水 + 规则说明
```

### 6.3.3 追剧页信息架构（Tab 3）

```
追剧 / Сериалдарым
├── 子 Tab：正在追 | 收藏 | 历史
├── 正在追：封面+更新红点（hasUpdate）
├── 收藏：网格封面
├── 历史：列表+进度条
└── 底部「猜你喜欢」横滑（GET /following/recommend）
```

### 6.4 UI 主题

```dart
// 深色沉浸背景 — 对标红果
primaryBackground: Color(0xFF0F0F0F)
cardBackground: Color(0xFF1A1A1A)
accent: Color(0xFFE94560)  // 剧集封面强调色，非网赚绿
textPrimary: Color(0xFFF5F5F5)
font: 系统默认 + 西里尔文友好
```

### 6.5 关键文案（i18n — `kk` 默认，`ru` 备选）

实现要求：`MaterialApp.locale` 默认 `kk`；`ProfileScreen` 提供 `Қазақша / Русский` 切换，切换后调用 `PUT /user/profile` 并热重载文案。

| Key | kk（默认） | ru（备选） |
|:----|:-----------|:-----------|
| app_name | Korotko | Коротко |
| tab_home | Басты | Главная |
| tab_welfare | Сыйлықтар | Бонусы |
| tab_following | Сериалдарым | Мои сериалы |
| tab_profile | Профиль | Профиль |
| home_continue | Көруді жалғастыру | Продолжить просмотр |
| home_rank_hot | Танымал | Популярное |
| home_rank_new | Жаңалықтар | Новинки |
| home_rank_done | Аяқталғандар | Завершённые |
| welfare_withdraw | Kaspi-ге шығару | Вывести в Kaspi |
| welfare_red_packet | Сыйлық жаңбыры | Дождь подарков |
| welfare_treasure | Қазына ашу | Открыть сундук |
| welfare_meal | Тамақтану | Приём пищи |
| player_unlock_ad | 30 сек көріңіз — 3 серия ашылады | Смотрите 30 сек — откройте 3 серии |
| player_follow | Тізіміме | В мой список |
| player_speed | Жылдамдық | Скорость |
| checkin_done | +50 монета | +50 монет |
| checkin_streak_7 | 7 күн қатарынан — +500! | 7 дней подряд — +500! |
| withdraw_ad_required | Алдымен жарнаманы көріңіз | Сначала посмотрите рекламу |
| following_watching | Қарап жатырмын | Смотрю |
| following_favorites | Таңдаулылар | Избранное |
| following_history | Тарих | История |
| profile_preference | Арналықтар | Предпочтения |
| settings_lang | Тіл / Язык | Язык |
| settings_personalized_ads | Жекелендірілген жарнама | Персонализированная реклама |
| legal_tos | Пайдаланушы келісімі | Пользовательское соглашение |
| legal_privacy | Құпиялылық саясаты | Политика конфиденциальности |

---

## §7 CMS Admin 规格

### 7.1 页面

| 页面 | 功能 |
|:-----|:-----|
| 登录 | email/password |
| 仪表盘 | 总剧集、总用户、今日播放 |
| 剧集列表 | CRUD、状态筛选 |
| 剧集编辑 | 上传封面、**哈萨克语元数据（主）**+ 俄语元数据（备）、版权方、分账%、保底 USD、`releaseMode` |
| 分集上传 | 视频 → FFmpeg HLS → MinIO；可设 `releaseAt` |
| 日更发布 | 「放出下一批」按钮，`dailyReleaseCount` 控制 |
| 发布 | draft → published |
| 提现审核 | 列表（Mock 模式自动通过） |

### 7.2 默认管理员（seed）

```
email: admin@korotko.local
password: KorotkoAdmin2026!
```

---

## §8 实施阶段（Agent 按序自动执行）

### Phase 0：脚手架（Day 1）

**任务**：
1. 在 `{WORKSPACE_ROOT}` 创建 §3 目录树（路径由 §0.4 解析，禁止 Agent 自选盘符）
2. 初始化 `pnpm-workspace.yaml`
3. 编写 `docker-compose.yml`：postgres、redis、minio、api、admin
4. 编写 `scripts/setup.ps1` 和 `scripts/dev.ps1`
5. 创建 `.env.example`
6. `git init` + 首次 commit

**验证**：`docker compose config` 无报错

---

### Phase 1：API 核心（Day 2–4）

**任务**：
1. 初始化 Fastify + Prisma + §4 schema
2. `prisma migrate dev` + seed：
   - 6 个分类：ceo, sweet, revenge, warrior, suspense, isekai
   - 3 部剧 × 5 集（`releaseMode=daily`，初始仅放出 3 集）
   - 样例 HLS：使用 **公网测试流** 或本地 `infra/sample-video/` 转码
3. 实现 §5.1–5.6 全部路由
4. 实现 `MockAdService`、`MockPayoutProvider`
5. 实现邀请码、反作弊基础（同 deviceId 注册不重复发邀请奖励）
6. 实现 `DailyReleaseService`（CMS 触发 + cron 可选）
7. `vitest` 集成测试 ≥ 30 条（含福利任务冷却、提现广告校验、追剧红点）

**验证**：`pnpm --filter api test` 全绿；`curl localhost:3000/health` OK

---

### Phase 2：CMS Admin（Day 5–6）

**任务**：
1. Vite + React + Ant Design
2. 实现 §7 全部页面
3. 视频上传 → API → FFmpeg 容器转码 → MinIO
4. 打通发布流程

**验证**：浏览器上传 1 集视频后，API `/dramas` 可查到且可播放

---

### Phase 3：Flutter App（Day 7–12）

**任务**：
1. `flutter create` 在 `apps/mobile`
2. 实现 §6 全部 Screen + 4 Tab
3. Dio 对接 API
4. 竖屏播放器 + HLS
5. Mock 广告解锁流程
6. 福利 Tab 完整流程（红包雨/宝箱/吃饭/进度条/9 格广告）
7. 播放器倍速/选集/追剧/点赞/分享/长按快进
8. 追剧三子 Tab + 首页榜单/分类/点击即播
9. 我的页看剧偏好 + 设置页广告开关
10. 游客模式 + 3 集后登录
11. `flutter test` 核心 widget 测试

**验证**：Android 模拟器/真机可：浏览→播放→签到→提现 Mock 成功

---

### Phase 4：联调与种子内容（Day 13）

**任务**：
1. `scripts/verify.ps1` 跑通 §9 全部检查
2. seed 3 部完整短剧（若缺视频，用 FFmpeg 从 30 秒样本生成 5 集）
3. 修复联调 bug，不留 TODO
4. 编写 `README.md` 部署说明

**验证**：§10 Done 清单 100%

---

### Phase 5：打包交付（Day 14）

**任务**：
1. `flutter build apk --release`
2. 输出 `dist/korotko-v1.0.0.apk`
3. `docker compose` 生产模式配置文件 `docker-compose.prod.yml`
4. 更新 `E:\知识库\02_市场分析\短剧出海\` 下写交付记录 `Korotko_交付清单.md`（Agent 自动生成）

**验证**：APK 可安装；Docker 全栈启动后功能与开发环境一致

---

## §9 自动验证清单（每阶段必跑）

```powershell
# scripts/verify.ps1 必须实现并全部 PASS

# 1. 基础设施
docker compose ps                          # 全部 healthy

# 2. API
curl http://localhost:3000/health          # 200
pnpm --filter api test                     # pass

# 3. 核心 API 冒烟（自动化脚本）
# - 注册登录获取 token
# - 拉取剧集列表 >= 3
# - 获取播放 URL
# - 签到 + 红包雨 + 宝箱 + 看剧奖励 + 余额增加
# - 提现申请（无广告应失败，有广告应 success）
# - 追剧/点赞/榜单 API 冒烟

# 4. Admin
curl http://localhost:5173                 # 200

# 5. Flutter
cd apps/mobile && flutter analyze          # 0 issues
cd apps/mobile && flutter test             # pass
cd apps/mobile && flutter build apk        # success
```

**规则**：任一 FAIL → 自动修复 → 重跑，不向用户报告直到全 PASS 或 5 轮后记录 blocker 并继续其他项。

---

## §10 终态 Done 检查表

Agent 声明完工前，以下必须全部 `[x]`：

```
[ ] {WORKSPACE_ROOT} 仓库存在且结构符合 §3
[ ] docker compose up -d 后 30 秒内 API 健康
[ ] App 首页：继续观看+分类+三榜单+推荐流，点击封面即播
[ ] 竖屏播放器：上下切集、倍速、选集、追剧、点赞、分享、长按快进
[ ] 第 3 集广告解锁流程可用
[ ] 福利 Tab：签到连击、红包雨、宝箱、吃饭任务、看剧进度条、9 格广告、提现前广告
[ ] 追剧 Tab：在看/收藏/历史 三子 Tab + 更新红点
[ ] 我的 Tab：看剧偏好、邀请码、广告个性化开关
[ ] CMS：上传、日更放出、版权分账字段可编辑
[ ] 哈萨克语 UI 主路径全覆盖（4 Tab + 播放 + 福利 + 提现 + 协议）
[ ] 设置页可切换俄语且切换后全文案生效
[ ] README 含完整启动步骤（含 WORKSPACE_ROOT 说明）
[ ] dist/korotko-v1.0.0.apk 存在
[ ] 代码中无 TODO/FIXME（测试文件除外）
```

---

## §11 环境变量（.env.example 模板）

```bash
# Database
DATABASE_URL=postgresql://korotko:korotko@localhost:5432/korotko
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET=change-me-in-production-korotko-2026
JWT_REFRESH_SECRET=change-me-refresh-korotko-2026

# MinIO / S3
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=korotko-videos
S3_PUBLIC_URL=http://localhost:9000/korotko-videos

# Adapters（空则自动 Mock）
YANDEX_ADS_ENABLED=false
KASPI_PAYOUT_ENABLED=false
UZUM_PAYOUT_ENABLED=false

# SMS（开发模式）
SMS_MOCK=true
SMS_MOCK_CODE=000000

# Admin
ADMIN_EMAIL=admin@korotko.local
ADMIN_PASSWORD=KorotkoAdmin2026!

# App
API_PORT=3000
API_PUBLIC_URL=http://10.0.2.2:3000   # Android 模拟器访问宿主机
```

---

## §12 支付/广告真实适配器（可选，有 Key 时自动切换）

Agent 实现 **适配器模式**：

```typescript
// apps/api/src/adapters/payout.ts
interface PayoutProvider {
  transfer(params: { phone: string; amount: number; channel: string }): Promise<{ externalId: string }>;
}
// 若 KASPI_PAYOUT_ENABLED=true 且 KASPI_API_KEY 存在 → KaspiProvider
// 否则 → MockPayoutProvider（始终可用）
```

```dart
// apps/mobile/lib/core/ads/ad_service.dart
abstract class AdService {
  Future<bool> showRewarded();
  Future<void> showInterstitial();
}
// YANDEX_ADS_ENABLED → YandexAdService
// 否则 → MockAdService（3 秒倒计时 UI）
```

**不得**因未配置 Key 停止开发。

---

## §13 Seed 样例剧集（Phase 1 必须写入）

| dramaId | titleKk | titleRu | category | 集数 | freeEpisodes | releaseMode | genderTag |
|:--------|:--------|:--------|:---------|:----:|:------------:|:-----------:|:---------:|
| seed-1 | Патшайымның өшкіші | Месть королевы | revenge | 5 | 2 | daily | female |
| seed-2 | Тәтті тұзақ | Сладкая ловушка | sweet | 5 | 2 | daily | female |
| seed-3 | Жауынгердің оралуы | Возвращение бойца | warrior | 5 | 2 | daily | male |

**分类 Seed（`nameKk` / `nameRu` 均必填）**：ceo=Бастық/Босс · sweet=Махаббат/Романтика · warrior=Жауынгер/Боевик · revenge=Кек/Месть · suspense=Жанрлық/Триллер · isekai=Уақытша/Попаданец

每集 `durationSec=90`；`hlsUrl` 指向 MinIO 或公网测试 m3u8。  
Seed 时 `publishedEpisodeCount=3`（日更剧初始只放出前 3 集）；`publisherName` 填示例版权方。

---

## §14 Agent 并行策略（Grok + Codex 协作时）

若多 Agent 并行：

| Agent | 负责 Phase | 目录 |
|:------|:-----------|:-----|
| Agent A | Phase 1 API | `apps/api/` |
| Agent B | Phase 2 Admin | `apps/admin/` |
| Agent C | Phase 3 Mobile | `apps/mobile/` |
| 编排者 | Phase 0、4、5、§9 验证 | 根目录 + scripts |

**接口契约**：以 §4 Prisma + §5 API 为冻结接口；移动端不得等 Admin 完成，先用 seed 数据开发。

---

## §15 反作弊最低实现

| 规则 | 实现 |
|:-----|:-----|
| 同 deviceId 重复注册 | 不发注册奖励 |
| 播放奖励 | progress ≥ 80% 才发 |
| 每日上限 | ECONOMY 常量强制 |
| 邀请生效 | 被邀请人观看 ≥3 集 |
| 提现 | riskScore < 40 提高门槛 |
| 首提 | 自动通过（Mock） |
| 红包雨/宝箱冷却 | Redis 或 DB 记录 `lastCompletedAt`，冷却内拒绝 |
| 吃饭任务 | 服务端校验 UTC+5 时段，客户端时间不可信 |
| 提现 | `adWatched=true` 且 5 分钟内有效 token |

---

## §16 启动指令（给用户）

完成后用户只需：

```powershell
# 工作目录由用户指定，示例：
cd {WORKSPACE_ROOT}
.\scripts\setup.ps1    # 首次
.\scripts\dev.ps1      # 启动
# 安装 dist\korotko-v1.0.0.apk 到手机
# API 地址改为电脑局域网 IP
```

---

## §17 红果对标补全说明（调研来源 + 本地化取舍）

> 本节汇总 2026-07 红果公开资料与用户体验报告，明确 **Korotko 照搬 / 简化 / 不做** 的边界。

### 17.1 调研来源摘要

| 来源 | 红果要点 |
|:-----|:---------|
| App Store / 应用宝简介 | 免费海量短剧 + 金币福利；番茄小说同源逻辑 |
| 人人都是产品经理 / v2 文档 | Tab=首页/福利/追剧/我的；30+ 低线用户；福利是留存非主产品 |
| 网易/U客直谈 2026 | 33000 币≈1 元；挂机看剧+开宝箱+9 格广告任务；提现需看广告 |
| 蹦酷网用户反馈 2025 | 红包雨 5000 币、宝箱 2000 币、广告翻倍机制；活跃度影响收益 |
| 应用宝键盘功能稿 2025 | 短按快进、长按 2x 倍速（PC 版；移动端映射为长按右侧） |
| 虎嗅 2026 | 版权方保底分账、日更非全放、IAA 为主；VIP 年费 260 元（**Korotko 不做 VIP**） |

### 17.2 功能对照表（红果 → Korotko）

| 红果功能 | Korotko 实现 | 本地化说明 |
|:---------|:-------------|:-----------|
| 4 Tab 结构 | ✅ §6.1 | **哈萨克文 Tab 名**（可切俄语） |
| 首页点击即播 | ✅ §6.3.1 | 跳过详情页 |
| 分类（霸总/甜宠等） | ✅ 6 类 seed | +穿越 isekai |
| 榜单并入首页 | ✅ hot/new/completed | 无独立热门 Tab |
| 继续观看置顶 | ✅ GET /play/continue | |
| 福利：签到 + 7 天连击 | ✅ CHECKIN_STREAK_7 | |
| 福利：红包雨 | ✅ 30min 冷却，广告翻倍 | 金额按 1000:$1 等比缩小 |
| 福利：开宝箱 | ✅ 15min 冷却，广告翻倍 | |
| 福利：吃饭任务 | ✅ 4 时段 UTC+5 | 中亚作息适配 |
| 福利：看剧存币进度条 | ✅ watch-progress API | |
| 福利：9 格高额度广告 | ✅ AD_TASK_SLOTS=9 | |
| 提现前看广告 | ✅ WITHDRAW_REQUIRES_AD | 提现到 Kaspi/Uzum |
| 播放器：倍速/选集 | ✅ 1.0–2.0x | |
| 播放器：追剧/点赞/分享 | ✅ 右侧浮层 | |
| 播放器：长按快进 | ✅ 长按右侧 2x | |
| 追剧：在看/收藏/历史 | ✅ 三子 Tab | |
| 我的：看剧偏好 | ✅ dramaPreference | 男频/女频/混合 |
| 我的：广告个性化 | ✅ personalizedAds | 设置页开关 |
| 分集日更 | ✅ releaseMode=daily | S 级剧每日 3 集 |
| CMS 版权分账/保底 | ✅ publisherName 等字段 | 结算逻辑 P2，字段 P0 |
| 金币 33000:1 | ❌ 改用 1000:1 | 中亚冷启动更慷慨 |
| 网文/听书 Tab | ❌ 排除 | 纯短剧 |
| VIP 年费会员 | ❌ 排除 | 下沉用户不愿付费 |
| SVOD 去广告 | ❌ 排除 | 见 §1.2 |

### 17.3 红果未实现但 Korotko 保留的中亚特化

| 功能 | 原因 |
|:-----|:-----|
| Kaspi / Uzum 提现 | 中亚支付习惯，红果是微信/支付宝 |
| 哈萨克语默认 UI | 哈萨克斯坦合规 + 本土认同；俄语作备选 |
| 游客 3 集后登录 | 降低 TG 引流摩擦 |

---

## 附录 A：与红果对齐的产品检查（Agent 完工前必跑）

### A.1 结构与定位

- [ ] 默认落地 **首页**而非福利页
- [ ] 首页主视觉是**剧集封面**不是金币
- [ ] 福利是独立 Tab 而非首页弹窗
- [ ] 无独立「热门」「赚钱」Tab
- [ ] 播放 3 集后才要求登录（游客模式）

### A.2 首页

- [ ] 继续观看置顶且点击即播
- [ ] 分类横滑 ≥6 类
- [ ] 热门/新剧/完结三榜单可见
- [ ] 推荐流点击封面直达 PlayerScreen

### A.3 福利

- [ ] 签到 + 连续 7 天额外奖励
- [ ] 红包雨有冷却 + 广告翻倍
- [ ] 开宝箱有冷却 + 广告翻倍
- [ ] 吃饭 4 时段任务（未到时不可领）
- [ ] 看剧存币进度条播放时增长
- [ ] 提现前必须完整看 1 条激励广告
- [ ] 看剧结束仅底部轻条「+XX 金币」，不强制跳福利 Tab

### A.4 播放器

- [ ] 倍速 1.0/1.25/1.5/2.0 可切换
- [ ] 选集面板可跳转任意已发布集
- [ ] 追剧/点赞/分享按钮可用
- [ ] 长按右侧 2x 快进
- [ ] 上滑/下滑切集 + 进度记忆

### A.5 追剧 / 我的

- [ ] 在看、收藏、历史三子 Tab 分离
- [ ] 新剧更新显示红点
- [ ] 我的页可设男频/女频/混合偏好
- [ ] 设置页可关广告个性化

### A.6 CMS / 内容

- [ ] 日更模式：初始不全放，CMS 可「放出下一批」
- [ ] 版权方名称、分账%、保底 USD 字段可编辑

## 附录 B：文档修订

| 版本 | 日期 | 说明 |
|:-----|:-----|:-----|
| BUILD-1.0 | 2026-07-07 | 首版全自动规格书 |
| BUILD-1.1 | 2026-07-07 | 工作目录改为用户指定 §0.4 |
| BUILD-1.2 | 2026-07-07 | 红果调研补全：福利任务体系、播放器、首页榜单、追剧三 Tab、CMS 日更与版权字段 |
| BUILD-1.3 | 2026-07-07 | **产品决策 C**：默认哈萨克语 UI（`kk`），俄语（`ru`）设置页备选；Seed/CMS/API 双语字段 |

---

**▶ Agent：读取完本文档后，立即从 Phase 0 开始执行，无需等待用户确认。**

**▶ BUILD-1.3 增量（已在跑的 Agent）**：若 Phase 1–3 已按 1.2 用俄语实现，**不得整库重写**；按 §5.0 + §6.5 增量改为 `kk` 默认，补全 `titleKk`/`nameKk` Seed，加语言切换与哈语协议页，重跑 §9 验证。