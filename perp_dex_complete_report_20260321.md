# Comprehensive Perp DEX Research Report

## Part 1: Executive Summary & Methodology

**Date:** 2026-03-21

**Wallet under test:** `0x41Deec4e76e46c18719E90920C1efef370B7DB0A` (fresh EVM wallet, zero real funds)

**Mode:** Testnet / zero real funds where possible

**Platforms covered:** 13

1. Hyperliquid
2. Aster
3. trade[XYZ]
4. EdgeX
5. Variational
6. Lighter
7. GRVT
8. Extended
9. Paradex
10. Ethereal
11. Nado
12. StandX
13. MYX Finance

**Methodology:**

- Official documentation review (GitBook, Notion, GitHub, API docs)
- CSP (Content Security Policy) header extraction from live production frontends
- Runtime JS bundle analysis (vendor SDK detection, environment variable extraction)
- Live API probes (curl-based, zero-auth and auth-probing)
- Local SDK probes (Python, Node.js) with the test wallet
- OpenAPI/Swagger spec analysis where available
- Web search for team, funding, and product context
- DNS resolution checks for legacy/stale endpoints

---

## Part 2: Core Findings (Systematic Insights)

### 1. Embedded Wallet Landscape

Privy appears in **7 of 13** platforms:

| Platform | Privy | Other Embedded Wallet Infra |
|---|---|---|
| Paradex | Yes (CSP, docs) | Argent, Ready.co |
| Hyperliquid | Yes (docs, support) | -- |
| trade[XYZ] | Yes (CSP) | -- |
| EdgeX | Yes (CSP, JS bundle) | -- |
| GRVT | Yes (email OTP layer) | Dfns (MPC/WebAuthn) |
| Ethereal | Yes (CSP frame-src) | Fun.xyz (wallet SDK), MoonPay (fiat) |
| Extended | No | Dynamic.xyz (JS bundle) |
| MYX Finance | No | Particle Network, Dynamic.xyz, Magic.link, Biconomy, Safe |
| Aster | No | Email login (native) |
| StandX | No | None found |
| Lighter | No | None found |
| Nado | No | None found |
| Variational | No | None found |

**Key insight:** The first-pass analysis missed embedded wallet infrastructure in **Ethereal**, **Extended**, and **EdgeX** because it only checked official documentation. CSP headers and JS bundle analysis revealed the truth:

- **Ethereal:** `auth.privy.io` in CSP `frame-src`, `funkit` (Fun.xyz) in HTML source, `MoonPay` APIs in `connect-src` -- none documented in developer guides.
- **Extended:** `dynamicEnvironmentId` and `dynamicauth` in the 1.77MB JS bundle -- Dynamic.xyz (a Privy competitor) supporting email/social/embedded wallets, but not yet surfaced in docs or UI.
- **EdgeX:** `auth.privy.io` in CSP `script-src` and `connect-src`, plus a `lib-privy` JS bundle -- docs only described a generic "MPC email" flow.

**GRVT's dual infrastructure** is the most sophisticated: Dfns provides the actual MPC wallet layer (WebAuthn passkeys, backup codes, credentials management), while Privy handles the email OTP authentication frontend. The testnet env config confirms both `DFNS_APP_ID` and `PRIVY_APP_ID` are active with `DFNS_PRIVY_ENABLE=1`.

**MYX Finance** has the broadest wallet infrastructure stack in the entire sample: Particle Network + Biconomy + Dynamic.xyz + Magic.link + Safe + WalletConnect + ConnectKit + RainbowKit, with EIP-4337 and EIP-7702 references for account abstraction.

### 2. API Auth Model Taxonomy

All 13 platforms categorized by their authentication patterns:

**JWT / session cookie:**
- **GRVT** -- EIP-712 wallet login or API key login, both return session cookies. 5 keys max per Trading Account, each tagged to an Ethereum address.
- **StandX** -- JWT via wallet signature (SIWE + ed25519 key pair). Body signature (ed25519) required for write operations.

**API key + HMAC:**
- **Aster (Pro API)** -- `X-MBX-APIKEY` header + HMAC SHA256 signatures. Up to 30 API keys per account. Standard CEX-like model.

**API key + Stark signature:**
- **Extended** -- API key for read-only access (`X-Api-Key` header), API key + SNIP12/EIP-712 Stark signature for writes. Per sub-account keys, up to 10 accounts per wallet.

**EIP-712 per-action signing (no API keys):**
- **Ethereal** -- 8 distinct signed action types (LinkSigner, TradeOrder, CancelOrder, InitiateWithdraw, etc.). No JWT or API key alternative. 49 REST endpoints.
- **Nado** -- Pure wallet signatures. No API keys, no username/password. Linked signers optional (1-Click Trading).

**Raw wallet signing:**
- **Hyperliquid** -- Direct wallet signing or approved API/agent wallets. Agent wallets sign on behalf of master account.

**JWT via wallet signature + body signature:**
- **StandX** -- Two-layer: JWT for session auth, ed25519 body signature for write operations.

**On-chain only (no REST trading API):**
- **MYX Finance** -- Only 2 public REST endpoints (market data). All trading via smart contract calls (Router.sol) or Seamless Key (on-chain delegated signer).
- **Variational** -- Current live API is read-only Omni stats. Trading API explicitly "still in development."

**Dependent on upstream:**
- **trade[XYZ]** -- Uses Hyperliquid API directly. Mainnet: `api.hyperliquid.xyz`, testnet: `api.hyperliquid-testnet.xyz`. Passes `type: perpDexs` for XYZ markets.

**Multi-layer (API key + passphrase + L2 signature):**
- **EdgeX** -- Private API gateway enforces `X-edgeX-Api-Key` + `X-edgeX-Passphrase` + `X-edgeX-Signature` + `X-edgeX-Timestamp`. Separate L2 private key / `l2Signature` for order actions (Pedersen hash + ECDSA).

**Dual-track (direct API + delegated builder):**
- **Aster** -- Pro API for direct traders (HMAC) AND Aster Code for builder/agent delegation (separate `/fapi/v3/` endpoints with per-user signer keys).

**Multi-credential (JWT + subkeys + readonly tokens):**
- **Paradex** -- JWT tokens, main private key for full access, subkeys for trading-only, readonly tokens for long-lived GET-only. EVM SIWE v2 onboarding + Starknet L2 key trading.

**Deposit-first + API key + auth token + nonce:**
- **Lighter** -- Account created by credited deposit. Then API key (indices 2-254), auth token generation, per-key nonce management. Standard vs Premium tiers with different rate limits.

### 3. Cold Wallet Friction Spectrum

Ranking all 13 platforms from easiest to hardest for a fresh wallet to place a first API order:

| Rank | Platform | Difficulty | Blocker |
|---|---|---|---|
| 1 | Extended (testnet) | Low | Onboard + API key + Stark sig -- all scriptable, proved end-to-end |
| 2 | StandX | Medium | Wallet sign + JWT + DUSD deposit + transfer to Perps wallet |
| 3 | Hyperliquid | Medium | Enable Trading + deposit/activation + agent wallet setup |
| 4 | Paradex | Medium | Min chain balance (0.001 ETH or 5 USDC) + onboarding + L2 key derivation |
| 5 | Aster | Medium | Onboard + deposit + UI API key creation + HMAC signing |
| 6 | trade[XYZ] | Medium | Privy smooths frontend, but same Hyperliquid activation underneath |
| 7 | Lighter | Medium-High | Deposit + wait for crediting + account_index + API key association + auth token |
| 8 | Nado | Medium-High | First deposit creates subaccount, then wallet signing for every action |
| 9 | Ethereal | High | Discord request for testnet funds + deposit + subaccount + EIP-712 per action |
| 10 | EdgeX | High | API key + passphrase + signature + timestamp + separate L2 key + l2Signature |
| 11 | GRVT | High | Web2 account + KYC + SecureKey + Trading Account + Fund + API Key + Signer tag |
| 12 | MYX Finance | N/A | No REST trading API; must call smart contracts directly |
| 13 | Variational | N/A | Trading API not yet available; read-only stats only |

### 4. Web2 vs API-First Trade-off

The fundamental split across this sample: platforms optimize for one or the other, rarely both.

**Web2-first platforms** (smoothest onboarding, highest initialization friction for API):
- MYX Finance: Particle Network social login + Seamless Key + credit card USDC -- but zero REST trading API
- GRVT: email + Google + Apple + Microsoft OAuth + Dfns+Privy -- but 7-step initialization chain for API
- trade[XYZ]: Privy email wallet as "fastest option" -- but inherits Hyperliquid's activation constraints

**API-first platforms** (fastest to programmatic trading, minimal Web2 concessions):
- Extended: Full write-path proved in first-pass, Dynamic.xyz in bundle but not surfaced
- StandX: Clean CEX-like REST+WS API, but wallet-only login
- Lighter: Mature API key + auth token stack, but deposit-first and no email login

**Balanced (attempting both):**
- Paradex: Privy email/social + JWT/subkey API model -- but cold wallet still gated
- Hyperliquid: Privy email + agent wallets -- but activation/deposit required for writes
- Aster: Email login + dual Pro API / Aster Code tracks -- still needs UI API key creation

---

## Part 3: Platform Matrix Table

