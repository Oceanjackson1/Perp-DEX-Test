# Perp DEX 机构级 API 性能与可用性基准报告

**日期：** 2026-03-21
**视角：** 机构交易台 / 做市商 / 量化基金 / Prop Trading Desk
**覆盖平台：** 13 个永续合约去中心化交易所

---

## 一、核心对比矩阵

### 1.1 速率限制对比

| 平台 | REST 请求限制 | 下单速率 | 撤单速率 | WS 连接数 | 备注 |
|------|-------------|---------|---------|----------|------|
| **Hyperliquid** | 1,200 权重/分钟 (IP) | 受权重+地址限制 | 无限制（nonce 作废即可） | 10/IP | 可购买额外权重 (0.0005 USDC/请求) |
| **Lighter** | Standard: 60/分钟; Premium: 24,000 权重/分钟 | Premium: 4,000-40,000 tx/分钟 (质押 LIT 分级) | 不消耗配额 | 100/IP | 双轨制：Standard 免费低速 vs Premium 付费高速 |
| **GRVT** | 市场数据: 1,500/分钟 | 260/10秒 (26/秒) | 2,600/10秒 (260/秒) | Tier 1: 30; Tier 9: 110 | 按交易对分别计算 |
| **Extended** | 1,000-12,000/分钟 (4级) | 受 REST 限制共享 | 支持批量撤单 | 未公开 | Tier 2 需 $50M 交易量 |
| **Paradex** | 1,500/分钟 (IP) | 800/秒 (下单+撤单共享) | 同上 | 20 连接/秒 | 批量=1个限制单位 (50x 效率) |
| **Ethereal** | 未公开 | 未公开 | 未公开 | 未公开 | 文档尚不完善 |
| **Aster** | 2,400 权重/分钟 (IP) | 按账户追踪 | 同上 | 200 流/连接 | Binance 兼容风格 |
| **EdgeX** | 未公开具体数值 | 未公开 | 未公开 | 未公开 | HTTP 429 限流 |
| **Nado** | 未公开 | 未公开 | 未公开 | 5/钱包 | 三层 API 架构 |
| **StandX** | 令牌桶: ~22 req/秒持续 | 同上 | 支持批量撤单 | 10/IP | 50 req/秒 突发 |
| **trade[XYZ]** | 继承 Hyperliquid | 继承 Hyperliquid | 继承 Hyperliquid | 继承 Hyperliquid | 底层即 HL |
| **MYX Finance** | 未公开 | REST API 支持下单 | 不适用 | 无 WebSocket | 有 REST API (api.myx.finance) |
| **Variational** | 不适用 | API 未上线 | API 未上线 | 未上线 | 候补名单中 |

### 1.2 订单类型对比

| 平台 | Limit | Market | Stop | TP/SL | TWAP | IOC | FOK | Post-Only | 冰山单 | OCO/OTO | Scale |
|------|-------|--------|------|-------|------|-----|-----|-----------|--------|---------|-------|
| **Hyperliquid** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ (ALO) | ❌ | ❌ | ✅ |
| **Lighter** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **GRVT** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Extended** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Paradex** | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Ethereal** | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Aster** | ✅ | ✅ | ✅ | ✅ | 🔜 | ✅ | ✅ | ✅ (GTX) | ❌ | ❌ | ❌ |
| **EdgeX** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Nado** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | 🔜 |
| **StandX** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ (ALO) | ❌ | ❌ | ❌ |
| **trade[XYZ]** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| **MYX Finance** | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Variational** | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### 1.3 批量操作能力

