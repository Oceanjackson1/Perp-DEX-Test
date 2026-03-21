# Perp DEX 研究与测试套件

针对 **13 个永续合约去中心化交易所 (Perp DEX)** 的综合研究与实测框架，聚焦用户注册摩擦、内嵌钱包基础设施、API 认证模型及程序化交易就绪度。

## 项目概述

本项目从两个核心维度，系统性地探测和分析主流 Perp DEX 平台的用户体验与 API 成熟度：

1. **Web2 用户友好度** — 非加密原生用户（邮箱/社交登录）从注册到开始交易有多简单？
2. **API 优先的开发者体验** — 一个全新的 EVM 钱包，多快能完成第一笔程序化下单？

所有测试均使用单一全新 EVM 测试钱包，在测试网/公开端点上进行，零真实资金投入。

## 覆盖平台

| # | 平台 | 登录模式 | 内嵌钱包 | API 认证方式 | 新钱包摩擦度 |
|---|------|---------|---------|-------------|------------|
| 1 | **Hyperliquid** | 钱包 + 邮箱 (Privy) | Privy 邮箱钱包 | 原生钱包签名 / Agent 钱包 | 中低 |
| 2 | **Aster** | 钱包 + 邮箱 | 原生邮箱钱包 | API Key + HMAC SHA256 | 中 |
| 3 | **trade[XYZ]** | 钱包 + Privy 邮箱 | Privy | 底层使用 Hyperliquid API | 中 |
| 4 | **EdgeX** | 钱包 + 邮箱 MPC | Privy（CSP 确认） | API Key + L2 签名 | 低（配置复杂） |
| 5 | **Variational** | 钱包 (Omni) | 无 | 仅读取（交易 API 未就绪） | 不可用 |
| 6 | **Lighter** | 钱包 + 充值 | 无 | API Key + Auth Token + Nonce | 低（需先充值） |
| 7 | **GRVT** | Web2 OAuth (Google/Apple/Microsoft/邮箱) | Dfns MPC + Privy 双层 | Session Cookie / API Key | 低（7步流程 + KYC） |
| 8 | **Extended** | 钱包优先 | Dynamic.xyz（隐藏在 JS 包中） | API Key + Stark 签名 | 测试网高 |
| 9 | **Paradex** | 钱包 + Privy 邮箱/社交 | Privy + Argent | JWT + Starknet 子密钥 | 中 |
| 10 | **Ethereal** | 钱包优先 | Privy + Fun.xyz（未文档化） | EIP-712 逐操作签名 | 低（需充值） |
| 11 | **Nado** | 钱包优先 | 无 | 纯钱包签名 | 低（需先充值） |
| 12 | **StandX** | 钱包 (BSC + Solana) | 无 | JWT via SIWE + ed25519 请求体签名 | 中高 |
| 13 | **MYX Finance** | 钱包 + Particle Network 社交登录 | Particle + Biconomy AA | 仅链上（无 REST 交易 API） | API 方式低 |

## 核心发现

### 内嵌钱包生态

**Privy 出现在 13 个平台中的 7 个** — 往往只能通过 CSP 头分析和 JS 包检测发现，官方文档中并未提及。

第二轮深度探测的重要发现：
- **Ethereal**：发现 Privy + Fun.xyz + MoonPay — 开发者文档中完全未记录
- **Extended**：JS 包中嵌入 Dynamic.xyz — 文档中未提及
- **EdgeX**：通过 CSP 头确认使用 Privy — 文档仅描述了通用的「MPC 邮箱」流程
- **MYX Finance**：技术栈最广泛（Particle + Biconomy + Dynamic + Magic + Safe + WalletConnect + ConnectKit + RainbowKit）

### Web2 用户最友好的平台

1. **GRVT** — 完整 OAuth（邮箱 + Google + Apple + Microsoft）+ Dfns/Privy SecureKey
2. **trade[XYZ]** — Privy 邮箱钱包，摩擦极低
3. **Aster** — 原生邮箱登录 + 钱包创建

### API 最成熟的平台（最快到首单）

1. **Extended** — 测试网完整写入路径已验证（注册 → API Key → 领取资金 → 下单 → 撤单）
2. **StandX** — 类 CEX 的标准 REST + WebSocket API
3. **Hyperliquid** — Agent 钱包模式文档完善

