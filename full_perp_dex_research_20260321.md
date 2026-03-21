## Full Perp DEX Research Matrix

Date: 2026-03-21
Wallet under test: `0x41Deec4e76e46c18719E90920C1efef370B7DB0A`
Mode: `testnet / zero real funds where possible`
Scope:

- Hyperliquid
- Aster
- trade[XYZ]
- EdgeX
- Variational
- Lighter
- GRVT
- Extended
- Paradex
- Ethereal
- Nado
- StandX
- MYX Finance

### Executive Summary

From a `Web2 onboarding / embedded-wallet` angle, the strongest first-pass signals are:

1. `GRVT`
2. `trade[XYZ]`
3. `Aster`
4. `EdgeX`
5. `Hyperliquid`

From an `API order-path maturity / developer usability` angle, the strongest first-pass signals are:

1. `Paradex`
2. `Extended`
3. `Hyperliquid`
4. `Lighter`
5. `Ethereal`

The biggest strategic split across this set is:

- Some products optimize for `retail/Web2 conversion` via email or embedded credentials.
- Others optimize for `professional API trading` via agent wallets, subkeys, Stark keys, or linked signers.
- Very few let a `fresh raw EVM wallet` go straight to `API first order` without an initialization step.

### Matrix

| Platform | Login / user onboarding | Embedded / AA-like path | API auth & order path | Fresh wallet -> API first order | Live evidence |
| --- | --- | --- | --- | --- | --- |
| Hyperliquid | Official docs support normal wallet or email login | Yes; email login is explicitly supported, support docs tie it to `Privy`, and the email wallet can be exported into a normal wallet extension | Raw wallet signing or approved API wallet / agent wallet | Medium-low from a cold test wallet; public/read path is queryable immediately, but official docs still require `Enable Trading` plus funded/activated HyperCore state before signed write actions work cleanly | Mainnet + testnet `info/meta` live; fresh wallet still returns zeroed read state, but signed `noop` and `market_open` again failed with `User or API Wallet does not exist`; official docs say testnet faucet needs same-address mainnet deposit and unactivated accounts cannot send `CoreWriter` actions |
| Aster | Wallet login and official email login guides both exist | Email login creates a new blockchain address tied to email | Two private paths: standard Pro API uses self-serve API keys + HMAC SHA256 for direct trading, while separate `Aster Code` builder/agent endpoints support delegated execution | Medium; a fresh wallet still needs onboarding, deposit, and UI-side API key creation, but direct trader access is materially simpler than the first-pass builder-only framing | `/fapi/v1/ping`, `/fapi/v1/time`, `/fapi/v1/exchangeInfo` live; official API pages say each account can create up to 30 API keys; `Aster Code` `/fapi/v3/agent` and `/fapi/v3/builder` remain separately signature-gated |
| trade[XYZ] | Existing wallet or Privy email wallet | Privy email wallet is explicit | Uses Hyperliquid API directly for XYZ markets, including `type: perpDexs` routing for XYZ assets | Medium; Privy smooths onboarding, but connected-wallet users still need deposit and sometimes `Enable Trading`, so the same Hyperliquid activation/deposit constraints likely apply underneath | Homepage live; CSP connect-src exposes `auth.privy.io` and `api-ui.hyperliquid.xyz`; official API docs point directly to Hyperliquid mainnet/testnet endpoints |
| EdgeX | Standard wallet or email MPC login | Email-based MPC wallet is explicit | Two-layer auth stack: private REST auth headers plus separate L2 private key / `l2Signature` for order actions | Low from raw wallet alone; specialized setup | Public funding endpoint live; private API gateway currently enforces `Api-Key -> Passphrase -> Signature`, and even `registerAccount` is behind the same private header gate |
| Variational | Wallet-first Omni flow; current live app is Omni, while Pro is not live | No embedded wallet evidence found; gasless deposits reduce friction but do not create an embedded wallet path | Current live API is read-only Omni stats; trading API still unavailable; old Pro/API-key docs and hosts now look archival | Effectively unavailable today for `fresh wallet -> API first order` | Omni mainnet/testnet apps and stats endpoint live; current docs say trading API is still in development and Pro is not live; legacy auth/setup doc URLs now 404 and old `api.*` / `pro.testnet.*` hostnames do not resolve |
| Lighter | Ethereum wallet plus deposit-backed account creation | No embedded wallet evidence found | API key per account/subaccount + auth token + nonce model | Low; programmatic account creation requires credited deposit first, then account index lookup, then API key setup | `orderBookDetails` live; wallet lookup returned `account not found`, but `createIntentAddress` already worked for the same fresh wallet, confirming deposit is the real first programmatic step |
| GRVT | Explicit `Web2 account + SecureKey + account structure` model; Web2 login includes email + Google + Apple + Microsoft OAuth | Strongest embedded path in sample: GRVT Native SecureKey powered by `Dfns` (MPC/WebAuthn/passkeys/backup codes) + `Privy` (email OTP auth layer) — a dual-infrastructure composite, not Privy alone | Session-cookie auth via API key or EIP-712 wallet login; 5 keys max per Funding/Trading Account; each key tagged to an Ethereum address | Low from a fresh wallet; only becomes medium after registered SecureKey plus funding/trading-account initialization; KYC is now required (`NEW_KYC_ENABLE=1`) | Live wallet login still returns `401 wallet address not registered`; testnet env config confirms `DFNS_PRIVY_ENABLE=1` with both `PRIVY_APP_ID` and `DFNS_APP_ID` active; mainnet market data live (95 instruments); official API setup guide requires `Create Web2 Account -> SecureKey -> Web3 Accounts -> Fund -> API Key` |
| Extended | Wallet-first account creation in docs; JS bundle contains `Dynamic.xyz` wallet SDK (supports email/social/embedded wallets) but not yet visibly surfaced | Dynamic.xyz (`dynamicEnvironmentId`) present in JS bundle — not Privy; first-pass was wrong to say "no embedded wallet evidence" | API key for reads + API key + Stark signature (SNIP12/EIP-712) for writes; per sub-account; up to 10 accounts/wallet | High on testnet (full write-path proved in first-pass); mainnet requires real USDC deposit first; 121 mainnet markets, 31 testnet | Mainnet live with $339M daily BTC volume; `Rhino.fi` for cross-chain bridging (Arbitrum); SDK `drop-api-keys` branch hints at future auth simplification |
| Paradex | Current docs support direct EVM onboarding and Privy-backed email/social wallets; frontend onboarding is more Web2-friendly than the older wallet-only narrative | Yes; current docs explicitly support Privy email/social wallets, and live app/testnet CSP confirms Privy runtime | JWT + main private key / subkey / readonly token; EVM SIWE v2 onboarding/auth plus Starknet subkey trading, while official SDK/code samples still lean on older `/onboarding` + `/auth` + L2 private-key flows | Medium; frontend onboarding is smoother, but a fresh raw wallet still cannot cleanly jump to programmatic trading before account creation/initialization | Mainnet/testnet apps live and expose Privy in CSP; testnet config live; local `/v1/onboarding` probe hit `INSUFFICIENT_MIN_CHAIN_BALANCE`, then `/v1/auth` returned `NOT_ONBOARDED`; docs say new testnet accounts are auto-credited after creation |
| Ethereal | Wallet-first onboarding in docs/API, but CSP reveals `Privy` + `Fun.xyz` + `MoonPay` integrations in the live frontend | CSP contains `auth.privy.io` in frame-src and `funkit` (Fun.xyz SDK) in HTML — embedded wallet infra IS present but not yet documented in dev guides | EIP-712 per-action signing (8 types), no API key alternative; 49 REST endpoints + native WebSocket v2; linked signers for delegation | Low from raw wallet alone; first deposit (min 10 USDe) into a subaccount is mandatory; testnet funding now requires Discord request (no public faucet) | 15 mainnet / 17 testnet products live; wallet still returns empty subaccounts + `404 Signer not found`; CSP also shows Relay, Merkl, Zerion, Binance Wallet, and ZK Lighter cross-references |
| Nado | Wallet-first, very explicit CEX-to-DEX onboarding docs | No embedded wallet evidence found; linked signers power 1-Click Trading but remain optional | No API keys; wallet signatures only; linked signer optional | Low from raw wallet alone; first deposit creates subaccount, but a direct deposit address is already queryable for the deterministic default subaccount before it exists | Gateway status active; default subaccount `exists=false`; linked signer is zero address; archive already returns a deposit address for that same default subaccount |
| StandX | Wallet-first (BSC + Solana); no email/social login visible; no embedded wallet signals in CSP or HTML | No embedded wallet evidence found | JWT via wallet signature (SIWE + ed25519 key pair), no traditional API keys; self-custodial token management with configurable permissions/expiry; body signature (ed25519) required for write ops | Medium-high; full REST + WebSocket trading API, but must hold DUSD (proprietary stablecoin) and use two-wallet system (Cash + Perps) | API live at `perps.standx.com`; BTC-USD $297M/24h volume; prepare-signin returns valid JWT for test wallet; private endpoints return `401 missing jwt`; 4 markets (BTC, ETH, XAU, XAG) |
| MYX Finance | Dual-path: wallet connection OR social login via `Particle Network` (email/phone/social) | Yes; `Particle Network` for social login + embedded wallet, `Biconomy` for gasless AA, `Seamless Key` as delegated on-chain signer; JS bundle also contains Dynamic.xyz, Magic.link, Safe, ConnectKit, RainbowKit | Only 2 public REST endpoints (market data); all trading is on-chain via smart contracts or Seamless Key — no off-chain REST trading API | Low for API-first; no REST order API exists; must interact with smart contracts directly or use Seamless Key (on-chain delegated signer) | `api.myx.finance` returns 37 perp pairs; JS bundle confirms Particle + Biconomy + WalletConnect + Dynamic + Magic + Safe; V2 with EIP-4337/7702 funded by Consensys but not yet launched |