| 平台 | 批量下单 | 批量撤单 | 一键撤全 | 批量修改 | 备注 |
|------|---------|---------|---------|---------|------|
| **Hyperliquid** | ✅ 数组式 | ✅ 数组式 + cloid | ✅ scheduleCancel (死人开关) | ✅ batchModify | 最完整；nonce 作废可替代撤单 |
| **Lighter** | ✅ sendTxBatch (50笔/批) | ✅ L2CancelAllOrders | ✅ | ✅ L2ModifyOrder | GroupedOrders 消耗 1 配额单位 |
| **GRVT** | ❌ 无批量下单 | ✅ cancel_all_orders | ✅ | ❌ | 高速率弥补（26单/秒） |
| **Extended** | ❌ | ✅ mass_cancel | ❌ 未确认 | ❌ | |
| **Paradex** | ✅ 1-50单/批 | ✅ 1-50单/批 | ❌ 未确认 | ❌ | 批量=1个限制单位，50x 效率 |
| **Ethereal** | ❌ 未文档化 | ❌ | ❌ | ❌ | |
| **Aster** | ✅ Binance 式 batchOrders | ✅ | ✅ | ❌ | |
| **EdgeX** | ❌ 未确认 | ❌ 未确认 | ❌ | ❌ | |
| **Nado** | ❌ 未确认 | ❌ 未确认 | ❌ | ❌ | |
| **StandX** | ❌ | ✅ cancel_orders | ❌ | ❌ | |
| **trade[XYZ]** | ✅ (继承 HL) | ✅ (继承 HL) | ✅ | ✅ | |
| **MYX Finance** | ✅ Multicall 合约 | ✅ 批量减仓 | ❌ | ❌ | 链上操作 |
| **Variational** | ❌ | ❌ | ❌ | ❌ | API 未上线 |

---

## 二、费率结构深度对比

### 2.1 基础 Maker/Taker 费率

| 平台 | 基础 Maker | 基础 Taker | 最优 Maker | 最优 Taker | 达到最优条件 |
|------|-----------|-----------|-----------|-----------|------------|
| **Lighter** | 0% (Standard) | 0% (Standard) | 0.0028% (Premium) | 0.0196% (Premium) | Standard 完全免费 |
| **Paradex** | 0% | 0% (零费率永续) | 0% | 0% (零费) | 零售 UI 交易 |
| **GRVT** | **-0.0001%** 返佣 | 0.045% | **-0.003%** 返佣 | 0.024% | $1B 30日交易量 |
| **Hyperliquid** | 0.015% | 0.045% | **-0.003%** 返佣 | 0.024% | $7B+ 交易量 + 做市份额 |
| **Extended** | 0% | 0.025% | 0% | 0.025% | 无分级费率 |
| **Ethereal** | 0% | 0.03% | 0% | 0.03% | 无 VIP 分级 |
| **Nado** | 0.01% | 0.035% | **-0.008%** 返佣 | 0.015% | $5B 30日交易量 |
| **Aster** | 0.01% | 0.035% | 0% | — | $1B+ 交易量 |
| **EdgeX** | 0.015% | 0.038% | 0% | 0.026% | $1B+ 交易量 |
| **StandX** | 0.01% | 0.04% | **-0.05%** 返佣 | 0.02% | MM2 做市计划 |
| **trade[XYZ]** | 0.030% | 0.090% | 0% | 0.048% | Hyperliquid VIP6 + 2x |
| **MYX Finance** | 0.045% | 0.055% | **-0.01%** 返佣 | 0.018% | $1B 30日量 或 1M MYX |
| **Variational** | 0% | 0% | 0% | 0% | 零费率（价差模型） |

### 2.2 做市商计划

| 平台 | 做市商计划 | 核心激励 |
|------|-----------|---------|
| **Hyperliquid** | ❌ 明确无 DMM | 共识层优先处理撤单/Post-Only；做市份额返佣最高 -0.003% |
| **Lighter** | ✅ Premium 账户体系 | 0ms Maker 延迟、独立速率桶、质押 LIT 解锁更高限制 |
| **GRVT** | ✅ 全层级 Maker 返佣 | 从 Tier 1 起即有 -0.0001% 返佣 |
| **Aster** | ✅ 专属做市计划 | 月度 300,000 USDT ASTER 奖池 |
| **StandX** | ✅ MM Uptime Program | 月度 500万 StandX 代币；基于在线时长 + 价差质量 |
| **Nado** | ✅ NLP 计划 | 机构交易者代表流动性池做市 |
| **其他** | ❌ 无专属计划 | — |