| Platform | Login / user onboarding | Embedded / AA-like path | API auth & order path | Fresh wallet -> API first order | Live evidence |
| --- | --- | --- | --- | --- | --- |
| Hyperliquid | Official docs support normal wallet or email login | Yes; email login is explicitly supported, support docs tie it to `Privy`, and the email wallet can be exported into a normal wallet extension | Raw wallet signing or approved API wallet / agent wallet | Medium-low from a cold test wallet; public/read path is queryable immediately, but official docs still require `Enable Trading` plus funded/activated HyperCore state before signed write actions work cleanly | Mainnet + testnet `info/meta` live; fresh wallet still returns zeroed read state, but signed `noop` and `market_open` again failed with `User or API Wallet does not exist`; official docs say testnet faucet needs same-address mainnet deposit and unactivated accounts cannot send `CoreWriter` actions |
| Aster | Wallet login and official email login guides both exist | Email login creates a new blockchain address tied to email | Two private paths: standard Pro API uses self-serve API keys + HMAC SHA256 for direct trading, while separate `Aster Code` builder/agent endpoints support delegated execution | Medium; a fresh wallet still needs onboarding, deposit, and UI-side API key creation, but direct trader access is materially simpler than the first-pass builder-only framing | `/fapi/v1/ping`, `/fapi/v1/time`, `/fapi/v1/exchangeInfo` live; official API pages say each account can create up to 30 API keys; `Aster Code` `/fapi/v3/agent` and `/fapi/v3/builder` remain separately signature-gated |
| trade[XYZ] | Existing wallet or Privy email wallet | Privy email wallet is explicit | Uses Hyperliquid API directly for XYZ markets, including `type: perpDexs` routing for XYZ assets | Medium; Privy smooths onboarding, but connected-wallet users still need deposit and sometimes `Enable Trading`, so the same Hyperliquid activation/deposit constraints likely apply underneath | Homepage live; CSP connect-src exposes `auth.privy.io` and `api-ui.hyperliquid.xyz`; official API docs point directly to Hyperliquid mainnet/testnet endpoints |
| EdgeX | Standard wallet or email MPC login | Email-based MPC wallet is explicit | Two-layer auth stack: private REST auth headers plus separate L2 private key / `l2Signature` for order actions | Low from raw wallet alone; specialized setup | Public funding endpoint live; private API gateway currently enforces `Api-Key -> Passphrase -> Signature`, and even `registerAccount` is behind the same private header gate |
| Variational | Wallet-first Omni flow; current live app is Omni, while Pro is not live | No embedded wallet evidence found; gasless deposits reduce friction but do not create an embedded wallet path | Current live API is read-only Omni stats; trading API still unavailable; old Pro/API-key docs and hosts now look archival | Effectively unavailable today for `fresh wallet -> API first order` | Omni mainnet/testnet apps and stats endpoint live; current docs say trading API is still in development and Pro is not live; legacy auth/setup doc URLs now 404 and old `api.*` / `pro.testnet.*` hostnames do not resolve |
| Lighter | Ethereum wallet plus deposit-backed account creation | No embedded wallet evidence found | API key per account/subaccount + auth token + nonce model | Low; programmatic account creation requires credited deposit first, then account index lookup, then API key setup | `orderBookDetails` live; wallet lookup returned `account not found`, but `createIntentAddress` already worked for the same fresh wallet, confirming deposit is the real first programmatic step |
| GRVT | Explicit `Web2 account + SecureKey + account structure` model; Web2 login includes email + Google + Apple + Microsoft OAuth | Strongest embedded path in sample: GRVT Native SecureKey powered by `Dfns` (MPC/WebAuthn/passkeys/backup codes) + `Privy` (email OTP auth layer) -- a dual-infrastructure composite, not Privy alone | Session-cookie auth via API key or EIP-712 wallet login; 5 keys max per Funding/Trading Account; each key tagged to an Ethereum address | Low from a fresh wallet; only becomes medium after registered SecureKey plus funding/trading-account initialization; KYC is now required (`NEW_KYC_ENABLE=1`) | Live wallet login still returns `401 wallet address not registered`; testnet env config confirms `DFNS_PRIVY_ENABLE=1` with both `PRIVY_APP_ID` and `DFNS_APP_ID` active; mainnet market data live (95 instruments); official API setup guide requires `Create Web2 Account -> SecureKey -> Web3 Accounts -> Fund -> API Key` |
| Extended | Wallet-first account creation in docs; JS bundle contains `Dynamic.xyz` wallet SDK (supports email/social/embedded wallets) but not yet visibly surfaced | Dynamic.xyz (`dynamicEnvironmentId`) present in JS bundle -- not Privy; first-pass was wrong to say "no embedded wallet evidence" | API key for reads + API key + Stark signature (SNIP12/EIP-712) for writes; per sub-account; up to 10 accounts/wallet | High on testnet (full write-path proved in first-pass); mainnet requires real USDC deposit first; 121 mainnet markets, 31 testnet | Mainnet live with $339M daily BTC volume; `Rhino.fi` for cross-chain bridging (Arbitrum); SDK `drop-api-keys` branch hints at future auth simplification |
| Paradex | Current docs support direct EVM onboarding and Privy-backed email/social wallets; frontend onboarding is more Web2-friendly than the older wallet-only narrative | Yes; current docs explicitly support Privy email/social wallets, and live app/testnet CSP confirms Privy runtime | JWT + main private key / subkey / readonly token; EVM SIWE v2 onboarding/auth plus Starknet subkey trading, while official SDK/code samples still lean on older `/onboarding` + `/auth` + L2 private-key flows | Medium; frontend onboarding is smoother, but a fresh raw wallet still cannot cleanly jump to programmatic trading before account creation/initialization | Mainnet/testnet apps live and expose Privy in CSP; testnet config live; local `/v1/onboarding` probe hit `INSUFFICIENT_MIN_CHAIN_BALANCE`, then `/v1/auth` returned `NOT_ONBOARDED`; docs say new testnet accounts are auto-credited after creation |
| Ethereal | Wallet-first onboarding in docs/API, but CSP reveals `Privy` + `Fun.xyz` + `MoonPay` integrations in the live frontend | CSP contains `auth.privy.io` in frame-src and `funkit` (Fun.xyz SDK) in HTML -- embedded wallet infra IS present but not yet documented in dev guides | EIP-712 per-action signing (8 types), no API key alternative; 49 REST endpoints + native WebSocket v2; linked signers for delegation | Low from raw wallet alone; first deposit (min 10 USDe) into a subaccount is mandatory; testnet funding now requires Discord request (no public faucet) | 15 mainnet / 17 testnet products live; wallet still returns empty subaccounts + `404 Signer not found`; CSP also shows Relay, Merkl, Zerion, Binance Wallet, and ZK Lighter cross-references |
| Nado | Wallet-first, very explicit CEX-to-DEX onboarding docs | No embedded wallet evidence found; linked signers power 1-Click Trading but remain optional | No API keys; wallet signatures only; linked signer optional | Low from raw wallet alone; first deposit creates subaccount, but a direct deposit address is already queryable for the deterministic default subaccount before it exists | Gateway status active; default subaccount `exists=false`; linked signer is zero address; archive already returns a deposit address for that same default subaccount |
| StandX | Wallet-first (BSC + Solana); no email/social login visible; no embedded wallet signals in CSP or HTML | No embedded wallet evidence found | JWT via wallet signature (SIWE + ed25519 key pair), no traditional API keys; self-custodial token management with configurable permissions/expiry; body signature (ed25519) required for write ops | Medium-high; full REST + WebSocket trading API, but must hold DUSD (proprietary stablecoin) and use two-wallet system (Cash + Perps) | API live at `perps.standx.com`; BTC-USD $297M/24h volume; prepare-signin returns valid JWT for test wallet; private endpoints return `401 missing jwt`; 4 markets (BTC, ETH, XAU, XAG) |
| MYX Finance | Dual-path: wallet connection OR social login via `Particle Network` (email/phone/social) | Yes; `Particle Network` for social login + embedded wallet, `Biconomy` for gasless AA, `Seamless Key` as delegated on-chain signer; JS bundle also contains Dynamic.xyz, Magic.link, Safe, ConnectKit, RainbowKit | Only 2 public REST endpoints (market data); all trading is on-chain via smart contracts or Seamless Key -- no off-chain REST trading API | Low for API-first; no REST order API exists; must interact with smart contracts directly or use Seamless Key (on-chain delegated signer) | `api.myx.finance` returns 37 perp pairs; JS bundle confirms Particle + Biconomy + WalletConnect + Dynamic + Magic + Safe; V2 with EIP-4337/7702 funded by Consensys but not yet launched |

---

## Part 4: Detailed Platform Analysis

### 4.1 Hyperliquid

**Overview & Onboarding:**

- Official onboarding docs say you can trade with a `normal defi wallet` or by `logging in with your email address`.
- Hyperliquid's email path is not a vague convenience wrapper:
  - the onboarding docs say logging in with email creates `a new blockchain address`
  - the support docs explicitly mention `Privy`
  - the docs also let users `Export Email Wallet` and copy the private key into a normal wallet extension
- For connected-wallet onboarding, the official flow is not just `connect and go`: users are told to click `Enable Trading` and sign a gas-less transaction before depositing.
- The testnet faucet doc explicitly notes that `email login` creates a different wallet address for mainnet and testnet, and that users can `export the email wallet`.
- The same testnet faucet doc says faucet access is not open to arbitrary fresh addresses: you must have `deposited on mainnet with the same address` first.
- On the API side, Hyperliquid supports `API wallets` / `agent wallets` approved by the master account.
- Developer docs also say new HyperCore accounts incur a one-time `1 quote token` activation fee on the first inbound transaction, and `unactivated accounts cannot send CoreWriter actions`.
- Email onboarding also carries a subtle operational trap for developers: the docs explicitly say `Privy` generates a different wallet address for mainnet and testnet, so email users do not automatically satisfy the faucet requirement with the same identity unless they export/import the wallet.

**API Authentication:**

- Raw wallet signing or approved API/agent wallets
- Agent wallets sign on behalf of the master account or sub-accounts
- No API keys in the traditional sense

**Live Probe Results:**

- `POST https://api.hyperliquid.xyz/info {"type":"meta"}` returned live mainnet universe data.
- `POST https://api.hyperliquid-testnet.xyz/info {"type":"meta"}` returned live testnet universe data (207 instruments).
- `POST https://api.hyperliquid-testnet.xyz/info {"type":"clearinghouseState","user":"<wallet>"}` returned a valid zeroed account state.
- `POST https://api.hyperliquid-testnet.xyz/info {"type":"openOrders","user":"<wallet>"}` returned `[]`.
- `POST https://api.hyperliquid-testnet.xyz/info {"type":"subAccounts","user":"<wallet>"}` returned `null`.
- Signed `noop` action returned: `User or API Wallet 0x41deec4e76e46c18719e90920c1efef370b7db0a does not exist.`
- Signed `market_open("BTC", True, 0.001, ...)` returned the same `User or API Wallet ... does not exist` error.

**Second-Pass Corrections:**

- Email onboarding is an explicit Privy-backed embedded path with wallet export.
- Write path still depends on Enable Trading, funded/activated HyperCore state, and testnet faucet gating.
- Mainnet and testnet meta both confirmed live.

**Assessment:**

- `Web2 friendliness`: medium-high
- `API order usability`: high after activation, medium-low from a cold raw wallet
- `Key friction`: `Enable Trading` + deposit/activation + faucet gating all sit in front of signed testnet write-path validation; the `Privy` email-wallet mainnet/testnet split remains a subtle trap

**Sources:**

- https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/how-to-start-trading
- https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/testnet-faucet
- https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/export-your-email-wallet
- https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/connectivity-issues/connected-via-email
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/activation-gas-fee
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint

---

### 4.2 Aster

**Overview & Onboarding:**

- Aster has an official `wallet login` guide and a separate official `email login` guide.
- The wallet-login guide is straightforward wallet auth, but even that path is chain-specific and notes a minimum `0.001 BNB` requirement when connecting on BNB Chain.
- The email flow creates a `new blockchain address` tied to the email and requires `USDT on Arbitrum` for deposits.
- Two distinct private/integration paths:
  - `Aster Pro API`: self-serve API keys for direct account trading (up to 30 API keys per account)
  - `Aster Code`: a separate `Builder + Agent/API Wallet` delegation model requiring 100 ASTER builder stake

**API Authentication:**

- Pro API: `X-MBX-APIKEY` header + HMAC SHA256 signatures
- Aster Code: per-user agent signer key, builder approval chain via `/fapi/v3/` endpoints

**Live Probe Results:**

- `GET https://fapi.asterdex.com/fapi/v1/ping` returned `{}`.
- `GET https://fapi.asterdex.com/fapi/v1/time` returned live `serverTime`.
- `GET https://fapi.asterdex.com/fapi/v1/exchangeInfo` returned full live market/instrument schema.
- `HEAD https://www.asterdex.com/en/api-management` returned `200`.
- Aster Code private probe sequence:

```json
{
  "base_url": "https://fapi.asterdex.com",
  "probe_sequence": [
    {
      "endpoint": "/fapi/v3/agent",
      "query": "timestamp=1&recvWindow=5000",
      "status_code": 400,
      "json": {"code": -1102, "msg": "Mandatory parameter 'nonce' was not sent, was empty/null, or malformed."}
    },
    {
      "endpoint": "/fapi/v3/agent",
      "query": "timestamp=1&recvWindow=5000&nonce=1",
      "status_code": 400,
      "json": {"code": -1102, "msg": "Mandatory parameter 'user' was not sent, was empty/null, or malformed."}
    },
    {
      "endpoint": "/fapi/v3/agent",
      "query": "timestamp=1&recvWindow=5000&nonce=1&user=0x41Deec4e76e46c18719E90920C1efef370B7DB0A",
      "status_code": 400,
      "json": {"code": -1102, "msg": "Mandatory parameter 'signature' was not sent, was empty/null, or malformed."}
    }
  ]
}
```

**Second-Pass Corrections:**

- Aster should not be modeled as `Aster Code only`. The Pro API path is standard self-serve and materially simpler.
- Dual-track: direct trader path (HMAC) vs delegated platform path (builder + agent signer).

**Assessment:**

- `Web2 friendliness`: high
- `API order usability`: high for direct trader (Pro API keys); medium for builder integrations (Aster Code)
- `Key friction`: fresh wallet still needs onboarding, deposit, and UI-side API-key creation

**Sources:**

- https://docs.asterdex.com/product/help/how-to-login-to-aster-with-your-wallet
- https://docs.asterdex.com/product/help/how-to-login-to-aster-with-your-email-address
- https://docs.asterdex.com/product/aster-perpetuals/api
- https://docs.asterdex.com/product/aster-perpetuals/api/how-to-create-an-api
- https://www.asterdex.com/en/api-management
- https://asterdex.github.io/aster-api-website/futures/general-info/
- https://asterdex.github.io/aster-api-website/asterCode/integration-flow/

---

### 4.3 trade[XYZ]

**Overview & Onboarding:**

- trade[XYZ] offers two clear onboarding paths: `Privy email wallet` or `connect existing wallet`.
- The docs explicitly say users can `create a new wallet directly in our interface via Privy`, framing it as the `fastest option` for new users.
- Existing-wallet users must verify wallet control, ensure they are on the `Hyperliquid` network, then `Deposit to Get Started`, and may then need to click `Enable Trading`.
- All markets accessed through trade[XYZ] operate on `Hyperliquid`. The `XYZ protocol` is a `HIP-3 DEX instance`.
- trade[XYZ] is the interface for XYZ markets and other Hyperliquid markets, and `is not the exclusive means of accessing XYZ markets`.