### 首轮与二轮探测差异最大的平台

- **Ethereal**：CSP 头暴露了 Privy + Fun.xyz + MoonPay（开发者文档完全未提及）
- **Extended**：JS 包中发现 Dynamic.xyz，但文档中未记录
- **EdgeX**：通过 CSP 确认 Privy 存在；文档最初仅描述通用「MPC 邮箱」

## 项目结构

```
.
├── README.md
│
├── # ── 研究报告 ──────────────────────────────────
├── perp_dex_complete_report_20260321.md    # 完整报告 97KB（覆盖全部 13 个平台）
├── full_perp_dex_research_20260321.md      # 研究矩阵与详细分析
├── first_pass_platform_probe.md            # 初步发现（Extended、Ethereal、GRVT、EdgeX）
├── institutional_api_benchmark_20260321.md # 机构级 API 性能与可用性基准报告
│
├── # ── 探测脚本 ──────────────────────────────────
├── extended_onboarding_probe.py            # Extended：SDK 账户创建 + API Key 生成
├── extended_write_probe.py                 # Extended：完整写入路径（注册→交易→撤单）
├── hyperliquid_safe_probe.py               # Hyperliquid：SDK 钱包状态 + 签名操作
├── paradex_wallet_probe.mjs                # Paradex：EVM→Starknet 密钥派生 + EIP-712
├── grvt_wallet_login_test.mjs              # GRVT：EIP-712 钱包登录 + Session 捕获
│
├── # ── 探测结果 (JSON) ───────────────────────────
├── # 第一轮结果
├── aster_private_probe_result.json
├── edgex_probe_result.json
├── ethereal_public_probe_result.json
├── extended_onboarding_result.json
├── extended_write_probe_result.json
├── grvt_wallet_login_result.json
├── hyperliquid_safe_probe_result.json
├── lighter_probe_result.json
├── nado_probe_result.json
├── variational_probe_result.json
│
├── # 第二轮结果（深度分析）
├── aster_second_pass_result.json
├── edgex_second_pass_result.json
├── ethereal_second_pass_result.json
├── extended_second_pass_result.json
├── grvt_second_pass_result.json
├── hyperliquid_second_pass_result.json
├── lighter_second_pass_result.json
├── myx_second_pass_result.json
├── nado_second_pass_result.json
├── paradex_second_pass_result.json
├── standx_second_pass_result.json
├── tradexyz_second_pass_result.json
│
├── # ── Paradex 配置产物 ──────────────────────────
├── paradex_testnet_config.json             # Paradex 测试网系统配置
├── paradex_probe_payload.json              # EIP-712 注册签名载荷
│
├── # ── 依赖 ──────────────────────────────────────
├── package.json                            # Node.js 依赖（ethers, starknet）
└── package-lock.json
```

## 机构级 API 基准报告

除了注册摩擦度研究外，本项目还包含一份完整的 **[机构级 API 性能与可用性基准报告](institutional_api_benchmark_20260321.md)**，从量化基金/做市商/Prop Desk 视角评估各平台，覆盖：

- **速率限制对比** — REST/WS 请求上限、权重系统、分级差异
- **订单类型矩阵** — Limit/Market/Stop/TWAP/IOC/FOK/Post-Only/Scale/OCO/OTO
- **批量操作能力** — 批量下单/撤单/一键撤全/批量修改
- **延迟与撮合引擎** — 声称延迟 (2ms ~ 300ms)、吞吐量 (1K ~ 100万 OPS)
- **费率深度对比** — 基础 Maker/Taker、VIP 分级、做市商返佣、专属做市计划
- **子账户架构** — 策略隔离、独立保证金、最大子账户数、API Key 数量
- **WebSocket 能力** — 公共/私有频道、订单簿更新频率 (50ms ~ 500ms)
- **SDK 生态** — Python/TS/Go/Rust 官方与社区 SDK、CCXT 集成
- **杠杆与交易对** — 最大杠杆 (20x ~ 1001x)、交易对数 (3 ~ 500+)
- **综合评分与分级推荐** — Tier 1-4 机构适用性评级