---

## 三、延迟与撮合引擎

| 平台 | 撮合引擎吞吐量 | 声称延迟 | Maker 延迟 | Taker 延迟 | 架构 |
|------|--------------|---------|-----------|-----------|------|
| **Ethereal** | **100万+单/秒** | **<20ms** | — | — | 应用专属定序器 (L3 on Converge) |
| **GRVT** | **60万笔/秒** | **~2ms** | — | — | 链下订单簿 + zkSync ZK Stack L3 Validium |
| **Lighter** | 未公开 | — | **0ms** (Premium) | **140-300ms** | 价格-时间优先 + SNARK 证明 |
| **EdgeX** | **20万单/秒** | **<10ms** | — | — | StarkEx ZK-Rollup |
| **Hyperliquid** | **20万单/秒** (理论 200万) | **~200ms** (中位) | ~200ms | ~200ms | HyperBFT 共识 (自有 L1) |
| **Nado** | 未公开 | **5-15ms** | — | — | CLOB on Ink L2 |
| **Paradex** | **1,000 TPS** | 2-3秒终局 | — | — | Starknet Appchain |
| **Extended** | 未公开 | 未公开 | — | — | 链下撮合 + Starknet 结算 (AWS 东京) |
| **Aster** | 未公开 | 毫秒级 (声称) | — | — | PoSA 共识 + 预确认 |
| **StandX** | 未公开 | 未公开 | — | — | 币安期货创始团队自研引擎 |
| **trade[XYZ]** | 继承 Hyperliquid | ~200ms | — | — | HyperBFT |
| **MYX Finance** | 不适用 | 取决于链 (250ms-3s) | — | — | Keeper 执行，非订单簿 |
| **Variational** | 不适用 | 取决于做市商响应 | — | — | RFQ 模型 |

**关键洞察：**
- **GRVT** 声称 2ms 延迟 + 60万 TPS，在所有 DEX 中最激进
- **Lighter** 的 0ms Maker 延迟对做市商极有吸引力（无速度碰撞）
- **Ethereal** 声称百万级 OPS，但仅 3 个交易对，实际验证有限
- **Hyperliquid** 的 200ms 是 DEX 级别，非 CEX 级别，但可通过自建节点降至 <20ms

---

## 四、子账户与多策略架构

| 平台 | 最大子账户数 | 策略隔离 | 独立保证金 | API Key 数量 | 保证金模式 |
|------|------------|---------|-----------|-------------|-----------|
| **EdgeX** | **20** | ✅ 完全隔离清算 | ✅ 逐仓/全仓 | 未公开 | 全仓 + 逐仓 |
| **Lighter** | 多个 (共享配额) | ✅ | ✅ | **253/账户** | 统一交易账户 (UTA) |
| **Hyperliquid** | **10** | ✅ 独立持仓/保证金 | ✅ | 主: 4; 子: 2/个 | 标准/统一/组合保证金 |
| **Extended** | **10** | ✅ 每子账户独立 Stark Key | ✅ | 每子账户独立 | 全仓 |
| **GRVT** | 多个 (Funding→Trading) | ✅ | ✅ | **5/Funding + 5/Trading** | 全仓 |
| **Paradex** | 多个 (隔离清算) | ✅ | ✅ | 未公开 | 全仓 |
| **Nado** | 多个 (池化子账户) | ✅ | ✅ 统一全仓 | — | 全仓 |
| **trade[XYZ]** | 10 (继承 HL) | ✅ | ✅ | 继承 HL | 继承 HL |
| **Aster** | ❌ 未确认 | — | — | 30/账户 | 全仓 + 逐仓 |
| **StandX** | ❌ 未文档化 | — | — | — | Cash + Perps 双钱包 |
| **Ethereal** | 未明确 | 暗示支持 | — | — | — |
| **MYX Finance** | ❌ | — | — | — | 逐仓 |
| **Variational** | ❌ | — | — | — | — |

---

## 五、WebSocket 能力对比