### Platform Notes

#### Hyperliquid

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
- This makes Hyperliquid materially better than a wallet-only DEX for mainstream onboarding, but still not a pure Web2 account model.
- For programmatic trading, Hyperliquid is one of the cleanest in the sample because the agent-wallet pattern is clearly documented and widely adopted.

Live probe:

- `POST https://api.hyperliquid.xyz/info {"type":"meta"}` returned live mainnet universe data.
- `POST https://api.hyperliquid-testnet.xyz/info {"type":"meta"}` returned live testnet universe data.
- `POST https://api.hyperliquid-testnet.xyz/info {"type":"clearinghouseState","user":"<wallet>"}` returned a valid zeroed account state for the test wallet rather than an unregistered/account-not-found error.
- `POST https://api.hyperliquid-testnet.xyz/info {"type":"openOrders","user":"<wallet>"}` returned `[]`.
- `POST https://api.hyperliquid-testnet.xyz/info {"type":"subAccounts","user":"<wallet>"}` returned `null`.
- Re-running the official Python SDK probe on `2026-03-21` with `python3.11`, a signed `noop` action again returned `User or API Wallet 0x41deec4e76e46c18719e90920c1efef370b7db0a does not exist.`
- Using the same SDK path on the same rerun, a signed `market_open("BTC", True, 0.001, ...)` probe returned the same `User or API Wallet ... does not exist` error.
- Local artifact: `hyperliquid_safe_probe.py` and `hyperliquid_safe_probe_result.json`
- Local second-pass artifact: `hyperliquid_second_pass_result.json`

Interpretation:

- Hyperliquid is materially easier to query from a fresh raw wallet than GRVT, Paradex, or Ethereal.
- But the read path and the signed write path are not equivalent: a wallet can be queryable before it is an active Hyperliquid user for signed actions.
- The second-pass review also makes the onboarding split clearer:
  - on the frontend, `email login` is a real embedded-style path backed by `Privy`
  - but it is still not the same thing as a ready-to-trade API identity
- The official docs narrow the blocker more precisely than `maybe it just needs funding`: for a raw wallet, `Enable Trading` plus a real funded/activated HyperCore state matter before write actions work cleanly.
- On testnet, this is even stricter operationally because the official faucet itself requires the `same address` to have already deposited on mainnet.
- Email onboarding also carries a subtle operational trap for developers: the docs explicitly say `Privy` generates a different wallet address for mainnet and testnet, so email users do not automatically satisfy the faucet requirement with the same identity unless they export/import the wallet.
- Inference from docs + local probe: the current rejection is still better described as `wallet not yet an activated HyperCore trading user`, not as a generic signing bug.

Assessment:

- `Web2 friendliness`: medium-high
- `API order usability`: high after activation, medium-low from a cold raw wallet
- `Key friction`: `Enable Trading` + deposit/activation + faucet gating all sit in front of signed testnet write-path validation; the `Privy` email-wallet mainnet/testnet split remains a subtle trap

Sources:

- https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/how-to-start-trading
- https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/testnet-faucet
- https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/export-your-email-wallet
- https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/connectivity-issues/connected-via-email
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/activation-gas-fee
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint

#### Aster

- Aster has an official `wallet login` guide and a separate official `email login` guide.
- The wallet-login guide is straightforward wallet auth, but even that path is chain-specific and notes a minimum `0.001 BNB` requirement when connecting on BNB Chain.
- The email flow creates a `new blockchain address` tied to the email and requires `USDT on Arbitrum` for deposits.
- The first-pass conclusion was too narrow on the API side.
- Current official product docs now make a separate `direct trader` path explicit for `Aster Pro`:
  - the API page says `The Aster Pro API allows you to connect your account and operate securely using API keys`
  - the `How to create an API` page says users should go to `API management`, connect their wallet, click `Create API`, and receive an `API key` plus `secret key`
  - the same page says each account can create up to `30 API keys`, and recommends IP binding
  - the public `API management` page on the live site also says `Each account can create up to 30 API keys`
- The official `Futures` API docs describe a conventional direct API model:
  - secure endpoints use `X-MBX-APIKEY`
  - signed endpoints use `HMAC SHA256`
  - API keys can be permission-scoped, and by default can access all secure routes
- So Aster is not `builder-only`.
- Instead, it currently has two distinct private/integration paths:
  - `Aster Pro API`: self-serve API keys for direct account trading
  - `Aster Code`: a separate `Builder + Agent/API Wallet` delegation model
- The `Aster Code` integration flow still makes that delegated path explicit:
  - the `Builder` address itself must already be registered on Aster and have at least `100 ASTER`
  - the Builder backend generates and stores a per-user `Agent/API Wallet` private key
  - the user approves the `Agent` with the main wallet via `POST /fapi/v3/approveAgent`
  - the user approves the `Builder` and fee cap via `POST /fapi/v3/approveBuilder`
  - the Builder then places `POST /fapi/v3/order` requests signed with the per-user signer key

Live probe:

- `GET https://fapi.asterdex.com/fapi/v1/ping` returned `{}`.
- `GET https://fapi.asterdex.com/fapi/v1/time` returned a live `serverTime`.
- `GET https://fapi.asterdex.com/fapi/v1/exchangeInfo` returned a full live market/instrument schema, including `ASTERUSDT`.
- `HEAD https://www.asterdex.com/en/api-management` returned `200`.
- `GET https://fapi.asterdex.com/fapi/v3/agent?...` and `GET https://fapi.asterdex.com/fapi/v3/builder?...` rejected incomplete private-auth probes in sequence:
  - missing `nonce`
  - then missing `user`
  - then missing `signature`
- The official endpoint docs show those same `GET /fapi/v3/agent` and `GET /fapi/v3/builder` calls also require an authorized `signer`, so the local probe only confirms the delegated `Aster Code` path is tightly gated.
- Local artifacts: `aster_private_probe_result.json` and `aster_second_pass_result.json`

Interpretation:

- Aster's public trading API surface is clearly live and production-like.
- But the more important second-pass correction is that Aster should not be modeled as `Aster Code only`.
- The product now exposes a much more conventional direct API path for self-directed traders:
  - onboard account
  - deposit collateral
  - create API key in the UI
  - use the regular HMAC-signed Pro API
- The builder-agent chain still exists, but it is a separate delegated-execution product surface rather than the only private order path.
- So the private story is best understood as `dual-track`:
  - direct trader path: standard API key / secret
  - delegated platform path: builder + per-user agent signer
- For a lone trader or prop desk, this makes Aster materially easier than the first-pass report suggested.
- For platforms building copy-trading / broker / embedded order-routing experiences, the `Aster Code` flow is still the more relevant and more complex path.

Assessment:

- `Web2 friendliness`: high
- `API order usability`: high for a direct trader using Pro API keys; medium for builder-platform integrations using `Aster Code`
- `Key friction`: a fresh wallet still needs onboarding, deposit, and UI-side API-key creation before first order; the heavier builder registration/funding and per-user signer management apply specifically to `Aster Code`, not to every API user

Sources:

- https://docs.asterdex.com/product/help/how-to-login-to-aster-with-your-wallet
- https://docs.asterdex.com/product/help/how-to-login-to-aster-with-your-email-address
- https://docs.asterdex.com/product/aster-perpetuals/api
- https://docs.asterdex.com/product/aster-perpetuals/api/how-to-create-an-api
- https://www.asterdex.com/en/api-management
- https://asterdex.github.io/aster-api-website/futures/general-info/
- https://asterdex.github.io/aster-api-website/asterCode/integration-flow/
- https://asterdex.github.io/aster-api-website/asterCode/endpoints/

#### trade[XYZ]