**API Authentication:**

- Uses Hyperliquid API directly: mainnet at `https://api.hyperliquid.xyz`, testnet at `https://api.hyperliquid-testnet.xyz`.
- For XYZ-specific markets, pass `type: perpDexs` and instrument identifiers such as `xyz:XYZ100`.

**Live Probe Results:**

- `HEAD https://trade.xyz` returned `200`.
- `HEAD https://app.trade.xyz` returned `200`.
- Production CSP signals:
  - `child-src` / `frame-src` include `https://auth.privy.io`
  - `connect-src` includes `https://*.hyperliquid.xyz` and `https://*.hyperliquid-testnet.xyz`
  - WebSocket access for `wss://*.hyperliquid.xyz` and `wss://*.hyperliquid-testnet.xyz`
- HTML includes `preconnect` and `dns-prefetch` hints for `https://api-ui.hyperliquid.xyz`.

**Assessment:**

- `Web2 friendliness`: high
- `API order usability`: medium-high (because Hyperliquid is underneath)
- `Key friction`: Privy smooths onboarding, but connected-wallet users still face deposit, Enable Trading, separate balance buckets, and geographic restrictions

**Sources:**

- https://docs.trade.xyz/about-trade-xyz/introduction
- https://docs.trade.xyz/getting-started/creating-or-connecting-your-wallet
- https://docs.trade.xyz/api/overview
- https://docs.trade.xyz/about-trade-xyz/hyperliquid-xyz-and-hip-3
- https://docs.trade.xyz/support-and-faqs/faqs/trade-xyz-and-equities-xyz-markets

---

### 4.4 EdgeX

**Overview & Onboarding:**

- EdgeX supports both `wallet login` and `MPC Login Users` via email.
- Email login creates an `EVM address` for the user after email verification.
- Live frontend now specifically loads a `lib-privy` bundle with `auth.privy.io` in CSP.

**API Authentication:**

- Two-layer auth stack:
  1. Private REST: `X-edgeX-Api-Key` + `X-edgeX-Passphrase` + `X-edgeX-Signature` + `X-edgeX-Timestamp`
  2. Order signing: separate `L2 private key` + `l2Signature` using Pedersen hash + ECDSA

**Live Probe Results:**

```json
{
  "public_funding_rate": {
    "status": 200,
    "body": {"code": "SUCCESS", "data": []}
  },
  "private_get_position_transaction_page": {
    "no_headers": {"code": "GATEWAY_HEADER_REQUIRED", "msg": "header required : 'X-edgeX-Api-Key'"},
    "api_key_only": {"code": "GATEWAY_HEADER_REQUIRED", "msg": "header required : 'X-edgeX-Passphrase'"},
    "api_key_and_passphrase": {"code": "GATEWAY_HEADER_REQUIRED", "msg": "header required : 'X-edgeX-Signature'"},
    "fake_full_header_stack": {"code": "INVALID_ACCOUNT_ID", "msg": "invalid accountId : 543429922991899150"}
  },
  "private_register_account": {
    "no_headers": {"code": "GATEWAY_HEADER_REQUIRED", "msg": "header required : 'X-edgeX-Api-Key'"}
  }
}
```

**Second-Pass Corrections:**

- Doc/runtime mismatch: docs say `X-edgeX-Api-Timestamp` and `X-edgeX-Api-Signature`; live gateway demands `X-edgeX-Api-Key`, `X-edgeX-Passphrase`, `X-edgeX-Signature`, and `X-edgeX-Timestamp`.
- Frontend is concretely Privy-backed, not just abstractly email-capable.

**Assessment:**

- `Web2 friendliness`: high at the frontend, medium at the integration layer
- `API order usability`: medium-low for independent integrators
- `Key friction`: high; exchange-native private-API credentials stacked on top of separate L2 signing path

**Sources:**

- https://edgex-1.gitbook.io/edgeX-documentation/getting-started/accounts-and-wallets
- https://edgex-1.gitbook.io/edgeX-documentation/api/authentication
- https://edgex-1.gitbook.io/edgeX-documentation/api/private-api/account-api
- https://edgex-1.gitbook.io/edgeX-documentation/api/private-api/order-api
- https://edgex-1.gitbook.io/edgeX-documentation/api/sign

---

### 4.5 Variational

**Overview & Onboarding:**

- Split into `Omni` (live) vs `Pro` (not live).
- Omni is the `first live app on the Variational Protocol`, focused on perp trading.
- Pro is `currently not live` (waitlist only).
- Deposits are `wallet-first`, `gasless` using EIP-712/EIP-2612, flat 0.1 USDC fee.

**API Authentication:**

- Current live API is read-only Omni stats.
- Trading API is explicitly "still in development, and is not yet available to any users."
- Old Pro API docs (HMAC/API-key) return 404 and old hostnames don't resolve.

**Live Probe Results:**

```json
{
  "stats_endpoint": {"url": "https://omni-client-api.prod.ap-northeast-1.variational.io/metadata/stats", "status": 200},
  "web_apps": {
    "omni_mainnet": {"url": "https://omni.variational.io", "status": 200},
    "omni_testnet": {"url": "https://omni.testnet.variational.io", "status": 200}
  },
  "dns_resolution": {
    "pro.testnet.variational.io": {"error": "[Errno 8] nodename nor servname provided, or not known"},
    "api.testnet.variational.io": {"error": "[Errno 8] nodename nor servname provided, or not known"},
    "api.variational.io": {"error": "[Errno 8] nodename nor servname provided, or not known"}
  }
}
```

**Assessment:**

- `Web2 friendliness`: medium for deposit UX, low for account abstraction
- `API order usability`: effectively unavailable today
- `Key friction`: the blocker is that the live product/API surface is read-only

**Sources:**

- https://docs.variational.io/
- https://docs.variational.io/technical-documentation/api
- https://docs.variational.io/pro/about-pro

---

### 4.6 Lighter

**Overview & Onboarding:**

- Wallet-first + deposit-first + API-native.
- Users need an `Ethereum wallet` to register. Live app shows `Connect Wallet to Trade`.
- No email, social-login, or embedded-wallet markers found.

**API Authentication:**

- Main accounts + sub-accounts
- API key public/private key pairs (indices 2-254 for programmatic use, 0-1 reserved for web/mobile)
- Per-key nonce management + auth token generation (up to 8h canonical, 1d-10y readonly)
- Standard vs Premium account types

**Live Probe Results:**

```json
{
  "order_book_details": {"status": 200},
  "accounts_by_l1_address": {"body": {"code": 21100, "message": "account not found"}},
  "create_intent_address": {"body": {"code": 200, "intent_address": "0x59B28B2c5414da224f32146895b95cCD283D75e9"}},
  "next_nonce": {
    "account_index_0_api_key_2": {"body": {"code": 200, "nonce": 0}},
    "account_index_999999999_api_key_2": {"body": {"code": 200, "nonce": 0}}
  }
}
```

**Assessment:**

- `Web2 friendliness`: low
- `API order usability`: high after account creation
- `Key friction`: deposit -> credited deposit -> account_index -> API key association -> auth token -> signed trading

**Sources:**

- https://docs.lighter.xyz/trading/api
- https://apidocs.lighter.xyz/docs/get-started
- https://apidocs.lighter.xyz/docs/create-accounts-programmatically
- https://apidocs.lighter.xyz/docs/api-keys

---

### 4.7 GRVT

**Overview & Onboarding:**

- Most explicit `Web2 + Web3 split` in the sample.
- Web2 login: email/password + Google + Microsoft + Apple OAuth.
- Web3 credential: `SecureKey` (external wallet or GRVT Native SecureKey powered by Dfns + Privy).
- Initialization chain: Create Web2 Account -> KYC -> SecureKey -> Web3 Accounts -> Fund -> API Key -> Signer tag.
- Business account signup enabled.
- KYC now required (`NEW_KYC_ENABLE=1`).

**API Authentication:**

- API key login or EIP-712 wallet login, both return session cookies.
- 5 keys max per Funding Account, 5 per Trading Account.
- Each key tagged to an Ethereum address (not SecureKey address).
- IP whitelisting available (up to 5 IPs).

**Live Probe Results:**

```json
{
  "testnet_wallet_login": {
    "endpoint": "https://edge.testnet.grvt.io/auth/wallet/login",
    "status": 401,
    "body": "{\"status\":401,\"message\":\"wallet address not registered\"}"
  },
  "mainnet_wallet_login": {
    "endpoint": "https://edge.grvt.io/auth/wallet/login",
    "status": 400,
    "body": "{\"status\":400,\"message\":\"invalid wallet address\"}"
  },
  "testnet_market_data": {
    "endpoint": "https://market-data.testnet.grvt.io/full/v1/instrument",
    "status": 200,
    "sample_instrument": "BTC_USDT_Perp"
  },
  "mainnet_all_instruments": {
    "endpoint": "https://market-data.grvt.io/full/v1/all_instruments",
    "instrument_count": 95
  }
}
```

**Testnet Env Config Extraction:**

```json
{
  "NEXT_PUBLIC_PRIVY_APP_ID": "cm8ftdmx602461229vprun741",
  "NEXT_PUBLIC_DFNS_ENABLE": "1",
  "NEXT_PUBLIC_DFNS_PRIVY_ENABLE": "1",
  "NEXT_PUBLIC_DFNS_APP_ID": "ap-3u16a-jq5e8-9gaqa965d49p5u36",
  "NEXT_PUBLIC_APPLE_OAUTH_ENABLE": "1",
  "NEXT_PUBLIC_MSFT_SIGN_UP_OAUTH_REQUIRED": "1",
  "NEXT_PUBLIC_NEW_KYC_ENABLE": "1",
  "NEXT_PUBLIC_ENABLE_BUSINESS_ACCOUNT_SIGNUP": "1",
  "NEXT_PUBLIC_MFA_TOTP_FORCED_FLAGS": "111111111",
  "NEXT_PUBLIC_GRVT_CHAIN_ID": "326"
}
```

**Second-Pass Corrections:**

- Native SecureKey is Dfns + Privy composite, not just Privy alone.
- Apple and Microsoft OAuth both enabled (broadest Web2 social login).
- KYC newly confirmed as required.
- MFA/TOTP appears forced.
- Own L2 chain (Chain ID 326 testnet / 325 mainnet).

**Assessment:**

- `Web2 friendliness`: very high (broadest in sample)
- `API order usability from cold wallet`: still low
- `Key friction`: KYC + cold wallet returns 401 + wallet signup now requires email + Native SecureKey cannot receive deposits + MFA forced

**Sources:**

- https://help.grvt.io/en/articles/13038840-how-to-log-in-sign-up-with-your-wallet-step-by-step-guide
- https://help.grvt.io/en/articles/10085106-what-is-a-grvt-native-securekey
- https://api-docs.grvt.io/
- https://api-docs.grvt.io/api_setup/
- https://docs.tealstreet.io/docs/connect/grvt
- https://github.com/wezzcoetzee/grvt

---

### 4.8 Extended

**Overview & Onboarding:**

- Wallet-first, infrastructure-heavy. Two signatures for account creation + registration.
- Account and signing key pair stored locally in browser.
- Up to 10 trading accounts per wallet.
- Testnet on Sepolia: $100,000 test USDC per day claimable per wallet.
- Dynamic.xyz present in JS bundle (not Privy).

**API Authentication:**

- Read-only: API key only (`X-Api-Key` header)
- Write: API key + Stark signature (SNIP12 / EIP-712 for Starknet)
- Rate limit: 1000 req/min default tier

**Live Probe Results:**

Full write-path proved on testnet:
1. Onboarded: account_id 16233, status ACTIVE
2. API key created: 32-character key
3. Balance: 1000 USD available for trade
4. Signed IOC order accepted:
   - Market: BTC-USD, side: BUY, qty: 0.0001, price: 35618.6
   - Order resolved: status=CANCELLED, reason=NO_LIQUIDITY
5. No resting orders after probe

Mainnet: 121 markets, BTC-USD showing ~$339M daily volume, $106M open interest.

**Second-Pass Corrections:**

- Dynamic.xyz wallet SDK IS present in JS bundle (first-pass missed it).
- Rhino.fi cross-chain bridging confirmed for Arbitrum deposits.
- 121 mainnet markets (was implied smaller).
- USDC is only collateral (not USDT).
- SDK `drop-api-keys` branch hints at future auth simplification.

**Assessment:**