| 平台 | 公共频道 | 私有频道 | 订单簿更新频率 | 协议 | 压缩 |
|------|---------|---------|--------------|------|------|
| **Hyperliquid** | 7+ (allMids, l2Book, trades, bbo, candle, activeAssetCtx 等) | 15+ (orderUpdates, userEvents, userFills, clearinghouseState 等) | ~500ms | 原生 WS | — |
| **Lighter** | 6 (order_book, ticker, market_stats, trade, height, spot_market_stats) | 10+ (account_all, account_orders, account_trades, user_stats, notification 等) | **50ms** | 原生 WS | permessage-deflate |
| **GRVT** | 4+ (ticker, order_book, trade, mini_ticker) | 4+ (order_state, cancel_status, private_trades, positions) | 可配置 | 原生 WS | — |
| **Aster** | 4+ (kline, depth, trades, ticker) | UserData Stream (via listenKey) | **100ms** 或 1s | 原生 WS | — |
| **Paradex** | 4 (order_book, trades, markets_summary, funding_data) | orders (JSON-RPC) | **50ms/100ms** | JSON-RPC WS | — |
| **Nado** | 订单簿、交易 | 认证后自动推送 | **~50ms** | 原生 WS | permessage-deflate |
| **StandX** | 3 (price, depth_book, public_trade) | 4 (order, position, balance, trade) | 未公开 | 原生 WS | — |
| **EdgeX** | 2 (ticker, orderbook) | 12+ 事件类型 (自动推送) | 未公开 | 原生 WS | — |
| **Extended** | 6 (orderbook, trades, funding, candles, mark_price, index_price) | 1 (account_updates) | 未公开 | 原生 WS | — |
| **Ethereal** | 有限文档 | 3 (ORDER_FILL, ORDER_UPDATE, TOKEN_TRANSFER) | — | 原生 WS v2 (主要) + Socket.IO (已废弃) | — |
| **trade[XYZ]** | 继承 Hyperliquid | 继承 Hyperliquid | ~500ms | 继承 HL | — |
| **MYX Finance** | ❌ 无 WebSocket | ❌ | — | — | — |
| **Variational** | ❌ 未上线 | ❌ | — | — | — |

---

## 六、SDK 生态系统

| 平台 | Python | TypeScript/JS | Go | Rust | 其他 | CCXT |
|------|--------|-------------|-----|------|------|------|
| **Hyperliquid** | ✅ 官方 | ✅ 社区 (2个) | ❌ | ✅ 社区 | Elixir | ✅ |
| **Lighter** | ✅ 官方 | ❌ | ✅ 官方 | ❌ | — | ❌ (已请求) |
| **GRVT** | ✅ 官方 (pre-1.0) | ✅ 官方 (v0.0.4) + 社区 | ❌ | ❌ | — | ✅ 兼容接口 |
| **Extended** | ✅ 官方 | ❌ | ✅ 官方 | ❌ | Rust 加密库 | ❌ |
| **Paradex** | ✅ 官方 | ❌ | ❌ | ❌ | — | ❌ |
| **Ethereal** | ✅ 官方 (早期) | ✅ 示例 | ❌ | ❌ | — | ❌ |
| **Aster** | ✅ 示例 | ✅ 官方 npm | ✅ 示例 | ❌ | Agent Skills Hub | ❌ |
| **Nado** | ✅ 官方 | ✅ 官方 (monorepo) | ❌ | ✅ 官方 | — | ❌ |
| **EdgeX** | ❌ | ❌ | ❌ | ❌ | B2B API | ❌ |
| **StandX** | ❌ | ❌ (仅示例) | ❌ | ❌ | — | ❌ |
| **trade[XYZ]** | ✅ (via HL) | ✅ (via HL) | ❌ | ✅ (via HL) | — | ✅ (via HL) |
| **MYX Finance** | ❌ | ❌ | ❌ | ❌ | 智能合约 ABI | ❌ |
| **Variational** | ✅ 示例 | ❌ | ❌ | ❌ | — | ❌ |

---