- trade[XYZ] offers two clear onboarding paths: `Privy email wallet` or `connect existing wallet`.
- The current wallet docs explicitly say users can `create a new wallet directly in our interface via Privy`, and frame the `Privy (email)` path as the `fastest option` for new users without a crypto wallet.
- Existing-wallet users do not just connect once: the docs say they must verify wallet control, ensure they are on the `Hyperliquid` network, then `Deposit to Get Started`, and may then need to click `Enable Trading` and sign an additional confirmation.
- The most important API point is unusually explicit: trade[XYZ] says users interact with all markets `using the Hyperliquid API`, with mainnet at `https://api.hyperliquid.xyz` and testnet at `https://api.hyperliquid-testnet.xyz`.
- For XYZ-specific markets, the docs say users should pass `type: perpDexs` and instrument identifiers such as `xyz:XYZ100`.
- The architecture docs also say:
  - all markets accessed through trade[XYZ] operate on `Hyperliquid`
  - the `XYZ protocol` is a `HIP-3 DEX instance`
  - trade[XYZ] is the interface for XYZ markets and other Hyperliquid markets, and `is not the exclusive means of accessing XYZ markets`
- That means trade[XYZ] is differentiated mainly in interface/onboarding and market packaging, not in its low-level execution API.
- The current FAQ adds an important balance nuance:
  - trade[XYZ] is an interface offering access to Hyperliquid markets generally
  - but `Equities [XYZ]` markets are distinct from Hyperliquid perp and spot markets
  - balances between perp accounts are not shared
- The current introduction page also says the interface may be unavailable in the `U.S.` and other restricted jurisdictions, so smoother onboarding does not mean universally available access.

Live probe:

- `HEAD https://trade.xyz` returned `200`.
- `HEAD https://app.trade.xyz` also returned `200`.
- The production `trade.xyz` homepage CSP shows:
  - `child-src` / `frame-src` include `https://auth.privy.io`
  - `connect-src` includes `https://api-ui.hyperliquid.xyz`
- The production `app.trade.xyz` CSP shows:
  - `child-src` / `frame-src` include `https://auth.privy.io`
  - `connect-src` includes `https://*.hyperliquid.xyz`
  - `connect-src` includes `https://*.hyperliquid-testnet.xyz`
  - websocket access for `wss://*.hyperliquid.xyz` and `wss://*.hyperliquid-testnet.xyz`
- The `app.trade.xyz` HTML also includes `preconnect` and `dns-prefetch` hints for `https://api-ui.hyperliquid.xyz`.
- Local artifact: `tradexyz_second_pass_result.json`

Interpretation:

- The production frontend matches the docs story very closely: `Privy` is part of the onboarding stack, and `Hyperliquid` infrastructure is part of the live runtime path.
- The docs themselves remove most of the ambiguity: trade[XYZ] should be treated as a `Hyperliquid / HIP-3 execution surface with a different onboarding shell`, not as a separate low-level trading stack.
- Inference from the now-confirmed Hyperliquid activation rules: the connected-wallet path on trade[XYZ] likely inherits the same underlying `Enable Trading` / activation / deposit constraints, even if the Privy shell makes them feel smoother.
- The newer docs also make two caveats clearer than the first pass did:
  - interface access may be jurisdiction-gated
  - positions and balances are not fully unified across all Hyperliquid and XYZ market buckets

Assessment:

- `Web2 friendliness`: high
- `API order usability`: medium-high, but mostly because Hyperliquid is underneath
- `Key friction`: Privy smooths onboarding, but connected-wallet users still face deposit and possible `Enable Trading` confirmations before trading is actually live; users also need to account for separate balance buckets and possible interface-level geographic restrictions

Sources:

- https://docs.trade.xyz/about-trade-xyz/introduction
- https://docs.trade.xyz/getting-started/creating-or-connecting-your-wallet
- https://docs.trade.xyz/api/overview
- https://docs.trade.xyz/about-trade-xyz/hyperliquid-xyz-and-hip-3
- https://docs.trade.xyz/support-and-faqs/faqs/trade-xyz-and-equities-xyz-markets

#### EdgeX

- EdgeX supports both `wallet login` and `MPC Login Users` via email.
- The accounts/wallets doc still says email login creates an `EVM address` for the user after email verification.
- That remains more Web2-friendly than a pure wallet-only DEX.
- But the current live frontend is now more specific than the docs: `https://pro.edgex.exchange` visibly loads a `lib-privy` bundle, and its CSP includes `auth.privy.io`.
- So the better current description is not just `email / MPC login`.
- It is: `a Privy-backed Web2-friendly login shell sitting in front of EdgeX's native account and signing stack`.
- However, the programmatic path is more specialized than the retail login story suggests.
- The auth docs describe one signature layer for private REST access:
  - custom headers with `X-edgeX-Api-Timestamp`
  - `X-edgeX-Api-Signature`
  - a private key exported from the UI and used to sign `timestamp + method + path + sorted params/body`
- Separately, the order/sign docs describe a second signature layer for trading actions:
  - dedicated `L2 private key`
  - `l2Signature`
  - Pedersen-hash-based message construction plus ECDSA signing
- The private API docs also expose `registerAccount (Create Sub-Account)` as a private endpoint that requires:
  - `l2Key`
  - `l2KeyYCoordinate`
  - `clientAccountId`
- Order requests then add further L2-specific fields such as `l2Nonce`, `l2Value`, `l2LimitFee`, `l2ExpireTime`, and `l2Signature`.

Live probe:

- `HEAD https://pro.edgex.exchange` returned `200`.
- The current production site CSP includes:
  - `auth.privy.io` in `script-src`
  - `auth.privy.io` in `connect-src`
- The current production HTML includes a `lib-privy` JavaScript bundle.
- `GET https://pro.edgex.exchange/api/v1/public/funding/getLatestFundingRate` returned:
  - `{"code":"SUCCESS","data":[]...}`
- `GET https://pro.edgex.exchange/api/v1/private/account/getPositionTransactionPage?...` with no auth headers returned:
  - `GATEWAY_HEADER_REQUIRED`
  - `header required : 'X-edgeX-Api-Key'`
- The same private call with a fake `X-edgeX-Api-Key` returned:
  - `GATEWAY_HEADER_REQUIRED`
  - `header required : 'X-edgeX-Passphrase'`
- The same private call with fake key + fake passphrase returned:
  - `GATEWAY_HEADER_REQUIRED`
  - `header required : 'X-edgeX-Signature'`
- The same private call with fake key + fake passphrase + fake signature + `X-edgeX-Api-Timestamp` returned:
  - `GATEWAY_HEADER_REQUIRED`
  - `header required : 'X-edgeX-Timestamp'`
- The same private call with fake key + fake passphrase + fake signature + `X-edgeX-Timestamp` returned:
  - `INVALID_API_KEY`
- `POST https://pro.edgex.exchange/api/v1/private/account/registerAccount` with a dummy JSON body but no auth headers returned:
  - `GATEWAY_HEADER_REQUIRED`
  - `header required : 'X-edgeX-Api-Key'`
- Local artifacts: `edgex_probe_result.json` and `edgex_second_pass_result.json`

Interpretation:

- EdgeX's production private API enforces a full custom gateway/auth stack before account data access.
- Importantly, even `registerAccount` is already behind that private gate, so sub-account creation is not exposed as a lightweight raw-wallet bootstrap endpoint.
- Inference from docs + live probe: EdgeX is best understood as a `Web2-friendly front door` sitting on top of an `exchange-native credential stack`, rather than a raw-wallet-first API.
- There is also a current doc/runtime split worth noting:
  - the auth page documents `X-edgeX-Api-Timestamp` and `X-edgeX-Api-Signature` as the required private-API headers
  - the live gateway currently demands `X-edgeX-Api-Key`, `X-edgeX-Passphrase`, `X-edgeX-Signature`, and then a timestamp header named `X-edgeX-Timestamp`
- There is a second doc/runtime split too:
  - docs still describe a generic `MPC email` flow
  - the live frontend now shows a concrete `Privy` dependency
- That makes the real integration burden heavier, and also more vendor-specific, than a first read of the docs suggests.

Assessment:

- `Web2 friendliness`: high at the frontend, medium at the integration layer
- `API order usability`: medium-low for independent integrators
- `Key friction`: high; EdgeX effectively stacks exchange-native private-API credentials on top of a separate L2 signing path

Sources:

- https://edgex-1.gitbook.io/edgeX-documentation/getting-started/accounts-and-wallets
- https://edgex-1.gitbook.io/edgeX-documentation/api/authentication
- https://edgex-1.gitbook.io/edgeX-documentation/api/private-api/account-api
- https://edgex-1.gitbook.io/edgeX-documentation/api/private-api/order-api
- https://edgex-1.gitbook.io/edgeX-documentation/api/sign

#### Variational

- Variational now needs to be split into `Omni` vs `Pro`, instead of being treated as a single unified product surface.
- The current official docs say `Omni` is the `first live app on the Variational Protocol`, focused on perp trading.
- The current `About Pro` page says `Variational Pro is currently not live` and points users to a waitlist.
- The current API page exposes a `Read-Only API` for Omni stats, but explicitly says the `trading API is still in development, and is not yet available to any users`.
- The roadmap still lists both `Enable API trading` and `Launch of Variational Pro` as undated items, which lines up with the current product-state split.
- Omni's deposit UX is still notable:
  - deposits are `wallet-first`
  - deposits are `gasless` using `EIP-712 / EIP-2612`
  - the archived deposit docs say the platform covers the on-chain gas and charges a flat `0.1 USDC` fee