### 机构推荐摘要

| 分级 | 平台 | 核心优势 |
|------|------|---------|
| **Tier 1** | Hyperliquid, Lighter | 最完整 API + Agent 钱包; 0ms Maker 延迟 + ZK 公平撮合 |
| **Tier 2** | GRVT, Paradex, Aster | 全层级返佣 + 期权; 250+ 对 + 零费率; Binance 兼容 API |
| **Tier 3** | Extended, trade[XYZ], EdgeX, Nado, StandX | TradFi 永续; S&P 500 授权; B2B 流动性; 统一保证金 |
| **Tier 4** | Ethereal, MYX, Variational | 仅 3 对/无 REST API/API 未上线 |

## 研究方法论

本研究采用 **两轮探测法**：

### 第一轮 — 文档审查与公开端点探测
- 官方文档审查（GitBook、Notion、GitHub、API 文档）
- 公开 API 端点测试（零认证读取）
- SDK 安装与基础连接测试

### 第二轮 — 深度技术探测
- **CSP 头提取** — 从生产环境前端页面发现隐藏的内嵌钱包提供商
- **JS 包分析** — 检测第三方 SDK（Privy、Dynamic.xyz、Fun.xyz、Particle 等）
- **实时 API 探测** — 带认证与无认证的端点测试
- **SDK 写入路径测试** — 完整的 注册 → 充值 → 交易 → 撤单 全流程
- **OpenAPI/Swagger 规范分析** — 端点枚举与 Schema 验证
- **DNS 解析检查** — 验证遗留/失效端点

## 技术栈

### Node.js (JavaScript/ESM)
- **ethers** v6.16.0 — EVM 钱包操作、EIP-712 类型化数据签名
- **starknet** v9.4.2 — Starknet L2 账户操作
- **@starkware-industries/starkware-crypto-utils** v0.2.1 — 从 EVM 签名派生 Stark 密钥

### Python 3.11
- **Extended SDK** (x10 perpetual) — 账户注册、API Key 创建、交易下单
- **Hyperliquid SDK** — 交易所客户端、钱包签名、市场查询
- **eth_account** / **requests** — EVM 钱包加载、HTTP 探测

## 安装与运行

### 前置条件
- Node.js 18+
- Python 3.11+

### 安装依赖

```bash
# 安装 Node.js 依赖
npm install

# 配置 Extended SDK 的 Python 环境
python3.11 -m venv .pydeps311
source .pydeps311/bin/activate
pip install x10-perpetual eth-account requests

# 配置 Hyperliquid SDK 的 Python 环境
python3.11 -m venv .pydeps_hl
source .pydeps_hl/bin/activate
pip install hyperliquid-python-sdk eth-account
```

### 运行探测脚本

```bash
# Paradex：Starknet 密钥派生 + 注册探测
node paradex_wallet_probe.mjs

# GRVT：钱包登录测试
node grvt_wallet_login_test.mjs

# Extended：完整写入路径测试（需要测试网资金）
source .pydeps311/bin/activate
python extended_write_probe.py

# Hyperliquid：钱包状态 + 安全下单探测
source .pydeps_hl/bin/activate
python hyperliquid_safe_probe.py
```

> **注意：** 大多数写入路径探测需要钱包中有测试网资金。只读探测可直接使用全新钱包运行。

## API 认证模型分类

13 个平台使用四种不同的认证模型：

| 认证模型 | 使用平台 |
|---------|---------|
| **JWT / Session Cookie** | GRVT、StandX |
| **API Key + HMAC** | Aster (Pro API)、Lighter、Extended |
| **原生钱包签名** | Hyperliquid、Nado、Ethereal、trade[XYZ] |
| **L2 密钥派生** | Paradex (Starknet)、EdgeX (自定义 L2) |

## 许可

本研究仅供教育与分析用途。

## 免责声明

- 所有测试均在 **测试网** 或 **公开只读端点** 上进行，零真实资金投入
- 研究过程中未泄露或破解任何私有 API Key 或生产环境凭证
- 研究结果反映的是 **2026-03-21** 的平台状态，各平台后续可能发生变化
- 本研究为独立调研，与所分析的任何平台无关联关系