## 七、杠杆、交易对与仓位规模

| 平台 | 最大杠杆 | 永续交易对数 | 资产类型 | 最大仓位 | 抵押品 |
|------|---------|------------|---------|---------|--------|
| **Aster** | **1,001x** | ~96 | 加密 + 美股 (AAPL 等) | 未公开 | 多抵押品 |
| **MYX Finance** | **50x** | ~13+ | 加密 | 未公开 | USDC |
| **EdgeX** | **100x** | 100+ | 加密 | 未公开 | USDC |
| **Extended** | **100x** | 121+ | 加密 + TradFi (EUR/USD, XAU, S&P500, 原油) | 未公开 | USDC |
| **StandX** | **100x** | 4+ | 加密 + 黄金/白银 | 未公开 | DUSD (生息稳定币) |
| **Lighter** | **50x** (BTC/ETH) | ~80+ | 加密 + 外汇 + 商品 (XAU, XAG) | 事实上无限 (OI 限制) | USDC |
| **Paradex** | **50x** | **250+** | 加密 + 永续期权 + 现货 | 未公开 | USDC |
| **Hyperliquid** | **50x** (部分新对50x) | **~313** | 加密 + S&P 500 + 美股 | BTC ≥25x: $15M | USDC |
| **Variational** | **50x** | **500+** | 加密 + 波动率 + RWA + 预测市场 | 未公开 | USDC |
| **GRVT** | **50x** | ~96 | 加密 + 期权 | 未公开 | USDT |
| **Nado** | **40x** | 30+ | 加密 + TradFi | 未公开 | USDT0 |
| **trade[XYZ]** | ~50x (继承 HL) | 数百 + TradFi | 加密 + S&P 500 (授权) + 黄金/白银 | 继承 HL | USDC |
| **Ethereal** | **20x** (BTC/ETH) | **15+** | 加密 (BTC, ETH, SOL 等) | BTC/ETH: $2.5M; SOL: $500K | USDe |

---

## 八、独特机构级功能

### 8.1 值得关注的差异化功能

| 平台 | 独特功能 | 机构价值 |
|------|---------|---------|
| **Hyperliquid** | Agent 钱包 (不暴露主钱包)、Builder Codes (前端/聚合器赚手续费)、共识层优先处理 Maker 订单、自建节点 (<20ms)、死人开关 | 最成熟的去中心化做市基础设施 |
| **Lighter** | 0ms Maker 延迟 (无速度碰撞)、ZK 证明验证撮合公平性、253 可编程 API Key/账户 (索引 2-254)、免费 Standard 账户 + 付费 Premium 双轨制 | 唯一对 HFT 做出明确承诺的 DEX |
| **GRVT** | 全层级 Maker 返佣、RFQ 大宗交易、期权合约、Dfns MPC 企业级托管、Business Account (多用户+角色权限) | 最接近传统金融机构架构 |
| **Extended** | TradFi 永续 (EUR/USD, 原油, S&P500)、AWS 东京托管推荐、100x 杠杆 | TradFi 资产覆盖最广 |
| **Paradex** | 零费率永续 (零售)、永续期权、250+ 交易对、批量下单 50 单/批 (1 限制单位)、Starknet 隐私 | 交易对数 + 期权 + 零费率三重优势 |
| **Ethereal** | USDe 生息抵押品、OTO/OCO 组合订单、FOK 订单、声称 <20ms + 100万 OPS | 如果兑现承诺，延迟性能最优 |
| **Aster** | Binance 兼容 API、Hidden 订单、1001x 杠杆、美股永续 (AAPL/NVDA 等)、做市计划 (30万 USDT/月) | Binance 生态迁移最简单 |
| **EdgeX** | Amber Group 孵化、200K OPS 引擎、B2B 流动性 API、混合跨链流动性层 | 机构流动性基础设施 |
| **Nado** | 统一交易栈 (现货+保证金+永续)、现货可计入组合保证金、NLP 机构做市计划、3 语言官方 SDK | 现货/永续统一保证金唯一 |
| **StandX** | DUSD 生息稳定币保证金、MM Uptime Program (500万代币/月)、币安期货创始团队 | 交易同时赚取抵押品收益 |
| **trade[XYZ]** | 授权 S&P 500 永续 (S&P Dow Jones 官方授权)、TradFi 资产先驱 | 唯一获得传统指数官方授权的 DEX |