- That is a good friction reducer, but it is still not an embedded-wallet / email-first onboarding path.
- The older `Pro` API story now looks stale rather than current:
  - the old auth/setup doc URLs are no longer live today and return `404`
  - the old `api.testnet.variational.io`, `api.variational.io`, and `pro.testnet.variational.io` hostnames do not resolve in today's probe
- So the more accurate conclusion is no longer just `API key generation is unavailable`.
- It is: `the current live product is Omni, the current public API is read-only, Pro is not live, and the old HMAC/API-key trading stack should be treated as archival residue until Variational re-opens a real trading API path`.

Live probe:

- `GET https://omni-client-api.prod.ap-northeast-1.variational.io/metadata/stats` returned live stats JSON.
- `https://omni.variational.io` returned `200`.
- `https://omni.testnet.variational.io` returned `200`.
- `https://docs.variational.io/technical-documentation/api` returned `200`.
- `https://docs.variational.io/pro/about-pro` returned `200`.
- `https://docs.variational.io/technical-documentation/api/authentication` returned `404`.
- `https://docs.variational.io/technical-documentation/api/quickstart-and-tutorials/api-trading-prerequisites-and-setup` returned `404`.
- DNS resolution today succeeded for `omni.variational.io`, `omni.testnet.variational.io`, and `omni-client-api.prod.ap-northeast-1.variational.io`.
- DNS resolution today failed for `pro.testnet.variational.io`, `api.testnet.variational.io`, and `api.variational.io`.
- Local artifact: `variational_probe_result.json`

Assessment:

- `Web2 friendliness`: medium for deposit UX, low for account abstraction
- `API order usability`: effectively unavailable today for general public trading integration
- `Key friction`: the blocker is no longer just account setup, but that the live product/API surface is read-only while the old trading API stack appears archived

Sources:

- https://docs.variational.io/
- https://docs.variational.io/technical-documentation/api
- https://docs.variational.io/pro/about-pro
- https://docs.variational.io/roadmap
- https://docs.variational.io/archive/deposits
- https://omni.variational.io
- https://omni.testnet.variational.io
- https://omni-client-api.prod.ap-northeast-1.variational.io/metadata/stats

#### Lighter

- Lighter should now be described as `wallet-first + deposit-first + API-native`, not as a Web2-friendly onboarding venue.
- The current product docs still say users need an `Ethereum wallet` to register a main account, and the live app still presents `Connect Wallet` / `Connect Wallet to Trade`.
- The API stack remains one of the most mature in the sample:
  - main accounts + sub-accounts
  - API key public/private key pairs
  - per-key nonce management
  - auth token generation
  - read-only auth tokens
  - programmatic API key creation
  - clear `Standard` vs `Premium` account types with rate-limit / latency separation
- The current `Get Started` guide also sharpens how the front-end fits into the same stack:
  - API-key indices `0` and `1` are reserved for the web/mobile interfaces
  - programmatic keys use indices `2-254`
  - actual authenticated programmatic access is still built around signer initialization and auth-token creation
- The cold-start path is now even more explicit in the official docs:
  - create the account by `depositing assets`
  - wait for the deposit to be credited
  - only then does a master `account_index` get generated
  - only after that should you use `account` / `accountsByL1Address`, associate API keys, and start signed trading
- The deposit docs still expose a pre-account external-funding path via `createIntentAddress` for CCTP-supported chains.

Live probe:

- `GET https://app.lighter.xyz` returned `200`.
- A live text probe of the app showed:
  - `Connect Wallet`
  - `Connect Wallet to Trade`
- A lightweight HTML/text runtime probe did **not** expose obvious `email`, `social-login`, or `embedded-wallet` markers.
- `GET https://mainnet.zklighter.elliot.ai/api/v1/orderBookDetails` returned `200` with live perp/spot market metadata.
- `GET https://mainnet.zklighter.elliot.ai/api/v1/accountsByL1Address?l1_address=0x000000000000000000000000000000000000dEaD` returned:
  - `200`
  - `{"code":21100,"message":"account not found"}`
- `POST https://mainnet.zklighter.elliot.ai/api/v1/createIntentAddress` with the dead address as `from_addr` returned:
  - `{"code":200,"intent_address":"0x59B28B2c5414da224f32146895b95cCD283D75e9"}`
- A fresh live second-pass call also returned another valid intent address:
  - `{"code":200,"intent_address":"0xffA9070EC9e9755dE66D7Ec473CA17C52C89BFBF"}`
- `GET https://mainnet.zklighter.elliot.ai/api/v1/nextNonce?account_index=0&api_key_index=2` returned:
  - `{"code":200,"nonce":0}`
- `GET https://mainnet.zklighter.elliot.ai/api/v1/nextNonce?account_index=999999999&api_key_index=2` also returned:
  - `{"code":200,"nonce":0}`
- `GET https://mainnet.zklighter.elliot.ai/api/v1/apikeys?account_index=0&api_key_index=255` returned public API-key metadata for an existing account, including:
  - `api_key_index`
  - `nonce`
  - `public_key`
  - `transaction_time`
- `POST https://mainnet.zklighter.elliot.ai/api/v1/changeAccountTier` without auth returned:
  - `{"code":20013,"message":"invalid auth"}`
- Official `Create accounts programmatically` docs say a Lighter account is created by depositing assets to Lighter; once credited, a master `account_index` is generated and can then be queried via contract or API.
- Local artifacts:
  - `lighter_probe_result.json`
  - `lighter_second_pass_result.json`

Assessment:

- `Web2 friendliness`: low
- `API order usability`: high after account creation
- `Key friction`: you must first create/fund the account, wait for crediting and `account_index` generation, then finish API-key association and auth-token setup before the flow becomes smooth

Interpretation:

- Lighter's current documented public REST paths remain live and usable from this environment.
- The latest official docs make the cold-start sequence more explicit than the first pass did: `deposit -> credited deposit -> account_index -> API-key association -> auth token -> signed trading`.
- The live `createIntentAddress` result remains important because it shows the deposit rail is already available even before the wallet has an exchange account.
- By contrast, `accountsByL1Address` still says `account not found`, which cleanly confirms that the real gate remains `credited deposit -> generated account_index`.
- The public `apikeys` metadata endpoint is a useful nuance: it shows some API-key metadata is queryable without auth, but that does not reduce the real bootstrap friction because the private key material and signer/auth-token flow are still gated by account ownership.
- The `nextNonce` endpoint is still not a reliable onboarding signal on its own: it returned `nonce: 0` even for an arbitrary large `account_index`, so it should not be read as proof that a usable trading account already exists.
- In practice, the first real blocker is not market-data access, nonce discovery, or even public key metadata; it is still `account creation by credited deposit`.

Sources:

- https://docs.lighter.xyz/trading/api
- https://apidocs.lighter.xyz/docs
- https://apidocs.lighter.xyz/docs/get-started
- https://apidocs.lighter.xyz/docs/create-accounts-programmatically
- https://apidocs.lighter.xyz/docs/deposits-transfers-and-withdrawals
- https://apidocs.lighter.xyz/docs/api-keys
- https://apidocs.lighter.xyz/docs/account-types
- https://apidocs.lighter.xyz/docs/rate-limits
- https://apidocs.lighter.xyz/docs/multi-signature-wallets

#### GRVT

- GRVT has the most explicit `Web2 + Web3 split` in the sample.
- The help center says users sign up with `email/password` or `Google/Microsoft OAuth` for Web2 credentials, and wallet-first signup also asks new users to connect an email during initial registration.
- Trading requires a `SecureKey` as the Web3 credential.
- GRVT allows either:
  - an external wallet as the SecureKey (MetaMask, Coinbase Wallet, Binance Wallet directly; Trust Wallet, Ledger Live, OKX, Phantom, Argent, etc. via WalletConnect)
  - or a `GRVT Native SecureKey` powered by `Privy`, with email OTP and passkey/backup-code recovery
- This is the closest thing in the sample to a serious “self-custodial but Web2-comfortable” onboarding model.
- The `Learn` docs say each user must register both `Web2` and `Web3` credentials.
- The same docs also separate `Funding Account` and `Trading Account`, and say API keys are created at `Trading Account` level.
- The official `API Setup Guide` is unusually explicit about the initialization chain:
  - `Step 1: Create Web2 Account`
  - `Step 2: Create Wallet`
  - `Step 3: Create Web3 Accounts`
  - `Step 4: Mint Tokens & Transfer`
  - `Step 5: Create API Key`
  - `Step 6: API Docs Auth`
- The help-center article for trading-account creation also says creating a trading account requires signing with your `registered SecureKey`.
- On the API side, GRVT supports `API key login` and `wallet login (EIP-712)`, then uses a session cookie.
- The wallet-login docs are also precise: the signer field is `Your registered EVM wallet address`.
- API key limits: max 5 per Funding Account, max 5 per Trading Account; each key must be tagged to a valid Ethereum public address (cannot be the same as SecureKey). IP whitelisting available (up to 5 IPs).
- CRITICAL limitation on Native SecureKey: official docs say “GRVT Native SecureKeys are meant for signing within GRVT and not for receiving funds via deposits. Deposits to GRVT Native SecureKeys will not result in a credit to one's GRVT account.”