- `Web2 friendliness`: low-medium (Dynamic.xyz present but not surfaced)
- `API order usability`: very high for serious integrators (full write-path proved)
- `Key friction`: Stark key derivation heavy but fully scriptable end-to-end

**Sources:**

- https://api.docs.extended.exchange/
- https://docs.extended.exchange/extended-resources/account-operations/account-creation
- https://github.com/x10xchange/python_sdk

---

### 4.9 Paradex

**Overview & Onboarding:**

- No longer just `wallet-only`: current docs support direct EVM onboarding via SIWE + Privy email/social wallets.
- EVM wallets derive Paradex account deterministically from EVM address.
- Testnet accounts auto-credited with $1,000,000 test USDC after creation.

**API Authentication:**

- JWT tokens for authenticated access
- Main private key for full access
- Subkeys for trading-only permissions
- Readonly tokens for long-lived GET-only access
- EVM auth v2 using SIWE (`personal_sign`)

**Live Probe Results:**

- Mainnet CSP `frame-src`: `https://login.argent.xyz`, `https://login.ready.co`, `https://privy.paradex.trade`
- Testnet CSP `frame-src`: `https://privy.testnet.paradex.trade`
- Testnet config returned live Starknet params.
- Local probe derived deterministic L2 address: `0x6e0b56155cbf1e6e2762134da12f47ca62d003e1934a3469bdc3dedf6bb2cb3`
- `POST /v1/onboarding` returned: `INSUFFICIENT_MIN_CHAIN_BALANCE` (need 0.001 ETH or 5 USDC on Ethereum/Arbitrum/Base)
- `POST /v1/auth` returned: `NOT_ONBOARDED`

**Second-Pass Corrections:**

- Privy email/social path is real (confirmed in CSP and docs).
- But cold programmatic path still gated by external chain-balance requirement.
- Official SDK/code-samples still lean on older L2 private key flow.

**Assessment:**

- `Web2 friendliness`: medium-high
- `API order usability`: very high
- `Key friction`: minimum external chain balance before account exists; docs/runtime and SDK samples not fully aligned

**Sources:**

- https://docs.paradex.trade/docs/accounts/wallet-overview
- https://docs.paradex.trade/docs/testnet-faqs
- https://docs.paradex.trade/api/general-information/api-authentication
- https://github.com/tradeparadex/code-samples
- https://github.com/tradeparadex/paradex-py

---

### 4.10 Ethereal

**Overview & Onboarding:**

- Wallet-first in docs/API, but CSP reveals Privy + Fun.xyz + MoonPay integrations.
- All trading through subaccounts; first deposit creates subaccount.
- Default subaccount name `primary` (bytes32 encoded).
- Linked signers for UI/one-click trading; expire after 90 days; max 5 per 7 days.

**API Authentication:**

- EIP-712 per-action signing, 8 distinct types
- No JWT or API key alternative
- 49 REST endpoints + native WebSocket v2

**Live Probe Results:**

```json
{
  "probe_date": "2026-03-21",
  "api_host": "https://api.ethereal.trade",
  "wallet": "0x41Deec4e76e46c18719E90920C1efef370B7DB0A",
  "product": {"status": 200, "sample_display_tickers": ["BTC-USD", "ETH-USD", "SOL-USD"]},
  "subaccount": {"status": 200, "body": {"data": [], "hasNext": false}},
  "linked_signer": {
    "status": 404,
    "body": {"message": "Signer not found: 0x41deec4e76e46c18719e90920c1efef370b7db0a", "error": "Not Found", "statusCode": 404}
  }
}
```

**CSP Analysis:**

- `auth.privy.io` in frame-src (Privy)
- `*.fun.xyz` in connect-src, `funkit` in HTML (Fun.xyz)
- `static.moonpay.com`, `api.moonpay.com` in connect-src (MoonPay fiat)
- `api.relay.link` (Relay cross-chain bridging)
- `api.merkl.xyz` (Merkl rewards)
- `dna.zerion.io` (Zerion wallet)
- `wallet.binance.com` (Binance Wallet)
- `mainnet.zklighter.elliot.ai` (ZK Lighter cross-reference)
- `api.statsig.com` (feature flags)

**Second-Pass Corrections:**

- Embedded wallet infrastructure IS present (Privy, Fun.xyz, MoonPay) -- first-pass was wrong.
- Testnet access more restrictive (Discord-only, no public faucet).
- API surface: 49 endpoints (larger than first-pass captured).
- WebSocket upgraded to native v2.
- 15 mainnet / 17 testnet products.

**Assessment:**

- `Web2 friendliness`: medium (Privy/Fun.xyz in CSP but not in dev docs)
- `API order usability from cold wallet`: still low
- `Key friction`: no API key auth, first deposit required, testnet Discord-only, linked signer rate-limited, only USDe deposits

**Sources:**

- https://docs.ethereal.trade/trading/perpetual-futures/ethereal-testnet
- https://docs.ethereal.trade/developer-guides/trading-api/quick-start
- https://docs.ethereal.trade/developer-guides/trading-api/accounts-and-signers
- https://docs.ethereal.trade/developer-guides/trading-api/message-signing
- https://docs.ethereal.trade/developer-guides/trading-api/websocket-gateway

---

### 4.11 Nado

**Overview & Onboarding:**

- Most explicit in teaching `CEX users how to think in DEX terms`.
- No API keys, no username/password; authentication is by wallet signature.
- Subaccounts with default name `default`; created by first deposit (min $5 USDT0).
- Linked signers = `1-Click Trading` (productized delegation, one per subaccount).
- Linked signers can do ANYTHING the main wallet can, including withdraw.

**API Authentication:**

- Pure wallet signatures (EIP-712 for writes, no signatures for read queries)
- No API key abstraction
- Linked signer optional

**Live Probe Results:**

```json
{
  "wallet": "0x41Deec4e76e46c18719E90920C1efef370B7DB0A",
  "default_subaccount": "0x41deec4e76e46c18719e90920c1efef370b7db0a64656661756c740000000000",
  "gateway_with_compression": {
    "status": {"status": "success", "data": "active"},
    "subaccount_info": {"exists": false, "spot_count": 5, "perp_count": 43},
    "linked_signer": {"linked_signer": "0x0000000000000000000000000000000000000000"}
  },
  "archive": {
    "subaccounts": [],
    "direct_deposit_address": {"v1_address": "0x740a7e70262c143bb88d901001d141f986deda45"}
  }
}
```

**Second-Pass Corrections:**

- Linked-signer flow is more polished than a bare delegate-key primitive (productized as `1-Click Trading`).
- Gateway requires compression headers (`Accept-Encoding: gzip/br/deflate`).
- Deposit address queryable before subaccount exists.

**Assessment:**

- `Web2 friendliness`: low at onboarding, medium after deposit with 1-Click Trading
- `API order usability`: medium for bots comfortable with wallet signing
- `Key friction`: no API-key abstraction; first deposit is hard prerequisite

**Sources:**

- https://docs.nado.xyz/developer-resources/get-started/core-concepts
- https://docs.nado.xyz/developer-resources/get-started/quickstart
- https://docs.nado.xyz/developer-resources/get-started/first-deposit
- https://docs.nado.xyz/developer-resources/get-started/linked-signers
- https://docs.nado.xyz/developer-resources/api/endpoints

---

### 4.12 StandX

**Overview & Onboarding:**

- Runs on `BNB Chain (BSC)` and `Solana`. Team: former `Binance Futures` founding team + `Goldman Sachs` alumni.
- Wallet-first only (Connect Wallet). No email/social login. No embedded wallet signals.
- Uses proprietary yield-bearing stablecoin `DUSD` as margin.
- Two-wallet system: Cash Wallet (deposit holding) + Perps Wallet (active trading).
- Correct domain: `standx.com` (NOT `standx.trade`).

**API Authentication:**

- JWT via wallet signature (SIWE + ed25519 key pair) -- no traditional API keys
- Flow: generate ed25519 key pair -> prepare-signin -> sign SIWE message -> login -> JWT (7-180 days)
- Body signature (ed25519) required for write operations
- Self-custodial token management: configurable permissions (Trade, Withdraw), expiry, revocable

**Live Probe Results:**

```json
{
  "api_status": {"endpoint": "https://api.standx.com", "status": 200, "body": "{\"time\":1774100678301,\"status\":\"ok\"}"},
  "symbol_info": {"status": 200, "markets": ["BTC-USD", "ETH-USD", "XAG-USD", "XAU-USD"]},
  "btc_market": {"last_price": "70701", "volume_24h": "4230.74 BTC", "volume_quote_24h": "$297M DUSD", "open_interest": "317.54 BTC ($22.4M)"},
  "prepare_signin": {"status": 200, "note": "Returns valid signedData JWT for test wallet. SIWE message with chainId=56 (BSC)."},
  "private_no_auth": {"status": 401, "body": "{\"code\":401,\"message\":\"missing jwt\"}"},
  "geo": {"region": "TH"}
}
```

**Assessment:**

- `Web2 friendliness`: low (wallet-first only)
- `API order usability`: high (clean REST + WebSocket, comparable to CEX APIs)
- `Key friction`: must hold DUSD, two-wallet transfer step, ed25519 body signature for writes, only 4 markets
- `Unique`: DUSD yields APY while trading, dual-chain BSC+Solana with unified API

**Sources:**

- https://docs.standx.com
- https://docs.standx.com/standx-api/standx-api
- https://docs.standx.com/standx-api/perps-http
- https://docs.standx.com/standx-api/perps-ws
- https://docs.standx.com/standx-api/perps-auth

---

### 4.13 MYX Finance

**Overview & Onboarding:**

- Multi-chain perp DEX on `BNB Chain`, `Arbitrum`, `Linea`, `opBNB`.
- Uses `Matching Pool Mechanism (MPM)` for zero-slippage.
- USDC-margined, up to 50x leverage, 37 trading pairs.
- V2 funded by `Consensys` (Feb 2026) -- Modular Derivative Settlement Engine, not yet launched.
- Dual-path onboarding: wallet connection OR social login via `Particle Network` (email, phone, social).
- `Seamless Key`: proprietary delegated trading key, gas-free via Biconomy relayer, non-custodial.
- New user flow: Social login -> Purchase USDC via credit card -> Create Seamless Key.

**API Authentication:**

- Only 2 public REST endpoints (market data, no auth).
- **No off-chain REST trading API.** All trading is on-chain via smart contracts (Router.sol).
- No WebSocket API. No official SDK.

**Live Probe Results:**

```json
{
  "api_contracts": {"endpoint": "https://api.myx.finance/v2/quote/market/contracts", "status": 200, "count": 37},
  "api_btc_spec": {"endpoint": "https://api.myx.finance/v2/quote/market/contract_specs?ticker_id=BTC-USDC", "status": 200, "body": {"contract_type": "Vanilla", "contract_price_currency": "USDC"}}
}
```

**JS Bundle Signals:**

- Particle Network (social login / embedded wallet)
- Biconomy (account abstraction / gasless)
- WalletConnect, ConnectKit, RainbowKit
- Dynamic.xyz, Magic.link, Safe
- EIP-4337, EIP-7702 references

**Assessment:**

- `Web2 friendliness`: high (Particle Network + Seamless Key + credit card)
- `API order usability`: low (no off-chain trading API; smart contracts only)
- `Key friction`: no REST order API, smart contract integration requires Solidity knowledge, no SDK

**Sources:**

- https://myxfinance.gitbook.io/myx
- https://myxfinance.gitbook.io/myx/protocol/api
- https://myxfinance.gitbook.io/myx/trading-mechanism/introducing-myx-seamless-trading
- https://github.com/myx-protocol/myx-contracts

---

## Part 5: Code Test Records

### 5.1 Test Scripts

#### 5.1.1 hyperliquid_safe_probe.py -- Hyperliquid testnet SDK probe (noop + market order)