### 8.2 FIX Protocol 支持

**所有 13 个平台均不支持 FIX Protocol。** 这是 DEX 生态与传统 CEX/TradFi 的一个重要差距。

---

## 九、机构综合评分

基于以下维度加权评估（满分 10 分）：

| 平台 | API 成熟度 | 速率/吞吐 | 订单类型 | 费率竞争力 | 子账户 | SDK | 延迟 | 综合评分 |
|------|-----------|----------|---------|-----------|--------|-----|------|---------|
| **Hyperliquid** | 9 | 8 | 9 | 8 | 7 | 8 | 6 | **8.2** |
| **Lighter** | 8 | 9 | 8 | 9 | 8 | 7 | 8 | **8.1** |
| **GRVT** | 7 | 8 | 7 | 9 | 8 | 6 | 9 | **7.7** |
| **Paradex** | 8 | 8 | 7 | 10 | 7 | 6 | 6 | **7.5** |
| **Aster** | 8 | 7 | 8 | 7 | 4 | 8 | 5 | **7.0** |
| **Extended** | 7 | 6 | 8 | 7 | 7 | 7 | 5 | **6.7** |
| **EdgeX** | 6 | 8 | 7 | 7 | 8 | 3 | 8 | **6.5** |
| **Nado** | 6 | 5 | 7 | 7 | 6 | 8 | 7 | **6.4** |
| **StandX** | 6 | 6 | 6 | 7 | 3 | 3 | 5 | **5.3** |
| **trade[XYZ]** | 7 | 8 | 9 | 5 | 7 | 8 | 6 | **7.0** |
| **Ethereal** | 4 | 5* | 8 | 6 | 3 | 4 | 5* | **4.5** |
| **MYX Finance** | 4 | 2 | 4 | 6 | 1 | 2 | 2 | **3.2** |
| **Variational** | 1 | 1 | 3 | 10 | 1 | 2 | 1 | **2.0** |

*Ethereal 延迟/吞吐基于平台声称值（<20ms、100万 OPS），实测 REST p50=135ms，WS 测试未收到数据，声称延迟完全未经独立验证

---

## 十、机构级推荐

### Tier 1 — 推荐 (综合最强)

#### Hyperliquid
- **优势：** 最完整的批量操作、TWAP/Scale 订单、Agent 钱包安全模型、313+ 交易对、共识层 Maker 优先
- **劣势：** 200ms 延迟（需自建节点才能降至 <20ms）、无 FIX、仅 10 子账户
- **适合：** 量化基金、算法交易、做市商（自建节点后）

#### Lighter
- **优势：** 0ms Maker 延迟、ZK 证明公平撮合、253 可编程 API Key/账户、Standard 免费 + Premium 分级
- **劣势：** SDK 仅 Python/Go、无 CCXT、社区较小
- **适合：** HFT 做市商、低延迟策略、需要可证明公平性的机构

### Tier 2 — 可用 (各有亮点)

#### GRVT
- **优势：** 全层级 Maker 返佣、60万 TPS + 2ms 延迟、RFQ 大宗、期权、企业账户
- **劣势：** SDK pre-1.0、无批量下单、需 KYC
- **适合：** 合规机构、期权策略、大宗交易

#### Paradex
- **优势：** 250+ 交易对、零费率零售、批量 50 单/批、永续期权
- **劣势：** 2-3秒终局延迟、无 TWAP
- **适合：** 多市场覆盖策略、期权做市

#### Aster
- **优势：** Binance 兼容 API（迁移成本低）、美股永续、做市计划、多语言 SDK
- **劣势：** 子账户缺失、TWAP 尚未上线
- **适合：** 从 Binance 迁移的交易团队、美股永续策略