Live probe:

- Official testnet wallet login was attempted with the local wallet.
- Result:
  - endpoint: `https://edge.testnet.grvt.io/auth/wallet/login`
  - status: `401`
  - body: `{“status”:401,”message”:”wallet address not registered”}`
- Local artifacts: `grvt_wallet_login_test.mjs` and `grvt_wallet_login_result.json`

Assessment:

- `Web2 friendliness`: very high
- `API order usability`: medium only after full account initialization
- `Key friction`: high before onboarding; even wallet login is not a cold-start primitive and expects a previously registered wallet/account state

Second-pass (2026-03-21):

- Re-ran testnet wallet login with EIP-712 signed payload — still returns `401 wallet address not registered`. Mainnet wallet login endpoint is also live and returns `400 invalid wallet address` for raw address format.
- Extracted testnet frontend env config from `https://testnet.grvt.io/api/env`. Major new findings:
  - **Dfns + Privy dual infrastructure**: The Native SecureKey is NOT just “powered by Privy” — it's a `Dfns` + `Privy` composite. `NEXT_PUBLIC_DFNS_PRIVY_ENABLE=1`, with separate `DFNS_APP_ID` and `PRIVY_APP_ID` both active. Dfns provides the MPC wallet layer (WebAuthn passkeys, backup codes, credentials management via `proxy-dfns.testnet.grvt.io`), while Privy handles the email OTP authentication frontend.
  - **Broader OAuth than first-pass documented**: `APPLE_OAUTH_ENABLE=1` and `MSFT_SIGN_UP_OAUTH_REQUIRED=1` — both Apple and Microsoft OAuth are enabled. This makes GRVT the broadest Web2 social login provider in the sample.
  - **KYC now required**: `NEW_KYC_ENABLE=1`, `KYC_MOBILE_ENABLED=1`. This is a significant friction point not present in most other platforms.
  - **Business account signup**: `ENABLE_BUSINESS_ACCOUNT_SIGNUP=1`, confirming institutional-grade intent.
  - **Own L2 chain**: Chain ID 326 (testnet) / 325 (mainnet), custom RPC at `rpc.testnet.grvt.io` / `rpc.grvt.io`. GRVT is a ZK-rollup with its own block production.
  - **MFA forced**: `MFA_TOTP_FORCED_FLAGS=111111111` suggests MFA/TOTP is mandatory.
- Market data is fully public on both testnet and mainnet:
  - `market-data.testnet.grvt.io/full/v1/instrument` returns instrument details (BTC_USDT_Perp confirmed).
  - `market-data.grvt.io/full/v1/all_instruments` returned 95 instruments on mainnet.
  - Both `market-data.testnet.grvt.io/time` and `market-data.grvt.io/time` return server timestamps.
- Testnet frontend redirects `testnet.grvt.io` → `/exchange/perpetual/BTC-USDT`, powered by Next.js with Sentry instrumentation.
- Community TypeScript SDK exists on GitHub (`wezzcoetzee/grvt`), supports CCXT-style client + WebSocket.
- Tealstreet integration docs confirm: EIP-712 signing required for orders, signer address must be tagged to API key in GRVT UI before trading.

Updated assessment:

- `Web2 friendliness`: very high — the broadest in the sample (email + Google + Apple + Microsoft OAuth + Dfns+Privy Native SecureKey)
- `API order usability from cold wallet`: still low. Full initialization chain required: Web2 Account → KYC → SecureKey registration → Trading Account creation → Funding → API Key generation → Signer address tagging.
- `Key friction`: high before onboarding. Cold wallet returns 401. KYC adds a new layer. Even after onboarding, Native SecureKey cannot receive deposits. MFA appears forced.
- `What changed vs first-pass`: The underlying infrastructure is more sophisticated than described — Dfns MPC + Privy email, not just Privy alone. Apple/Microsoft OAuth were undocumented. KYC is newly confirmed. Core cold-wallet assessment unchanged.

Sources:

- https://help.grvt.io/en/articles/13038840-how-to-log-in-sign-up-with-your-wallet-step-by-step-guide
- https://help.grvt.io/en/articles/10085106-what-is-a-grvt-native-securekey
- https://help.grvt.io/en/articles/9614877-what-is-a-securekey
- https://help.grvt.io/en/articles/9610158-how-do-i-create-a-trading-account
- https://help.grvt.io/en/articles/9636561-how-do-i-generate-an-api-key
- https://help.grvt.io/en/articles/9614688-what-are-api-keys
- https://help.grvt.io/en/articles/9630078-what-wallets-does-grvt-support-for-securekey-via-external-wallets
- https://api-docs.grvt.io/
- https://api-docs.grvt.io/learn/
- https://api-docs.grvt.io/api_setup/
- https://api-docs.grvt.io/trading_api/
- https://docs.tealstreet.io/docs/connect/grvt
- https://github.com/wezzcoetzee/grvt
- Result file: `grvt_second_pass_result.json`

#### Extended

- Extended is wallet-first and more infrastructure-heavy than retail-friendly.
- Official docs say a new wallet connection requires `two signatures`:
  - account creation
  - registration for trading
- The account and signing key pair are stored `locally in the browser`.
- On the API side, Extended is explicit:
  - account can be created via `UI` or `SDK`
  - users manage `API keys`, `Stark keys`, and `Vault numbers`
  - order management needs both `API key` and `Stark signature`
- Testnet is on `Sepolia`, and the docs say users can claim `$100,000 test USDC per day` per L1 wallet.

Live probe:

- `GET https://api.starknet.sepolia.extended.exchange/api/v1/info/markets` returned `200` with a large live market list.
- `GET https://api.starknet.sepolia.extended.exchange/api/v1/info/markets/BTC-USD/stats` returned `200` with live BTC testnet stats.
- `GET https://api.starknet.sepolia.extended.exchange/api/v1/user/account/info` returned `401` without auth.
- `GET https://api.starknet.sepolia.extended.exchange/api/v1/user/orders` returned `401` without auth.
- Local SDK probe via `extended_onboarding_probe.py` then succeeded with the wallet under test:
  - `POST /auth/onboard` returned an active default account:
    - `account_id`: `16233`
    - `account_index`: `0`
    - `status`: `ACTIVE`
  - `GET /api/v1/user/accounts` returned the same account for the L1 wallet.
  - `POST /api/v1/user/account/api-key` succeeded and returned a 32-character API key.
  - Private reads with that API key succeeded:
    - `GET /api/v1/user/account/info`
    - `GET /api/v1/user/orders` with `count = 0`
- Local write-path probe via `extended_write_probe.py` then succeeded on testnet:
  - `GET /api/v1/user/client/info` returned a live client object:
    - `client_id`: `17059`
    - `evm_wallet_address`: the wallet under test
  - testnet balance endpoint returned `1000` USD available for trade
  - a signed `BTC-USD` `IOC` buy probe with:
    - `qty = 0.0001`
    - `price = 35618.6`
    - `time_in_force = IOC`
    was accepted by `POST /api/v1/user/order`
  - the fetched order then resolved to:
    - `status = CANCELLED`
    - `status_reason = NO_LIQUIDITY`
  - `GET /api/v1/user/orders` after the probe returned `count = 0`, so no order was left resting
- Local artifacts:
  - `extended_onboarding_probe.py`
  - `extended_onboarding_result.json`
  - `extended_write_probe.py`
  - `extended_write_probe_result.json`

Interpretation:

- Extended's documented Starknet Sepolia testnet host is live and exposes public market data cleanly.
- The important change from the first pass is that a fresh raw EVM wallet is not blocked by an external balance gate or pre-registration gate on testnet.
- A wallet can onboard directly through the official SDK path, receive an active account, create an API key, and immediately access private read endpoints.
- More importantly, the signed write path is no longer hypothetical: on the activated testnet client, a deliberately non-crossing IOC order was accepted and resolved at the business layer rather than failing at auth.
- The real friction is not account existence but the heavier auth stack:
  - EIP-712 wallet signatures for onboarding
  - derived Stark key material
  - API key for private REST
  - testnet client / balance activation
  - Stark signatures for actual order placement

Assessment:

- `Web2 friendliness`: low-medium
- `API order usability`: very high for serious integrators
- `Key friction`: initialization is materially heavier than a normal EVM-signed REST API, but it is now empirically scriptable end-to-end on testnet

Second-pass (2026-03-21):