```python
#!/usr/bin/env python3.11

import json
import re
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SDK_PATH = ROOT / ".pydeps_hl"
DEFAULT_WALLET_FILE = ROOT / "evm_wallet_20260320_165220.txt"

ADDRESS_PATTERN = re.compile(r"^Address:\s*(0x[a-fA-F0-9]{40})$")
PRIVATE_KEY_PATTERN = re.compile(r"^Private Key:\s*(0x[a-fA-F0-9]{64})$")

sys.path.insert(0, str(SDK_PATH))

from eth_account import Account  # noqa: E402
from hyperliquid.exchange import Exchange  # noqa: E402
from hyperliquid.utils import constants  # noqa: E402
import requests  # noqa: E402


def load_wallet(wallet_file: Path) -> tuple[str, str]:
    address = None
    private_key = None

    for raw_line in wallet_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        address_match = ADDRESS_PATTERN.match(line)
        if address_match:
            address = address_match.group(1)
            continue

        private_key_match = PRIVATE_KEY_PATTERN.match(line)
        if private_key_match:
            private_key = private_key_match.group(1)

    if not address or not private_key:
        raise ValueError(f"Could not parse wallet file: {wallet_file}")

    return address, private_key


def try_call(fn):
    try:
        return {"ok": True, "result": fn()}
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def post_info(payload):
    response = requests.post(
        f"{constants.TESTNET_API_URL}/info",
        json=payload,
        timeout=30,
        headers={"Content-Type": "application/json", "User-Agent": "codex-hl-probe"},
    )
    return {
        "status_code": response.status_code,
        "json": response.json(),
    }


def main() -> int:
    address, private_key = load_wallet(DEFAULT_WALLET_FILE)
    wallet = Account.from_key(private_key)

    meta = post_info({"type": "meta"})["json"]
    exchange = Exchange(
        wallet,
        base_url=constants.TESTNET_API_URL,
        meta=meta,
        spot_meta={"universe": [], "tokens": []},
    )

    results = {
        "wallet_address": address,
        "base_url": constants.TESTNET_API_URL,
        "meta_probe": {
            "ok": True,
            "universe_count": len(meta.get("universe", [])),
        },
        "pre_state": try_call(lambda: post_info({"type": "clearinghouseState", "user": address})),
        "pre_open_orders": try_call(lambda: post_info({"type": "openOrders", "user": address})),
    }

    nonce = int(time.time() * 1000)
    results["noop"] = try_call(lambda: exchange.noop(nonce))

    # Intentionally use an IOC market-style order on a zero-balance wallet.
    # If auth/signing works, the expected outcome is a clean trading-layer rejection
    # such as insufficient margin, not an auth-format failure.
    results["market_open_btc_buy_0_001"] = try_call(lambda: exchange.market_open("BTC", True, 0.001, slippage=0.01))

    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

#### 5.1.2 extended_onboarding_probe.py -- Extended testnet onboarding (account creation + API key)

```python
#!/usr/bin/env python3.11

import asyncio
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SDK_PATH = ROOT / ".pydeps311"
DEFAULT_WALLET_FILE = ROOT / "evm_wallet_20260320_165220.txt"

ADDRESS_PATTERN = re.compile(r"^Address:\s*(0x[a-fA-F0-9]{40})$")
PRIVATE_KEY_PATTERN = re.compile(r"^Private Key:\s*(0x[a-fA-F0-9]{64})$")

sys.path.insert(0, str(SDK_PATH))

from x10.perpetual.configuration import TESTNET_CONFIG  # noqa: E402
from x10.perpetual.trading_client.account_module import AccountModule  # noqa: E402
from x10.perpetual.user_client.user_client import UserClient  # noqa: E402


def load_wallet(wallet_file: Path) -> tuple[str, str]:
    address = None
    private_key = None

    for raw_line in wallet_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        address_match = ADDRESS_PATTERN.match(line)
        if address_match:
            address = address_match.group(1)
            continue

        private_key_match = PRIVATE_KEY_PATTERN.match(line)
        if private_key_match:
            private_key = private_key_match.group(1)

    if not address or not private_key:
        raise ValueError(f"Could not parse wallet file: {wallet_file}")

    return address, private_key


def redact_api_key(api_key: str) -> dict:
    if len(api_key) <= 8:
        return {"prefix": api_key, "length": len(api_key)}
    return {"prefix": api_key[:8], "suffix": api_key[-4:], "length": len(api_key)}


async def run_probe(wallet_file: Path) -> dict:
    address, private_key = load_wallet(wallet_file)
    client = UserClient(TESTNET_CONFIG, lambda: private_key)
    results = {
        "wallet_address": address,
        "testnet_host": TESTNET_CONFIG.onboarding_url,
        "api_base_url": TESTNET_CONFIG.api_base_url,
    }

    onboarded_account = None
    fetched_accounts = []

    try:
        onboarded = await client.onboard()
        onboarded_account = onboarded.account
        results["onboard"] = {
            "ok": True,
            "account": onboarded.account.model_dump(mode="json"),
            "l2_public_key": onboarded.l2_key_pair.public_hex,
        }
    except Exception as exc:  # noqa: BLE001
        results["onboard"] = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    try:
        accounts = await client.get_accounts()
        fetched_accounts = accounts
        results["get_accounts"] = {
            "ok": True,
            "count": len(accounts),
            "accounts": [
                {
                    "account": account.account.model_dump(mode="json"),
                    "l2_public_key": account.l2_key_pair.public_hex,
                }
                for account in accounts
            ],
        }
    except Exception as exc:  # noqa: BLE001
        results["get_accounts"] = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    target_account = None
    if onboarded_account is not None:
        target_account = onboarded_account
    elif fetched_accounts:
        target_account = fetched_accounts[0].account

    if target_account is not None:
        try:
            api_key = await client.create_account_api_key(target_account, description="codex probe")
            results["create_account_api_key"] = {
                "ok": True,
                "api_key": redact_api_key(api_key),
                "account_id": target_account.id,
            }
        except Exception as exc:  # noqa: BLE001
            results["create_account_api_key"] = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "account_id": target_account.id,
            }
    else:
        results["create_account_api_key"] = {
            "ok": False,
            "error_type": "NoAccountAvailable",
            "error": "No onboarded account was available for API key creation.",
        }

    if results["create_account_api_key"].get("ok"):
        account_module = AccountModule(TESTNET_CONFIG, api_key=api_key)
        try:
            account_response = await account_module.get_account()
            account_data = account_response.data
            results["private_get_account"] = {
                "ok": True,
                "account": account_data.model_dump(mode="json") if account_data is not None else None,
            }
        except Exception as exc:  # noqa: BLE001
            results["private_get_account"] = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        try:
            orders_response = await account_module.get_open_orders()
            orders = orders_response.data or []
            results["private_get_open_orders"] = {
                "ok": True,
                "count": len(orders),
            }
        except Exception as exc:  # noqa: BLE001
            results["private_get_open_orders"] = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        await account_module.close_session()

    await client.close_session()
    return results


def main() -> int:
    wallet_file = DEFAULT_WALLET_FILE
    results = asyncio.run(run_probe(wallet_file))
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

#### 5.1.3 extended_write_probe.py -- Extended testnet write path (signed IOC order)

```python
#!/usr/bin/env python3.11

import asyncio
import json
import re
import sys
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SDK_PATH = ROOT / ".pydeps311"
DEFAULT_WALLET_FILE = ROOT / "evm_wallet_20260320_165220.txt"

ADDRESS_PATTERN = re.compile(r"^Address:\s*(0x[a-fA-F0-9]{40})$")
PRIVATE_KEY_PATTERN = re.compile(r"^Private Key:\s*(0x[a-fA-F0-9]{64})$")

sys.path.insert(0, str(SDK_PATH))

from x10.perpetual.accounts import StarkPerpetualAccount  # noqa: E402
from x10.perpetual.configuration import TESTNET_CONFIG  # noqa: E402
from x10.perpetual.markets import MarketModel  # noqa: E402
from x10.perpetual.orders import OrderSide, OrderStatus, TimeInForce  # noqa: E402
from x10.perpetual.trading_client.trading_client import PerpetualTradingClient  # noqa: E402
from x10.perpetual.user_client.user_client import UserClient  # noqa: E402


def load_wallet(wallet_file: Path) -> tuple[str, str]:
    address = None
    private_key = None

    for raw_line in wallet_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        address_match = ADDRESS_PATTERN.match(line)
        if address_match:
            address = address_match.group(1)
            continue

        private_key_match = PRIVATE_KEY_PATTERN.match(line)
        if private_key_match:
            private_key = private_key_match.group(1)

    if not address or not private_key:
        raise ValueError(f"Could not parse wallet file: {wallet_file}")

    return address, private_key


def redact_api_key(api_key: str) -> dict:
    if len(api_key) <= 8:
        return {"prefix": api_key, "length": len(api_key)}
    return {"prefix": api_key[:8], "suffix": api_key[-4:], "length": len(api_key)}


def pick_market(markets: list[MarketModel]) -> MarketModel:
    active_markets = [
        market
        for market in markets
        if market.active and market.market_stats.bid_price > 0 and market.market_stats.ask_price > 0
    ]
    if not active_markets:
        raise ValueError("No active markets with non-zero bid/ask were returned.")

    for keyword in ("BTC", "ETH", "SOL"):
        for market in active_markets:
            if keyword in market.name.upper():
                return market

    return active_markets[0]


def build_safe_ioc_order(market: MarketModel) -> dict:
    bid = market.market_stats.bid_price
    ask = market.market_stats.ask_price
    tick = market.trading_config.min_price_change
    floor = market.trading_config.limit_price_floor
    cap = market.trading_config.limit_price_cap

    buy_candidate = max(floor, min(bid * Decimal("0.5"), ask - tick))
    buy_price = market.trading_config.round_price(buy_candidate, rounding_direction=ROUND_DOWN)
    if buy_price < ask:
        return {
            "side": OrderSide.BUY,
            "price": buy_price,
            "strategy": "IOC buy placed well below best ask to avoid execution and resting.",
        }

    sell_candidate = min(cap, max(ask * Decimal("1.5"), bid + tick))
    sell_price = market.trading_config.round_price(sell_candidate, rounding_direction=ROUND_UP)
    if sell_price > bid:
        return {
            "side": OrderSide.SELL,
            "price": sell_price,
            "strategy": "IOC sell placed well above best bid to avoid execution and resting.",
        }

    raise ValueError(f"Could not build a non-crossing IOC order for market {market.name}.")


async def fetch_order_state(client: PerpetualTradingClient, order_id: int, retries: int = 5) -> dict:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = await client.account.get_order_by_id(order_id)
            return {
                "ok": True,
                "attempt": attempt,
                "order": response.data.model_dump(mode="json") if response.data is not None else None,
            }
        except Exception as exc:  # noqa: BLE001
            last_error = {
                "attempt": attempt,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            await asyncio.sleep(1)

    return {
        "ok": False,
        "error": last_error,
    }


async def run_probe(wallet_file: Path) -> dict:
    address, private_key = load_wallet(wallet_file)
    user_client = UserClient(TESTNET_CONFIG, lambda: private_key)
    trading_client = None

    results = {
        "wallet_address": address,
        "testnet_host": TESTNET_CONFIG.onboarding_url,
        "api_base_url": TESTNET_CONFIG.api_base_url,
    }

    try:
        accounts = await user_client.get_accounts()
        if not accounts:
            raise ValueError("No accounts returned by Extended testnet onboarding API.")

        onboarded_account = accounts[0]
        api_key = await user_client.create_account_api_key(
            onboarded_account.account,
            description="codex write probe",
        )

        results["account"] = {
            "id": onboarded_account.account.id,
            "account_index": onboarded_account.account.account_index,
            "status": onboarded_account.account.status,
            "l2_vault": onboarded_account.account.l2_vault,
            "l2_public_key": onboarded_account.l2_key_pair.public_hex,
        }
        results["api_key"] = redact_api_key(api_key)

        stark_account = StarkPerpetualAccount(
            vault=onboarded_account.account.l2_vault,
            private_key=onboarded_account.l2_key_pair.private_hex,
            public_key=onboarded_account.l2_key_pair.public_hex,
            api_key=api_key,
        )
        trading_client = PerpetualTradingClient(TESTNET_CONFIG, stark_account=stark_account)

        try:
            balance_before = await trading_client.account.get_balance()
            results["balance_before_claim"] = {
                "ok": True,
                "balance": balance_before.data.model_dump(mode="json") if balance_before.data is not None else None,
            }
        except Exception as exc:  # noqa: BLE001
            results["balance_before_claim"] = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        try:
            claim = await trading_client.testnet.claim_testing_funds()
            results["claim_testing_funds"] = {
                "ok": True,
                "response": claim.data.model_dump(mode="json") if claim.data is not None else None,
            }
            await asyncio.sleep(1)
        except Exception as exc:  # noqa: BLE001
            results["claim_testing_funds"] = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        try:
            balance_after_claim = await trading_client.account.get_balance()
            results["balance_after_claim"] = {
                "ok": True,
                "balance": balance_after_claim.data.model_dump(mode="json") if balance_after_claim.data is not None else None,
            }
        except Exception as exc:  # noqa: BLE001
            results["balance_after_claim"] = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        try:
            client_info = await trading_client.account.get_client()
            results["client_info_after_claim"] = {
                "ok": True,
                "client": client_info.data.model_dump(mode="json") if client_info.data is not None else None,
            }
        except Exception as exc:  # noqa: BLE001
            results["client_info_after_claim"] = {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        markets_response = await trading_client.markets_info.get_markets()
        markets = markets_response.data or []
        selected_market = pick_market(markets)
        order_plan = build_safe_ioc_order(selected_market)
        order_qty = selected_market.trading_config.min_order_size

        results["selected_market"] = {
            "name": selected_market.name,
            "bid_price": str(selected_market.market_stats.bid_price),
            "ask_price": str(selected_market.market_stats.ask_price),
            "mark_price": str(selected_market.market_stats.mark_price),
            "min_order_size": str(selected_market.trading_config.min_order_size),
            "min_order_size_change": str(selected_market.trading_config.min_order_size_change),
            "min_price_change": str(selected_market.trading_config.min_price_change),
            "limit_price_floor": str(selected_market.trading_config.limit_price_floor),
            "limit_price_cap": str(selected_market.trading_config.limit_price_cap),
        }
        results["planned_probe_order"] = {
            "side": order_plan["side"],
            "qty": str(order_qty),
            "price": str(order_plan["price"]),
            "time_in_force": TimeInForce.IOC,
            "strategy": order_plan["strategy"],
        }

        placed_order_response = await trading_client.place_order(
            market_name=selected_market.name,
            amount_of_synthetic=order_qty,
            price=order_plan["price"],
            side=order_plan["side"],
            time_in_force=TimeInForce.IOC,
            external_id="codex-extended-write-probe",
        )
        placed_order = placed_order_response.data
        results["place_order"] = {
            "ok": True,
            "order": placed_order.model_dump(mode="json") if placed_order is not None else None,
        }

        if placed_order is not None:
            fetched_order = await fetch_order_state(trading_client, placed_order.id)
            results["fetch_order_state"] = fetched_order

            open_orders = await trading_client.account.get_open_orders(market_names=[selected_market.name])
            open_order_list = open_orders.data or []
            results["open_orders_after_probe"] = {
                "ok": True,
                "count": len(open_order_list),
                "orders": [order.model_dump(mode="json") for order in open_order_list],
            }

            active_statuses = {OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED, OrderStatus.UNTRIGGERED}
            if fetched_order.get("ok") and fetched_order.get("order") is not None:
                order_status = fetched_order["order"].get("status")
                if order_status in active_statuses:
                    try:
                        await trading_client.orders.cancel_order(placed_order.id)
                        results["cleanup_cancel"] = {
                            "ok": True,
                            "order_id": placed_order.id,
                        }
                    except Exception as exc:  # noqa: BLE001
                        results["cleanup_cancel"] = {
                            "ok": False,
                            "order_id": placed_order.id,
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        }
        return results
    except Exception as exc:  # noqa: BLE001
        results["probe_error"] = {
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        return results
    finally:
        if trading_client is not None:
            await trading_client.info.close_session()
            await trading_client.testnet.close_session()
            await trading_client.close()
        await user_client.close_session()


def main() -> int:
    results = asyncio.run(run_probe(DEFAULT_WALLET_FILE))
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

#### 5.1.4 grvt_wallet_login_test.mjs -- GRVT testnet EIP-712 wallet login

```javascript
import fs from "node:fs";
import { Wallet, Signature } from "ethers";