### Tier 3 — 特定场景

| 平台 | 适用场景 |
|------|---------|
| **Extended** | TradFi 永续 (外汇/商品/指数)、100x 杠杆需求 |
| **trade[XYZ]** | S&P 500 授权永续、TradFi-on-Hyperliquid |
| **EdgeX** | Amber Group 生态、B2B 流动性接入 |
| **Nado** | 统一现货/保证金/永续保证金账户 |
| **StandX** | 生息抵押品 (DUSD)、做市商代币激励 |

### Tier 4 — 不推荐 (机构级不达标)

| 平台 | 原因 |
|------|------|
| **Ethereal** | 15+ 交易对但 20x 最大杠杆、文档不完善、声称延迟 (<20ms) 完全未经验证（实测 REST p50=135ms） |
| **MYX Finance** | REST API 存在 (api.myx.finance) 但无 WebSocket；50x 最大杠杆（非 125x，125x 为资本效率） |
| **Variational** | API 未上线、RFQ 模型（非订单簿）、500+ 市场但无法程序化交易 |

---

## 附录：数据来源

### 官方文档
- Hyperliquid: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
- Lighter: https://apidocs.lighter.xyz
- GRVT: https://api-docs.grvt.io
- Extended: https://api.docs.extended.exchange
- Paradex: https://docs.paradex.trade
- Ethereal: https://docs.ethereal.trade
- Aster: https://docs.asterdex.com
- EdgeX: https://edgex-1.gitbook.io/edgeX-documentation
- Nado: https://docs.nado.xyz
- StandX: https://docs.standx.com
- MYX Finance: https://myxfinance.gitbook.io/myx
- Variational: https://docs.variational.io

### 费率页面
- Hyperliquid: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
- Lighter: https://docs.lighter.xyz/trading/trading-fees
- GRVT: https://help.grvt.io/en/articles/9614699-how-does-grvt-s-fee-model-work
- Aster: https://docs.asterdex.com/product/aster-perpetuals/fees-and-specs/fees
- EdgeX: https://edgex-1.gitbook.io/edgeX-documentation/trading/trading-fees
- Nado: https://docs.nado.xyz/fees-and-rebates
- StandX: https://docs.standx.com/docs/stand-x-perps-solutions/trading-fee
- MYX Finance: https://myxfinance.gitbook.io/myx/protocol/trading-costs
- Variational: https://docs.variational.io/omni/trading/fees

---

## 勘误记录 (2026-03-23 审查后修正)

经 70+ 项事实核查后，修正以下错误：

| # | 平台 | 原始声称 | 修正后 | 严重度 |
|---|------|---------|--------|--------|
| 1 | **StandX** | ~46 个交易对 | **4+ 个** (BTC, ETH, XAU, XAG 经 API 确认) | 严重 |
| 2 | **MYX Finance** | 最大杠杆 125x | **50x** (125x 是 MPM 资本效率，非交易杠杆) | 严重 |
| 3 | **MYX Finance** | 无 REST 交易 API | **有 REST API** (api.myx.finance 支持下单) | 严重 |
| 4 | **Ethereal** | 仅 3 个交易对 | **15+ 个主网产品** (API 确认) | 中等 |
| 5 | **Extended** | 50+ 交易对 | **121+ 个** (API 确认) | 中等 |
| 6 | **Lighter** | sendTxBatch 最多 15 笔 | **50 笔** (官方 API 文档) | 中等 |
| 7 | **Lighter** | 255 API Key/账户 | **253 可编程 Key** (索引 0-1 保留 UI，255 为查询) | 轻微 |
| 8 | **Ethereal** | WebSocket 使用 Socket.IO | **原生 WS v2 为主**，Socket.IO 已废弃 | 中等 |
| 9 | **Ethereal** | 延迟评分 9 分 | **降至 5 分** (声称未经验证，实测 REST p50=135ms) | 中等 |
| 10 | **Nado** | NLP = Nado Liquidity Program | **NLP = Nado Liquidity Provider** (零售 LP 金库) | 轻微 |