- **Correction — embedded wallet infrastructure IS present**: The JS bundle (`/assets/index-CvzKfSsU.js`, 1.77MB) contains `dynamicEnvironmentId: d4582476-d6fe-4ddb-bc66-2c0941e05456` and `dynamicauth` references. This is **Dynamic.xyz** (a competing product to Privy) — supports email, social login, and embedded wallets. However, this is not yet surfaced in docs or prominently in the UI. The first-pass "No embedded wallet evidence found" was incorrect.
- **Rhino.fi cross-chain bridging confirmed**: JS config contains `rhinoApiKey` and `rhinoBaseUrl: https://api.rhino.fi`. This powers the Arbitrum deposit path (under $100k) documented in the deposit docs.
- **Mainnet significantly larger**: 121 markets on mainnet (BTC-USD showing ~$339M daily volume, $106M open interest). Testnet has 31 markets.
- **USDC is the only collateral** (not USDT). Ethereum + Arbitrum deposits supported, no minimum deposit, zero deposit fees currently.
- **Python SDK active on GitHub** (`x10xchange/python_sdk`, package `x10-python-trading-starknet`):
  - Starknet branch is primary, StarkEx branch is legacy.
  - Interesting `drop-api-keys` branch exists — suggests potential future auth model change.
  - Rust-accelerated Stark crypto for signing.
- **Hosting**: AWS CloudFront + S3, build `v0-64-18`, actively maintained.
- Core auth model unchanged: API key for reads, API key + Stark signature (SNIP12) for writes.
- First-pass probe results remain valid (account_id 16233 on testnet, API key creation, signed IOC order all succeeded).

Updated assessment:

- `Web2 friendliness`: low-medium — higher than first-pass. Dynamic.xyz in JS bundle, but not yet user-facing.
- `API order usability from cold wallet`: still the highest in the sample on testnet. Mainnet requires real USDC deposit.
- `Key friction`: Stark key derivation is heavy but well-documented and scriptable. `drop-api-keys` branch hints at potential simplification.
- `What changed vs first-pass`: Dynamic.xyz wallet SDK present. 121 mainnet markets. Rhino.fi bridging. Core auth unchanged.

Sources:

- https://api.docs.extended.exchange/
- https://docs.extended.exchange/extended-resources/account-operations/account-creation
- https://docs.extended.exchange/starkex-specific-docs/deposits-and-withdrawals
- https://docs.extended.exchange/protocol-reference/api-hosts (redirected, content from API docs)
- https://github.com/x10xchange/python_sdk
- https://pypi.org/project/x10-python-trading-starknet/
- Result file: `extended_second_pass_result.json`

#### Paradex

- Paradex is no longer best described as `retail-unfriendly wallet-only onboarding`.
- The current wallet overview explicitly supports:
  - direct `EVM` onboarding via `SIWE`
  - `Email and Social Wallets` secured by `Privy`
- The same wallet-overview doc says EVM wallets are a direct onboarding path, the Paradex account is deterministically derived from the EVM address, and `no key derivation is required` because the wallet’s secp256k1 public key is used directly.
- The current testnet FAQ says each new account is automatically credited with `$1,000,000 test USDC` shortly after creation.
- On the API side, Paradex still has one of the cleanest credential models in the sample:
  - JWT tokens for authenticated access
  - main private key for full access
  - `subkeys` for trading-only permissions
  - `readonly tokens` for long-lived GET-only access
  - `EVM auth v2` using `SIWE` (`personal_sign`)
- This remains a strong model for safe delegation because subkeys can trade but cannot withdraw/transfer.
- But there is now a real split between `current user-facing docs/runtime` and `official integrator code`:
  - current docs present `Privy + direct EVM SIWE v2` as the modern onboarding surface
  - official code-samples and `paradex-py` still lean heavily on the older deterministic `Paradex / L2 private key` flow built around `/onboarding` and `/auth`

Live probe:

- `HEAD https://app.paradex.trade` returned `200`; CSP `frame-src` includes:
  - `https://login.argent.xyz`
  - `https://login.ready.co`
  - `https://privy.paradex.trade`
- `HEAD https://app.testnet.paradex.trade` returned `200`; CSP `frame-src` includes:
  - `https://privy.testnet.paradex.trade`
- `GET https://api.testnet.paradex.trade/v1/system/config` returned live testnet configuration and Starknet-related params.
- Local probe script derived a deterministic Paradex L2 address from the test wallet and prepared valid v1-style onboarding/auth signatures:
  - local artifact: `paradex_wallet_probe.mjs`
  - derived L2 account: `0x6e0b56155cbf1e6e2762134da12f47ca62d003e1934a3469bdc3dedf6bb2cb3`
- `POST https://api.testnet.paradex.trade/v1/onboarding` returned:
  - error: `INSUFFICIENT_MIN_CHAIN_BALANCE`
  - message: account creation requires at least `0.001 ETH` or `5 USDC` on `Ethereum`, `Arbitrum`, or `Base`
- `POST https://api.testnet.paradex.trade/v1/auth` returned:
  - error: `NOT_ONBOARDED`
  - message: user has never called `/onboarding`
- Local second-pass artifact: `paradex_second_pass_result.json`

Interpretation:

- Paradex is materially more `Web2-friendly` on the frontend than the first-pass conclusion suggested.
- The Privy-backed email/social path is not just a docs claim:
  - the current wallet-overview doc exposes it explicitly
  - the live mainnet/testnet apps currently advertise Privy in CSP
- But this does **not** mean a fresh raw wallet can already go straight to API order flow.
- Our local probe still shows that the cold programmatic path is gated before account creation by an `external chain-balance` requirement.
- The current docs/runtime and the official SDK/sample repos therefore tell a more nuanced story:
  - user-facing onboarding has moved toward `Privy + direct EVM SIWE v2`
  - official programmatic examples still mostly assume the older `L2 private key` / `/onboarding` / `/auth` model
- So the important blocker is not simply `signature format confusion`.
- The more accurate interpretation is:
  - Paradex now has a better retail onboarding surface than we first scored
  - but a cold API-first wallet still faces initialization gates before it becomes a tradable account
  - and integrators must currently choose carefully between the newer docs narrative and the older code-sample narrative

Assessment:

- `Web2 friendliness`: medium-high
- `API order usability`: very high
- `Key friction`: frontend onboarding is smoother than before, but API onboarding is still initialization-heavy, docs/runtime and official SDK samples are not fully aligned, and the first real gate is the minimum external chain-balance requirement before the account even exists

Sources:

- https://docs.paradex.trade/docs/accounts/wallet-overview
- https://docs.paradex.trade/docs/testnet-faqs
- https://docs.paradex.trade/api/general-information/api-authentication
- https://github.com/tradeparadex/code-samples
- https://github.com/tradeparadex/paradex-py

#### Ethereal

- Ethereal is `wallet-first`, but its API and signer architecture are unusually well documented.
- All trading happens through `subaccounts`.
- The current quickstart says the first step is to `make your first deposit`.
- The `Accounts & Signers` docs are more explicit: a user must create at least one subaccount by choosing a `bytes32` identifier and then making an initial `deposit` or `depositUsd`.
- The docs explicitly recommend the default subaccount name `primary` (encoded as `bytes32`).
- Subsequent deposits to the same subaccount do not create a new subaccount.
- Ethereal supports `linked signers` so that retail users can submit and cancel orders without signing every action from the EOA.
- The docs explicitly say linked signers are mostly for UI/one-click trading UX, and are not strictly necessary for bots.
- Linked signers cannot withdraw funds, and currently expire after `90` days unless refreshed.
- The API uses `EIP-712` signatures per action type rather than JWT-style login.
- The message-signing docs enumerate separate signed action types such as `LinkSigner`, `RevokeLinkedSigner`, `RefreshLinkedSigner`, `ExtendLinkedSigner`, `EIP712Auth`, `InitiateWithdraw`, `TradeOrder`, and `CancelOrder`.
- Testnet onboarding is also not a pure public faucet flow: the public-testnet docs say users submit an access request through the app, and the testnet distribution system funds accounts in under 24 hours.

Live probe:

- `GET https://api.ethereal.trade/v1/product` returned live public market metadata.
- `GET https://api.ethereal.trade/v1/subaccount?sender=<wallet>` returned `{"data":[],"hasNext":false}` for the wallet under test.
- `GET https://api.ethereal.trade/v1/linked-signer/address/<wallet>` returned:
  - `404`
  - `{"message":"Signer not found: 0x41deec4e76e46c18719e90920c1efef370b7db0a","error":"Not Found","statusCode":404}`
- Local artifact: `ethereal_public_probe_result.json`

Assessment:

- `Web2 friendliness`: medium-low
- `API order usability`: medium-high once the account is initialized
- `Key friction`: fresh wallets cannot trade via API until the testnet access/distribution flow is completed, the first deposit creates a subaccount, and per-action EIP-712 signing is in place

Second-pass (2026-03-21):

- **Major correction — embedded wallet infrastructure IS present**: The CSP headers from `app.ethereal.trade` reveal:
  - `auth.privy.io` in `frame-src` — Privy embedded wallet/auth integration
  - `*.fun.xyz` and `wss://*.fun.xyz` in `connect-src`, plus `funkit` in HTML source — Fun.xyz wallet SDK
  - `static.moonpay.com` and `api.moonpay.com` in `connect-src` — MoonPay fiat on-ramp
  - The first-pass conclusion "No embedded wallet evidence found" is therefore **incorrect**.
  - However, none of these are documented in the developer guides — they appear to be frontend-only integrations, possibly for upcoming features or under A/B testing (Statsig feature flags also in CSP).