const walletFile = "/Users/ocean/Documents/Perp DEX测试/evm_wallet_20260320_165220.txt";
const walletText = fs.readFileSync(walletFile, "utf8");
const privateKeyMatch = walletText.match(/Private Key:\s*(0x[a-fA-F0-9]{64})/);

if (!privateKeyMatch) {
  throw new Error("Private key not found in wallet file");
}

const privateKey = privateKeyMatch[1];
const wallet = new Wallet(privateKey);

const serverTimeRes = await fetch("https://market-data.testnet.grvt.io/time");
if (!serverTimeRes.ok) {
  throw new Error(`Failed to fetch GRVT server time: ${serverTimeRes.status}`);
}

const serverTimeJson = await serverTimeRes.json();
const serverTimeMs = BigInt(serverTimeJson.server_time);
const expiration = (serverTimeMs * 1_000_000n) + (5n * 60n * 1_000_000_000n);
const nonce = Math.floor(Math.random() * 0xffffffff);

const domain = {
  name: "GRVT Exchange",
  version: "0",
  chainId: 326,
};

const types = {
  WalletLogin: [
    { name: "signer", type: "address" },
    { name: "nonce", type: "uint32" },
    { name: "expiration", type: "int64" },
  ],
};

const value = {
  signer: wallet.address,
  nonce,
  expiration,
};

const rawSignature = await wallet.signTypedData(domain, types, value);
const sig = Signature.from(rawSignature);

const loginRes = await fetch("https://edge.testnet.grvt.io/auth/wallet/login", {
  method: "POST",
  headers: {
    "content-type": "application/json",
    "cookie": "rm=true;",
  },
  body: JSON.stringify({
    address: wallet.address,
    signature: {
      signer: wallet.address,
      v: sig.v,
      r: sig.r,
      s: sig.s,
      nonce,
      expiration: expiration.toString(),
      chain_id: "326",
    },
  }),
});

const responseText = await loginRes.text();

console.log(
  JSON.stringify(
    {
      address: wallet.address,
      status: loginRes.status,
      ok: loginRes.ok,
      setCookie: loginRes.headers.get("set-cookie"),
      body: responseText,
    },
    null,
    2,
  ),
);
```

#### 5.1.5 paradex_wallet_probe.mjs -- Paradex L2 key derivation + onboarding/auth payload generation

```javascript
import fs from 'fs';

import { ethers } from 'ethers';
import { keyDerivation } from '@starkware-industries/starkware-crypto-utils';
import * as Starknet from 'starknet';

const WALLET_FILE =
  '/Users/ocean/Documents/Perp DEX测试/evm_wallet_20260320_165220.txt';
const CONFIG_FILE =
  '/Users/ocean/Documents/Perp DEX测试/paradex_testnet_config.json';
function normalizeHex(value) {
  if (typeof value === 'string') {
    return value.startsWith('0x') ? value : `0x${value}`;
  }
  return `0x${BigInt(value).toString(16)}`;
}

function readWalletPrivateKey() {
  const txt = fs.readFileSync(WALLET_FILE, 'utf8');
  const match = txt.match(/Private Key:\s*(0x[0-9a-fA-F]+)/);
  if (!match) {
    throw new Error('private key not found in wallet file');
  }
  return match[1];
}

function readConfig() {
  return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
}

function chainIdHexFromString(value) {
  return `0x${Buffer.from(value, 'utf8').toString('hex')}`;
}

function formatStarkSignature(signature) {
  if (Array.isArray(signature)) {
    return [String(signature[0]), String(signature[1])];
  }
  if (signature && typeof signature === 'object' && 'r' in signature && 's' in signature) {
    return [String(signature.r), String(signature.s)];
  }
  throw new Error(`unexpected stark signature shape: ${JSON.stringify(signature)}`);
}

function buildStarkKeyTypedData(l1ChainId) {
  return {
    domain: {
      name: 'Paradex',
      version: '1',
      chainId: String(l1ChainId),
    },
    primaryType: 'Constant',
    types: {
      Constant: [{ name: 'action', type: 'string' }],
    },
    message: {
      action: 'STARK Key',
    },
  };
}

function buildOnboardingTypedData(starknetChainId) {
  return {
    message: {
      action: 'Onboarding',
    },
    domain: {
      name: 'Paradex',
      chainId: chainIdHexFromString(starknetChainId),
      version: '1',
    },
    primaryType: 'Constant',
    types: {
      StarkNetDomain: [
        { name: 'name', type: 'felt' },
        { name: 'chainId', type: 'felt' },
        { name: 'version', type: 'felt' },
      ],
      Constant: [{ name: 'action', type: 'felt' }],
    },
  };
}

function buildAuthTypedData(starknetChainId, timestamp, expiration) {
  return {
    message: {
      method: 'POST',
      path: '/v1/auth',
      body: '',
      timestamp,
      expiration,
    },
    domain: {
      name: 'Paradex',
      chainId: chainIdHexFromString(starknetChainId),
      version: '1',
    },
    primaryType: 'Request',
    types: {
      StarkNetDomain: [
        { name: 'name', type: 'felt' },
        { name: 'chainId', type: 'felt' },
        { name: 'version', type: 'felt' },
      ],
      Request: [
        { name: 'method', type: 'felt' },
        { name: 'path', type: 'felt' },
        { name: 'body', type: 'felt' },
        { name: 'timestamp', type: 'felt' },
        { name: 'expiration', type: 'felt' },
      ],
    },
  };
}