- Additional CSP signals: `api.relay.link` (Relay cross-chain bridging), `api.merkl.xyz` (Merkl rewards), `dna.zerion.io` (Zerion wallet), `wallet.binance.com` (Binance Wallet), `mainnet.zklighter.elliot.ai` (ZK Lighter cross-reference).
- Hosting confirmed: Vercel (with Sentry instrumentation).
- Re-ran API probes:
  - Mainnet products: 15 (was fewer in first-pass). Testnet products: 17.
  - Wallet still returns empty subaccounts and `404 Signer not found` on both mainnet and testnet.
  - `/v1/rpc/config` returns full EIP-712 domain and all 8 signature types on both environments.
  - OpenAPI spec (`/openapi.json`) exposes 49 total endpoints, including: referral system, points/rewards, whitelist, rate-limit config, maintenance status, order dry-run.
- Testnet access has become **more restrictive**: current docs say "Reach out to a team member Discord in #developer-support" for testnet funds. No more app-based access request flow.
- Linked signer quota confirmed: max 5 per 7 days across all subaccounts, queryable via `/linked-signer/quota`.
- WebSocket upgraded: native v2 at `wss://ws2.ethereal.trade/v1/stream` is now primary; old Socket.io endpoint is deprecated. 8 channel types available.
- Deposits: only USDe supported, wraps to WUSDe. Min deposit 10 units, zero fees currently.

Updated assessment:

- `Web2 friendliness`: medium — higher than first-pass. Privy + Fun.xyz + MoonPay in CSP, but not yet reflected in developer docs or API design.
- `API order usability from cold wallet`: still low. No API key alternative; EIP-712 per action. First deposit required.
- `Key friction`: testnet access now Discord-only (more restrictive). Linked signer rate-limited. Only USDe deposits.
- `What changed vs first-pass`: Biggest correction is embedded wallet infra presence (Privy, Fun.xyz, MoonPay in CSP). Testnet access more restrictive. API surface richer (49 endpoints). WebSocket upgraded.

Sources:

- https://docs.ethereal.trade/trading/perpetual-futures/ethereal-testnet
- https://docs.ethereal.trade/developer-guides/trading-api/quick-start
- https://docs.ethereal.trade/developer-guides/trading-api/accounts-and-signers
- https://docs.ethereal.trade/developer-guides/trading-api/message-signing
- https://docs.ethereal.trade/developer-guides/trading-api/websocket-gateway
- https://docs.ethereal.trade/developer-guides/trading-api/token-transfers
- https://docs.ethereal.trade/protocol-reference/api-hosts
- https://pypi.org/project/ethereal-sdk/
- Result file: `ethereal_second_pass_result.json`

#### Nado

- Nado is the most explicit in teaching `CEX users how to think in DEX terms`.
- The docs clearly say:
  - `no API keys`
  - `no username/password`
  - authentication is by wallet signature
- Nado uses `subaccounts`, with the default name `default`.
- A subaccount does not exist until the user makes an initial deposit of at least `$5 USDT0` or equivalent.
- The `Quickstart` and `First Deposit` guides are unusually direct that there is no separate account-creation step: `first deposit` is what creates the subaccount.
- Nado also supports `linked signers`, which is their delegation / one-click trading mechanism.
- The second-pass docs make that `one-click trading` story much more explicit than the first pass did:
  - the linked-signer guide directly says this is Nado's `1-Click Trading` feature
  - the UI flow is described as generating a random linked-signer key and storing it encrypted in the browser
  - that means Nado is still wallet-first, but the post-onboarding trading UX is more productized than a generic delegate-key model
- The linked-signer docs add important nuance:
  - linked signer setup itself is blocked until the subaccount already exists
  - the link request must be signed by the `main wallet` key, not the linked signer key
  - each subaccount can have exactly one linked signer
  - linked signers are optional; the main wallet always works
  - the current docs explicitly say a linked signer can do `ANYTHING` the main wallet can, including withdraw
- The current first-deposit docs are also more operationally helpful than the first pass captured:
  - they now separate `UI Deposit`, `On-Chain Contract Call`, and `Direct Deposit`
  - for developers, they frame the on-chain contract call as the recommended programmatic deposit method
- The current endpoints doc also lists gateway, archive, subscriptions, trigger, and v2 endpoints clearly for both mainnet and testnet.
- This is very clear and developer-friendly conceptually, but much less friendly for pure Web2 users.

Live probe:

- `https://app.nado.xyz` currently redirects to `/perpetuals`.
- `HEAD https://app.nado.xyz/perpetuals` returned `200`.
- A lightweight public HTML probe of `/perpetuals` did not expose obvious email-login or embedded-wallet vendor markers.
- A raw `curl` POST without compression headers is now blocked by the gateway with:
  - `Invalid compression headers: 'Accept-Encoding' must include 'gzip', 'br' or 'deflate'`
- Repeating the same gateway queries with `curl --compressed` succeeded.
- `POST https://gateway.test.nado.xyz/v1/query {"type":"status"}` returned:
  - `{"status":"success","data":"active"...}`
- `POST https://gateway.test.nado.xyz/v1/query {"type":"subaccount_info","subaccount":"0x41deec4e76e46c18719e90920c1efef370b7db0a64656661756c740000000000"}` returned:
  - `exists: false`
  - `spot_count: 5`
  - `perp_count: 43`
- `POST https://gateway.test.nado.xyz/v1/query {"type":"linked_signer","subaccount":"0x41deec4e76e46c18719e90920c1efef370b7db0a64656661756c740000000000"}` returned:
  - `linked_signer: 0x0000000000000000000000000000000000000000`
- `POST https://gateway.test.nado.xyz/v1/query {"type":"symbols"}` returned a large live symbol map including active products such as `BTC-PERP`, `SUI-PERP`, and spot `USDC`.
- `POST https://archive.test.nado.xyz/v1 {"subaccounts":{"address":"<wallet>"}}` returned:
  - `{"subaccounts":[]}`
- `POST https://archive.test.nado.xyz/v1 {"direct_deposit_address":{"subaccount":"<default-subaccount>"}}` returned:
  - `{"v1_address":"0x740a7e70262c143bb88d901001d141f986deda45"}`
- Local artifacts: `nado_probe_result.json` and `nado_second_pass_result.json`

Interpretation:

- Nado's gateway is live and directly queryable even before onboarding.
- But the deterministic `default` subaccount for this wallet does not exist yet, and no linked signer has been assigned.
- The archive/indexer results sharpen that boundary further:
  - `subaccounts[]` is still empty for the wallet
  - but a unique direct deposit address is already queryable for the deterministic `default` subaccount
- So Nado separates `pre-funding routing` from `subaccount existence`: you can know where to deposit before the subaccount exists, but the subaccount still stays `exists=false` until the first deposit lands.
- This cleanly confirms the docs claim that `first deposit creates the subaccount`, while also showing the deposit rail is already deterministic and queryable in advance.
- Operationally, today's gateway also appears to sit behind a front door that expects normal compression headers, so very low-level clients may need slightly more realistic HTTP defaults than a barebones curl.
- The second-pass update is mostly about product framing rather than raw protocol mechanics:
  - Nado still is not an embedded-wallet / email-first venue
  - but its linked-signer flow is more polished than a bare delegate-key primitive, because the UI deliberately packages it as `1-Click Trading`
- So the better current description is:
  - `wallet-first and non-Web2 at onboarding`
  - `clean and fairly productized once funded, especially if linked signer / 1-Click Trading is enabled`

Assessment:

- `Web2 friendliness`: low at onboarding, medium after deposit if `1-Click Trading` is enabled
- `API order usability`: medium for bots who are comfortable with wallet signing
- `Key friction`: no API-key abstraction layer; first deposit is a hard prerequisite, and linked-signer setup only comes after subaccount creation

Sources:

- https://docs.nado.xyz/developer-resources/get-started/core-concepts
- https://docs.nado.xyz/developer-resources/get-started/quickstart
- https://docs.nado.xyz/developer-resources/get-started/first-deposit
- https://docs.nado.xyz/developer-resources/get-started/linked-signers
- https://docs.nado.xyz/developer-resources/api/endpoints
- https://docs.nado.xyz/developer-resources/api/gateway/queries/linked-signer
- https://docs.nado.xyz/developer-resources/api/archive-indexer/direct-deposit-address

#### StandX

- StandX runs on `BNB Chain (BSC)` and `Solana`, using its proprietary yield-bearing stablecoin `DUSD` as margin.
- Team: former `Binance Futures` founding team + `Goldman Sachs` alumni.
- **Important**: the correct domain is `standx.com`, NOT `standx.trade` (which is a broken PHP deployment).
- Onboarding is `wallet-first` only — Connect Wallet is the primary entry point. No email/social login visible, no embedded wallet signals in CSP or HTML.
- Uses a `two-wallet system`: Cash Wallet (deposit holding) + Perps Wallet (active trading). Users deposit DUSD then transfer internally.
- Dedicated tutorial for Binance Wallet users.

API:

- Full REST + WebSocket trading API at `https://perps.standx.com`.
- Auth model: `JWT via wallet signature` — no traditional API keys. Self-custodial system.
  - Generate temporary `ed25519` key pair
  - `POST /v1/offchain/prepare-signin` → returns SIWE-style `signedData` JWT
  - Sign message with wallet (EVM ECDSA or Solana ed25519)
  - `POST /v1/offchain/login` → returns JWT token (default 7 days)
  - Body signature (`ed25519`) required for write operations (orders, cancels, transfers)
- Token management at `standx.com/user/session`: configurable permissions (Trade, Withdraw), expiry (7/30/90/180 days), revocable. Signing keys generated client-side only.
- Public endpoints: symbol info, market data, depth book, recent trades, funding rates, klines.
- Private read: orders, positions, balance.
- Private write: new_order, cancel, batch cancel, change leverage/margin mode, transfer margin.
- WebSocket: market stream + order execution via WS (`order:new`, `order:cancel`).
- Rate limits: token bucket ~22 req/sec sustained, 50 req/sec per IP.
- Only `4 markets`: BTC-USD, ETH-USD, XAG-USD, XAU-USD (all DUSD-margined, max 40x leverage).

Live probe (2026-03-21):

- `https://api.standx.com` returned `{"status":"ok"}`.
- `GET /api/query_symbol_info` returned 4 markets with full specs.
- `GET /api/query_symbol_market?symbol=BTC-USD` returned live data: last_price $70,701, volume_24h 4,230 BTC ($297M DUSD), OI 317 BTC ($22.4M).
- `POST /v1/offchain/prepare-signin?chain=bsc` with test wallet returned valid `signedData` JWT with SIWE message (chainId=56).
- `GET /api/query_balance` without auth returned `401 missing jwt`.
- `GET https://geo.standx.com/v1/region` returned region `TH` — geo-restrictions may apply.
- No official SDK found. Auth examples in TypeScript for EVM and SVM.

Assessment:

- `Web2 friendliness`: low. Wallet-first only.
- `API order usability`: high. Clean REST + WebSocket API, comparable to CEX APIs. Well-documented auth flow for both EVM and Solana.
- `Key friction`: must hold DUSD (not standard USDC/USDT), two-wallet transfer step, ed25519 body signature for writes, only 4 markets.
- `Unique`: DUSD yields APY while trading (interest-bearing collateral), dual-chain BSC+Solana with unified API.

Sources:

- https://docs.standx.com
- https://docs.standx.com/standx-api/standx-api
- https://docs.standx.com/standx-api/perps-http
- https://docs.standx.com/standx-api/perps-ws
- https://docs.standx.com/standx-api/perps-auth
- https://docs.standx.com/standx-api/perps-auth-evm-example
- https://docs.standx.com/standx-api/perps-auth-svm-example
- https://docs.standx.com/docs/stand-x-perps-solutions/api-token
- Result file: `standx_second_pass_result.json`

#### MYX Finance

- MYX Finance is a multi-chain perp DEX on `BNB Chain`, `Arbitrum`, `Linea`, and `opBNB`.
- Uses `Matching Pool Mechanism (MPM)` for zero-slippage by internally matching long/short positions.
- USDC-margined, up to 50x leverage, 37 trading pairs.
- $MYX token launched (rallied 1400%).
- V2 funded by `Consensys` (Feb 2026) — will become a `Modular Derivative Settlement Engine`. Not yet launched.

Onboarding:

- Dual-path: traditional wallet connection OR social login via `Particle Network` (email, phone, social).
- `Seamless Key` — MYX's proprietary delegated trading key:
  - Functions as an API key for programmatic/automated use
  - Master wallet signs password message → seed generates new EOA key pair → encrypted and stored locally
  - `Gas-free`: MYX relayer (Biconomy) sponsors gas, fees deducted in USDC
  - Non-custodial: Seamless Key carries no assets, all funds stay in Master wallet
  - ERC20 Permit for USDC authorization, order nonce for replay protection
- New user flow: Create wallet via social login → Purchase USDC via credit card → Create Seamless Key.

API:

- Only `2 public REST endpoints` documented at `https://api.myx.finance`:
  - `GET /v2/quote/market/contracts` — list all 37 pairs (no auth)
  - `GET /v2/quote/market/contract_specs` — pair specs (no auth)
- **No off-chain REST trading API** — all trading is `on-chain` via smart contract calls (Router.sol).
- Smart contract methods: `createIncreaseOrder`, `createDecreaseOrder`, `cancelOrder`, etc.
- No WebSocket API documented.
- No official SDK.

JS bundle signals (2026-03-21):

- `Particle Network` (PARTICLE) — social login / embedded wallet
- `Biconomy` (BICONOMY) — account abstraction / gasless relayer
- `WalletConnect`, `ConnectKit`, `RainbowKit` — wallet connection
- `Dynamic.xyz` (Dynamic) — wallet infrastructure
- `Magic.link` (MAGIC) — email-based wallet
- `Safe` (SAFE) — smart accounts
- `Wagmi`, `Viem`, `Ethers` — Ethereum libraries
- `4337`, `7702` — EIP references for account abstraction
- This is the broadest wallet infrastructure stack in the entire sample.

V2 upgrade:

- Architecture: Modular Derivative Settlement Engine — other platforms can build on top.
- EIP-4337 + EIP-7702 for gasless one-click trading.
- Chainlink Permissionless Oracle Stack.
- Chain Abstraction: collateral across 20+ networks.
- Launch date: not yet announced.

Live probe (2026-03-21):

- `GET /v2/quote/market/contracts` returned 37 pairs across BNB Chain, Arbitrum, Linea.
- `GET /v2/quote/market/contract_specs?ticker_id=BTC-USDC` returned specs (contract_type: Vanilla, currency: USDC).
- `app.myx.finance` CSP is minimal (`upgrade-insecure-requests` only) — vendor signals are all in JS bundles.
- GitHub repo (`myx-protocol/myx-contracts`) is Solidity-only, no consumer SDK.
- Audits: PeckShield (2 reports), SlowMist (5 phased).

Assessment:

- `Web2 friendliness`: high — Particle Network social login + Seamless Key gasless trading + credit card USDC purchase.
- `API order usability`: low for REST API developers. No off-chain trading API. Must interact with smart contracts or use Seamless Key (on-chain delegated signer).
- `Key friction`: no REST order API, smart contract integration requires Solidity knowledge, no SDK.
- `Unique`: zero-slippage MPM, broadest wallet infra stack in sample (Particle + Biconomy + Dynamic + Magic + Safe + WalletConnect), V2 backed by Consensys.

Sources:

- https://myxfinance.gitbook.io/myx
- https://myxfinance.gitbook.io/myx/protocol/api
- https://myxfinance.gitbook.io/myx/trading-mechanism/introducing-myx-seamless-trading
- https://github.com/myx-protocol/myx-contracts
- https://decrypt.co/358412/myx-completes-strategic-funding-round-led-by-consensys-ahead-of-v2-launch
- Result file: `myx_second_pass_result.json`

### Practical Ranking

#### Best for Web2-user conversion

1. `GRVT`
2. `trade[XYZ]`
3. `Aster`
4. `EdgeX`
5. `Hyperliquid`

#### Best for pro/API traders

1. `Paradex`
2. `Extended`
3. `Hyperliquid`
4. `Lighter`
5. `Ethereal`

#### Most initialization-heavy before first API order

1. `EdgeX`
2. `Aster`
3. `Ethereal`
4. `GRVT`
5. `Nado`

### What This Means For Next Hands-on Testing

The first-pass sweep across all `11` platforms is now complete.

If continuing with second-pass activation testing, the next best order is:

1. `Paradex`
2. `Hyperliquid`
3. `Aster`
4. `Nado`
5. `Lighter`
6. `GRVT`
7. `Ethereal`
8. `EdgeX`
9. `Extended`
10. `trade[XYZ]`
11. `Variational`

Rationale:

- `Paradex` now has the cleanest remaining solvable blocker: the live probe narrowed failure to `minimum external chain balance` and then `NOT_ONBOARDED`, so a funded second pass could materially upgrade confidence.
- `Hyperliquid` still matters because the remaining uncertainty is also specific and testable: `Enable Trading` plus real activated HyperCore state, though it is operationally heavier because the official faucet flow references same-address mainnet funding.
- `Aster`, `Nado`, and `Lighter` all still have meaningful second-pass value because their remaining unknowns are downstream of a known first blocker: builder/user authorization, first deposit-created subaccount, and credited deposit-created account index respectively.
- `GRVT`, `Ethereal`, and `EdgeX` can sit behind those because their first-pass boundary conditions are now already quite clear.
- `Extended` already has the strongest live write-path validation in the set, so more testing there is useful but lower urgency.
- `trade[XYZ]` depends heavily on the underlying `Hyperliquid` activation story, so it should trail Hyperliquid rather than lead it.
- `Variational` now drops to the bottom because the current live product is `Omni`, `Pro` is explicitly not live, the public trading API is still unavailable, and the old `Pro` API docs/hostnames already show `404` / non-resolving behavior today.