async function main() {
  const config = readConfig();
  const evmPrivateKey = readWalletPrivateKey();
  const evmWallet = new ethers.Wallet(evmPrivateKey);

  const starkKeyTypedData = buildStarkKeyTypedData(config.l1_chain_id);
  const seedSignature = await evmWallet.signTypedData(
    starkKeyTypedData.domain,
    starkKeyTypedData.types,
    starkKeyTypedData.message,
  );
  const repeatSignature = await evmWallet.signTypedData(
    starkKeyTypedData.domain,
    starkKeyTypedData.types,
    starkKeyTypedData.message,
  );

  if (seedSignature !== repeatSignature) {
    throw new Error('non-deterministic STARK key signature from EVM wallet');
  }

  const l2PrivateKey = normalizeHex(
    keyDerivation.getPrivateKeyFromEthSignature(seedSignature),
  );
  const l2PublicKey = normalizeHex(
    keyDerivation.privateToStarkKey(l2PrivateKey),
  );

  const constructorCalldata = Starknet.CallData.compile({
    implementation: config.paraclear_account_hash,
    selector: Starknet.hash.getSelectorFromName('initialize'),
    calldata: Starknet.CallData.compile({
      signer: l2PublicKey,
      guardian: '0',
    }),
  });

  const l2Address = normalizeHex(
    Starknet.hash.calculateContractAddressFromHash(
      l2PublicKey,
      config.paraclear_account_proxy_hash,
      constructorCalldata,
      0,
    ),
  );

  const provider = new Starknet.RpcProvider({
    nodeUrl: config.starknet_fullnode_rpc_url,
    chainId: Starknet.shortString.encodeShortString(config.starknet_chain_id),
  });
  const account = new Starknet.Account({
    provider,
    address: l2Address,
    signer: l2PrivateKey,
  });

  const onboardingSig = formatStarkSignature(
    await account.signMessage(buildOnboardingTypedData(config.starknet_chain_id)),
  );
  const timestamp = Math.floor(Date.now() / 1000);
  const expiration = timestamp + 24 * 60 * 60;
  const authSig = formatStarkSignature(
    await account.signMessage(
      buildAuthTypedData(config.starknet_chain_id, timestamp, expiration),
    ),
  );

  const result = {
    evmAddress: evmWallet.address,
    l2Address,
    l2PublicKey,
    onboardingRequest: {
      headers: {
        'PARADEX-ETHEREUM-ACCOUNT': evmWallet.address,
        'PARADEX-STARKNET-ACCOUNT': l2Address,
        'PARADEX-STARKNET-SIGNATURE': JSON.stringify(onboardingSig),
      },
      body: {
        public_key: l2PublicKey,
      },
    },
    authRequest: {
      headers: {
        'PARADEX-STARKNET-ACCOUNT': l2Address,
        'PARADEX-STARKNET-SIGNATURE': JSON.stringify(authSig),
        'PARADEX-TIMESTAMP': String(timestamp),
        'PARADEX-SIGNATURE-EXPIRATION': String(expiration),
      },
      timestamp,
      expiration,
    },
  };

  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
```

---

### 5.2 Test Results

#### 5.2.1 hyperliquid_safe_probe_result.json

```json
{
  "wallet_address": "0x41Deec4e76e46c18719E90920C1efef370B7DB0A",
  "base_url": "https://api.hyperliquid-testnet.xyz",
  "meta_probe": {
    "ok": true,
    "universe_count": 207
  },
  "pre_state": {
    "ok": true,
    "result": {
      "status_code": 200,
      "json": {
        "marginSummary": {
          "accountValue": "0.0",
          "totalNtlPos": "0.0",
          "totalRawUsd": "0.0",
          "totalMarginUsed": "0.0"
        },
        "crossMarginSummary": {
          "accountValue": "0.0",
          "totalNtlPos": "0.0",
          "totalRawUsd": "0.0",
          "totalMarginUsed": "0.0"
        },
        "crossMaintenanceMarginUsed": "0.0",
        "withdrawable": "0.0",
        "assetPositions": [],
        "time": 1774069382046
      }
    }
  },
  "pre_open_orders": {
    "ok": true,
    "result": {
      "status_code": 200,
      "json": []
    }
  },
  "noop": {
    "ok": true,
    "result": {
      "status": "err",
      "response": "User or API Wallet 0x41deec4e76e46c18719e90920c1efef370b7db0a does not exist."
    }
  },
  "market_open_btc_buy_0_001": {
    "ok": true,
    "result": {
      "status": "err",
      "response": "User or API Wallet 0x41deec4e76e46c18719e90920c1efef370b7db0a does not exist."
    }
  }
}
```

#### 5.2.2 extended_onboarding_result.json

```json
{
  "wallet_address": "0x41Deec4e76e46c18719E90920C1efef370B7DB0A",
  "testnet_host": "https://api.starknet.sepolia.extended.exchange",
  "api_base_url": "https://api.starknet.sepolia.extended.exchange/api/v1",
  "onboard": {
    "ok": true,
    "account": {
      "id": 16233,
      "description": "Main account",
      "account_index": 0,
      "status": "ACTIVE",
      "l2_key": "0x51477b6e58c98344ded9a8e307479e195a796e49c3940f95cb21b2913d7a585",
      "l2_vault": 513234,
      "bridge_starknet_address": "0x067779645d55f0fd4461e918b9ceba156ed42ce52fafcf72e472964b696a2b94"
    },
    "l2_public_key": "0x51477b6e58c98344ded9a8e307479e195a796e49c3940f95cb21b2913d7a585"
  },
  "get_accounts": {
    "ok": true,
    "count": 1,
    "accounts": [
      {
        "account": {
          "id": 16233,
          "description": "Main account",
          "account_index": 0,
          "status": "ACTIVE",
          "l2_key": "0x51477b6e58c98344ded9a8e307479e195a796e49c3940f95cb21b2913d7a585",
          "l2_vault": 513234,
          "bridge_starknet_address": "0x067779645d55f0fd4461e918b9ceba156ed42ce52fafcf72e472964b696a2b94"
        },
        "l2_public_key": "0x51477b6e58c98344ded9a8e307479e195a796e49c3940f95cb21b2913d7a585"
      }
    ]
  },
  "create_account_api_key": {
    "ok": true,
    "api_key": {
      "prefix": "4bd4dd51",
      "suffix": "a5a9",
      "length": 32
    },
    "account_id": 16233
  },
  "private_get_account": {
    "ok": true,
    "account": {
      "id": 16233,
      "description": "Main account",
      "account_index": 0,
      "status": "ACTIVE",
      "l2_key": "0x51477b6e58c98344ded9a8e307479e195a796e49c3940f95cb21b2913d7a585",
      "l2_vault": 513234,
      "bridge_starknet_address": "0x067779645d55f0fd4461e918b9ceba156ed42ce52fafcf72e472964b696a2b94"
    }
  },
  "private_get_open_orders": {
    "ok": true,
    "count": 0
  }
}
```

#### 5.2.3 extended_write_probe_result.json

```json
{
  "wallet_address": "0x41Deec4e76e46c18719E90920C1efef370B7DB0A",
  "testnet_host": "https://api.starknet.sepolia.extended.exchange",
  "api_base_url": "https://api.starknet.sepolia.extended.exchange/api/v1",
  "account": {
    "id": 16233,
    "account_index": 0,
    "status": "ACTIVE",
    "l2_vault": 513234,
    "l2_public_key": "0x51477b6e58c98344ded9a8e307479e195a796e49c3940f95cb21b2913d7a585"
  },
  "api_key": {
    "prefix": "62b1f847",
    "suffix": "3598",
    "length": 32
  },
  "balance_before_claim": {
    "ok": true,
    "balance": {
      "collateral_name": "USD",
      "balance": "1000",
      "equity": "1000",
      "available_for_trade": "1000",
      "available_for_withdrawal": "1000",
      "unrealised_pnl": "0",
      "initial_margin": "0",
      "margin_ratio": "0.0000",
      "updated_time": 1774072275028
    }
  },
  "claim_testing_funds": {
    "ok": true,
    "response": {
      "id": 2035232950446071808
    }
  },
  "balance_after_claim": {
    "ok": true,
    "balance": {
      "collateral_name": "USD",
      "balance": "1000",
      "equity": "1000",
      "available_for_trade": "1000",
      "available_for_withdrawal": "1000",
      "unrealised_pnl": "0",
      "initial_margin": "0",
      "margin_ratio": "0.0000",
      "updated_time": 1774072275028
    }
  },
  "client_info_after_claim": {
    "ok": true,
    "client": {
      "id": 17059,
      "evm_wallet_address": "0x41deec4e76e46c18719e90920c1efef370b7db0a",
      "starknet_wallet_address": null,
      "referral_link_code": null
    }
  },
  "selected_market": {
    "name": "BTC-USD",
    "bid_price": "71237.3",
    "ask_price": "74400",
    "mark_price": "70650.277546750003",
    "min_order_size": "0.0001",
    "min_order_size_change": "0.00001",
    "min_price_change": "0.1",
    "limit_price_floor": "0.05",
    "limit_price_cap": "0.05"
  },
  "planned_probe_order": {
    "side": "BUY",
    "qty": "0.0001",
    "price": "35618.6",
    "time_in_force": "IOC",
    "strategy": "IOC buy placed well below best ask to avoid execution and resting."
  },
  "place_order": {
    "ok": true,
    "order": {
      "id": 2035232962947313664,
      "external_id": "codex-extended-write-probe"
    }
  },
  "fetch_order_state": {
    "ok": true,
    "attempt": 2,
    "order": {
      "id": 2035232962947313664,
      "account_id": 16233,
      "external_id": "codex-extended-write-probe",
      "market": "BTC-USD",
      "type": "LIMIT",
      "side": "BUY",
      "status": "CANCELLED",
      "status_reason": "NO_LIQUIDITY",
      "price": "35618.6000000000000000",
      "average_price": null,
      "qty": "0.0001000000000000",
      "filled_qty": "0E-16",
      "cancelled_qty": "0E-16",
      "reduce_only": false,
      "post_only": false,
      "payed_fee": "0E-16",
      "created_time": 1774072325820,
      "updated_time": 1774072325874,
      "expiry_time": null,
      "time_in_force": "IOC",
      "tp_sl_type": null,
      "take_profit": null,
      "stop_loss": null
    }
  },
  "open_orders_after_probe": {
    "ok": true,
    "count": 0,
    "orders": []
  }
}
```

#### 5.2.4 grvt_wallet_login_result.json

```json
{
  "address": "0x41Deec4e76e46c18719E90920C1efef370B7DB0A",
  "status": 401,
  "ok": false,
  "setCookie": null,
  "body": "{\"status\":401,\"message\":\"wallet address not registered\"}"
}
```

#### 5.2.5 ethereal_public_probe_result.json

```json
{
  "probe_date": "2026-03-21",
  "api_host": "https://api.ethereal.trade",
  "wallet": "0x41Deec4e76e46c18719E90920C1efef370B7DB0A",
  "product": {
    "status": 200,
    "sample_display_tickers": [
      "BTC-USD",
      "ETH-USD",
      "SOL-USD"
    ]
  },
  "subaccount": {
    "status": 200,
    "body": {
      "data": [],
      "hasNext": false
    }
  },
  "linked_signer": {
    "status": 404,
    "body": {
      "message": "Signer not found: 0x41deec4e76e46c18719e90920c1efef370b7db0a",
      "error": "Not Found",
      "statusCode": 404
    }
  }
}
```

---

### 5.3 curl-based Probe Summaries

**StandX:**
- `POST /v1/offchain/prepare-signin?chain=bsc` with test wallet address returned a valid `signedData` JWT containing a SIWE message with chainId=56.
- `GET /api/query_symbol_info` returned 4 markets (BTC-USD, ETH-USD, XAG-USD, XAU-USD).
- `GET /api/query_balance` without auth returned `{"code":401,"message":"missing jwt"}`.
- `GET /api/query_symbol_market?symbol=BTC-USD` returned: last_price $70,701, volume_24h $297M DUSD.

**MYX:**
- `GET /v2/quote/market/contracts` returned 37 perp pairs across BNB Chain, Arbitrum, Linea.
- `GET /v2/quote/market/contract_specs?ticker_id=BTC-USDC` returned: contract_type Vanilla, currency USDC.
- `app.myx.finance` CSP is minimal (only `upgrade-insecure-requests`) -- all vendor signals are in JS bundles.

**GRVT testnet env config extraction** (from `https://testnet.grvt.io/api/env`):
- `NEXT_PUBLIC_PRIVY_APP_ID`: `cm8ftdmx602461229vprun741`
- `NEXT_PUBLIC_DFNS_ENABLE`: `1`
- `NEXT_PUBLIC_DFNS_PRIVY_ENABLE`: `1`
- `NEXT_PUBLIC_DFNS_APP_ID`: `ap-3u16a-jq5e8-9gaqa965d49p5u36`
- `NEXT_PUBLIC_DFNS_ORG_ID`: `or-1r3dt-7kcb9-0r8ckn81rag7lit`
- `NEXT_PUBLIC_APPLE_OAUTH_ENABLE`: `1`
- `NEXT_PUBLIC_MSFT_SIGN_UP_OAUTH_REQUIRED`: `1`
- `NEXT_PUBLIC_NEW_KYC_ENABLE`: `1`
- `NEXT_PUBLIC_GRVT_CHAIN_ID`: `326`
- `NEXT_PUBLIC_MFA_TOTP_FORCED_FLAGS`: `111111111`

**Ethereal CSP header extraction** (from `app.ethereal.trade`):
- `frame-src`: `auth.privy.io` (Privy)
- `connect-src`: `*.fun.xyz`, `wss://*.fun.xyz` (Fun.xyz wallet SDK)
- `connect-src`: `static.moonpay.com`, `api.moonpay.com` (MoonPay fiat)
- `connect-src`: `api.relay.link` (Relay bridging), `api.merkl.xyz` (Merkl rewards), `dna.zerion.io` (Zerion), `wallet.binance.com` (Binance Wallet), `mainnet.zklighter.elliot.ai` (ZK Lighter)
- `connect-src`: `api.statsig.com` (feature flags)
- HTML: `funkit` string present (Fun.xyz SDK)

**Extended JS bundle analysis** (from `/assets/index-CvzKfSsU.js`, 1.77MB):
- `dynamicEnvironmentId: d4582476-d6fe-4ddb-bc66-2c0941e05456` (Dynamic.xyz)
- `rhinoApiKey: PUBLIC-981a60fc-93a6-4cba-adbf-5ef9960a459b`, `rhinoBaseUrl: https://api.rhino.fi` (Rhino.fi bridging)
- 10+ WalletConnect references
- 0 Privy references (NOT using Privy)
- Build: `app-exchange-v0-64-18-1fc8c2f90`, `runtimeEnv: starknet-prod`

---

## Part 6: Second-Pass Result Files

All 13 platforms have second-pass result JSON files:

| File | Platform | Description |
|---|---|---|
| `hyperliquid_second_pass_result.json` | Hyperliquid | Docs recheck + testnet re-probe. Confirms Privy email path, activation gate. |
| `aster_second_pass_result.json` | Aster | Dual API track correction (Pro API vs Aster Code). |
| `tradexyz_second_pass_result.json` | trade[XYZ] | CSP confirms Privy + Hyperliquid runtime. |
| `edgex_second_pass_result.json` | EdgeX | Gateway header sequence probe + Privy in CSP. |
| `variational_probe_result.json` | Variational | DNS resolution failures for legacy hosts. Read-only API only. |
| `lighter_second_pass_result.json` | Lighter | Docs recheck + createIntentAddress probe. Deposit-first confirmed. |
| `grvt_second_pass_result.json` | GRVT | Env config extraction (Dfns+Privy, KYC, OAuth). Broadest Web2. |
| `extended_second_pass_result.json` | Extended | Dynamic.xyz in bundle, 121 mainnet markets, Rhino.fi bridging. |
| `paradex_second_pass_result.json` | Paradex | Privy in CSP, min chain balance gate, L2 key derivation probe. |
| `ethereal_second_pass_result.json` | Ethereal | CSP reveals Privy+Fun.xyz+MoonPay. 49 endpoints. WebSocket v2. |
| `nado_second_pass_result.json` | Nado | 1-Click Trading productization. Compression header requirement. |
| `standx_second_pass_result.json` | StandX | Full API surface documented. JWT auth flow. 4 markets. |
| `myx_second_pass_result.json` | MYX Finance | Particle+Biconomy+Dynamic+Magic. On-chain only. V2 Consensys-backed. |

Additionally, first-pass probe results:

| File | Platform | Description |
|---|---|---|
| `hyperliquid_safe_probe_result.json` | Hyperliquid | SDK probe: noop + market order both rejected. |
| `extended_onboarding_result.json` | Extended | Testnet onboarding + API key creation succeeded. |
| `extended_write_probe_result.json` | Extended | Full signed IOC order placed and resolved. |
| `grvt_wallet_login_result.json` | GRVT | EIP-712 wallet login returned 401. |
| `ethereal_public_probe_result.json` | Ethereal | Empty subaccounts + 404 signer. |
| `aster_private_probe_result.json` | Aster | Aster Code private endpoint probe sequence. |
| `edgex_probe_result.json` | EdgeX | Gateway header requirement sequence. |
| `lighter_probe_result.json` | Lighter | Account not found + intent address created. |
| `nado_probe_result.json` | Nado | Gateway status + subaccount + deposit address. |
| `paradex_probe_payload.json` | Paradex | Derived L2 address + onboarding/auth payloads. |
| `paradex_testnet_config.json` | Paradex | Live testnet system config (Starknet params). |

---

## Part 7: Updated Rankings (All 13 Platforms)

### Best for Web2-user conversion

1. **MYX Finance** -- Particle Network social login + Seamless Key gasless trading + credit card USDC purchase. The smoothest path from zero-crypto to trading, but only via on-chain smart contracts (no REST API).
2. **GRVT** -- Dfns+Privy Native SecureKey + email + Google + Apple + Microsoft OAuth + KYC. The broadest Web2 social login provider, but the most elaborate initialization chain for API access.
3. **trade[XYZ]** -- Privy email wallet described as the "fastest option" for new users. Smooth frontend, but inherits Hyperliquid activation constraints underneath.
4. **Aster** -- Official email login guide, email creates new blockchain address. Dual Pro API + Aster Code tracks.
5. **EdgeX** -- Privy-backed MPC email login. Web2-friendly front door over exchange-native credential stack.
6. **Hyperliquid** -- Privy email login with wallet export. Enable Trading still required.

### Best for API-first / pro traders

1. **Extended** -- Full write-path proved end-to-end (onboard -> API key -> signed IOC order). 121 mainnet markets, $339M daily BTC volume. Heavy auth stack (EVM + Stark + API key) but fully scriptable.
2. **StandX** -- Clean REST + WebSocket trading API comparable to CEX APIs. JWT auth via wallet signature, well-documented EVM + Solana examples. Only 4 markets.
3. **Paradex** -- JWT + subkeys + readonly tokens. Cleanest credential delegation model. $1M test USDC on testnet. But cold wallet still gated by min chain balance.
4. **Hyperliquid** -- Agent wallet pattern is clearly documented and widely adopted. Clean after activation, but activation/deposit required first.
5. **Lighter** -- Mature API key + auth token + sub-account stack. Standard vs Premium tiers. But deposit-first and no email login.
6. **Ethereal** -- 49 REST endpoints + native WebSocket v2. Rich API surface. But EIP-712 per-action (no API keys), and testnet access now Discord-only.

### No REST trading API available

1. **MYX Finance** -- On-chain only (smart contract calls or Seamless Key). 37 pairs but no off-chain REST order API. V2 with account abstraction not yet launched.
2. **Variational** -- Trading API explicitly "still in development." Current live API is read-only Omni stats. Pro is not live. Legacy API hosts don't resolve.

### Most initialization-heavy before first API order

1. **GRVT** -- Web2 Account -> KYC -> SecureKey -> Trading Account -> Fund -> API Key -> Signer tag (7 steps).
2. **EdgeX** -- API Key + Passphrase + Signature + Timestamp + separate L2 key + l2Signature.
3. **Ethereal** -- Discord testnet request -> deposit -> subaccount -> EIP-712 per action -> linked signer rate-limited.
4. **Lighter** -- Deposit -> credited -> account_index -> API key association -> auth token.
5. **Nado** -- First deposit -> subaccount -> wallet signing for every action.

---

## Part 8: Appendix

### Test Wallet

- **Address:** `0x41Deec4e76e46c18719E90920C1efef370B7DB0A`
- **Created:** 2026-03-20
- **Funding:** Zero real funds on all chains. Testnet-only activity on Extended (Sepolia).
- **Note:** Private key is NOT included in this report. Stored locally in `evm_wallet_20260320_165220.txt`.

### URLs Tested

**Hyperliquid:**
- `https://api.hyperliquid.xyz/info` (mainnet)
- `https://api.hyperliquid-testnet.xyz/info` (testnet)

**Aster:**
- `https://fapi.asterdex.com/fapi/v1/ping`
- `https://fapi.asterdex.com/fapi/v1/time`
- `https://fapi.asterdex.com/fapi/v1/exchangeInfo`
- `https://fapi.asterdex.com/fapi/v3/agent`
- `https://fapi.asterdex.com/fapi/v3/builder`
- `https://www.asterdex.com/en/api-management`

**trade[XYZ]:**
- `https://trade.xyz`
- `https://app.trade.xyz`

**EdgeX:**
- `https://pro.edgex.exchange`
- `https://pro.edgex.exchange/api/v1/public/funding/getLatestFundingRate`
- `https://pro.edgex.exchange/api/v1/private/account/getPositionTransactionPage`
- `https://pro.edgex.exchange/api/v1/private/account/registerAccount`

**Variational:**
- `https://omni.variational.io`
- `https://omni.testnet.variational.io`
- `https://omni-client-api.prod.ap-northeast-1.variational.io/metadata/stats`
- `https://docs.variational.io/technical-documentation/api`
- `https://docs.variational.io/technical-documentation/api/authentication` (404)

**Lighter:**
- `https://app.lighter.xyz`
- `https://mainnet.zklighter.elliot.ai/api/v1/orderBookDetails`
- `https://mainnet.zklighter.elliot.ai/api/v1/accountsByL1Address`
- `https://mainnet.zklighter.elliot.ai/api/v1/createIntentAddress`
- `https://mainnet.zklighter.elliot.ai/api/v1/nextNonce`
- `https://mainnet.zklighter.elliot.ai/api/v1/apikeys`
- `https://mainnet.zklighter.elliot.ai/api/v1/changeAccountTier`

**GRVT:**
- `https://edge.testnet.grvt.io/auth/wallet/login`
- `https://edge.grvt.io/auth/wallet/login`
- `https://edge.testnet.grvt.io/auth/api_key/login`
- `https://market-data.testnet.grvt.io/time`
- `https://market-data.grvt.io/time`
- `https://market-data.testnet.grvt.io/full/v1/instrument`
- `https://market-data.grvt.io/full/v1/all_instruments`
- `https://testnet.grvt.io/api/env`

**Extended:**
- `https://api.starknet.sepolia.extended.exchange/api/v1/info/markets` (testnet)
- `https://api.starknet.extended.exchange/api/v1/info/markets` (mainnet)
- `https://api.starknet.extended.exchange/api/v1/info/markets/BTC-USD/stats` (mainnet)
- `https://app.extended.exchange` (JS bundle analysis)

**Paradex:**
- `https://app.paradex.trade`
- `https://app.testnet.paradex.trade`
- `https://api.testnet.paradex.trade/v1/system/config`
- `https://api.testnet.paradex.trade/v1/onboarding`
- `https://api.testnet.paradex.trade/v1/auth`

**Ethereal:**
- `https://api.ethereal.trade/v1/product`
- `https://api.etherealtest.net/v1/product`
- `https://api.ethereal.trade/v1/subaccount`
- `https://api.ethereal.trade/v1/linked-signer/address/<wallet>`
- `https://api.ethereal.trade/v1/rpc/config`
- `https://api.ethereal.trade/openapi.json`
- `https://app.ethereal.trade` (CSP analysis)

**Nado:**
- `https://app.nado.xyz`
- `https://gateway.test.nado.xyz/v1/query` (status, subaccount_info, linked_signer, symbols)
- `https://archive.test.nado.xyz/v1` (subaccounts, direct_deposit_address)

**StandX:**
- `https://api.standx.com`
- `https://perps.standx.com/api/query_symbol_info`
- `https://perps.standx.com/api/query_symbol_market`
- `https://perps.standx.com/api/query_depth_book`
- `https://perps.standx.com/api/query_balance`
- `https://api.standx.com/v1/offchain/prepare-signin`
- `https://geo.standx.com/v1/region`

**MYX Finance:**
- `https://api.myx.finance/v2/quote/market/contracts`
- `https://api.myx.finance/v2/quote/market/contract_specs`
- `https://app.myx.finance` (JS bundle analysis)

### Artifact File Listing

All files in `/Users/ocean/Documents/Perp DEX测试/`:

| File | Type | Description |
|---|---|---|
| `evm_wallet_20260320_165220.txt` | Wallet | Test wallet (address + private key) |
| `hyperliquid_safe_probe.py` | Script | Hyperliquid testnet SDK probe |
| `hyperliquid_safe_probe_result.json` | Result | Hyperliquid probe output |
| `hyperliquid_second_pass_result.json` | Result | Hyperliquid second-pass analysis |
| `extended_onboarding_probe.py` | Script | Extended testnet onboarding probe |
| `extended_onboarding_result.json` | Result | Extended onboarding output |
| `extended_write_probe.py` | Script | Extended testnet write-path probe |
| `extended_write_probe_result.json` | Result | Extended write-path output |
| `extended_second_pass_result.json` | Result | Extended second-pass analysis |
| `grvt_wallet_login_test.mjs` | Script | GRVT EIP-712 wallet login probe |
| `grvt_wallet_login_result.json` | Result | GRVT login output |
| `grvt_second_pass_result.json` | Result | GRVT second-pass analysis (env config) |
| `paradex_wallet_probe.mjs` | Script | Paradex L2 key derivation + payload generation |
| `paradex_probe_payload.json` | Result | Paradex derived addresses + signatures |
| `paradex_testnet_config.json` | Result | Paradex testnet system config |
| `paradex_second_pass_result.json` | Result | Paradex second-pass analysis |
| `ethereal_public_probe_result.json` | Result | Ethereal public API probe output |
| `ethereal_second_pass_result.json` | Result | Ethereal second-pass analysis (CSP) |
| `ethereal_swagger_ui_init.js` | Data | Ethereal OpenAPI spec (311KB) |
| `aster_private_probe_result.json` | Result | Aster Code private endpoint probing |
| `aster_second_pass_result.json` | Result | Aster second-pass analysis |
| `tradexyz_second_pass_result.json` | Result | trade[XYZ] second-pass analysis |
| `edgex_probe_result.json` | Result | EdgeX gateway header sequence |
| `edgex_second_pass_result.json` | Result | EdgeX second-pass analysis |
| `variational_probe_result.json` | Result | Variational DNS + API probes |
| `lighter_probe_result.json` | Result | Lighter first-pass probes |
| `lighter_second_pass_result.json` | Result | Lighter second-pass analysis |
| `nado_probe_result.json` | Result | Nado gateway + archive probes |
| `nado_second_pass_result.json` | Result | Nado second-pass analysis |
| `standx_second_pass_result.json` | Result | StandX full API analysis |
| `myx_second_pass_result.json` | Result | MYX Finance full analysis |
| `first_pass_platform_probe.md` | Notes | First-pass probe notes |
| `full_perp_dex_research_20260321.md` | Report | Full research report (source for this document) |
| `package.json` | Config | Node.js dependencies |
| `package-lock.json` | Config | Node.js lockfile |
| `node_modules/` | Dir | Node.js dependencies (ethers, starknet, starkware-crypto-utils) |
| `.pydeps311/` | Dir | Python 3.11 dependencies (Extended SDK) |
| `.pydeps_hl/` | Dir | Python dependencies (Hyperliquid SDK) |
