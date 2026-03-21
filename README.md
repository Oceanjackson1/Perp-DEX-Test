# Perp DEX Research & Testing Suite

A comprehensive research and live-testing framework for **13 perpetual futures decentralized exchanges (Perp DEXs)**, focusing on onboarding friction, embedded wallet infrastructure, API authentication models, and programmatic trading readiness.

## Overview

This project systematically probes and analyzes the onboarding experience and API maturity of major Perp DEX platforms from two key perspectives:

1. **Web2 Onboarding Friendliness** — How easy is it for a non-crypto-native user (email/social login) to start trading?
2. **API-First Developer Experience** — How quickly can a fresh EVM wallet reach its first programmatic order?

All tests use a single fresh EVM test wallet against testnet/public endpoints with zero real funds.

## Platforms Covered

| # | Platform | Login Model | Embedded Wallet | API Auth | Fresh Wallet Friction |
|---|----------|-------------|-----------------|----------|----------------------|
| 1 | **Hyperliquid** | Wallet + Email (Privy) | Privy email wallet | Raw wallet signing / agent wallet | Medium-low |
| 2 | **Aster** | Wallet + Email | Native email wallet | API key + HMAC SHA256 | Medium |
| 3 | **trade[XYZ]** | Wallet + Privy email | Privy | Hyperliquid API underneath | Medium |
| 4 | **EdgeX** | Wallet + Email MPC | Privy (CSP-confirmed) | API key + L2 signature | Low (complex setup) |
| 5 | **Variational** | Wallet (Omni) | None | Read-only (trading API not ready) | Unavailable |
| 6 | **Lighter** | Wallet + Deposit | None | API key + auth token + nonce | Low (deposit-first) |
| 7 | **GRVT** | Web2 OAuth (Google/Apple/Microsoft/Email) | Dfns MPC + Privy dual | Session cookie / API key | Low (7-step chain + KYC) |
| 8 | **Extended** | Wallet-first | Dynamic.xyz (hidden in JS bundle) | API key + Stark signature | High on testnet |
| 9 | **Paradex** | Wallet + Privy email/social | Privy + Argent | JWT + Starknet subkey | Medium |
| 10 | **Ethereal** | Wallet-first | Privy + Fun.xyz (undocumented) | EIP-712 per-action signing | Low (deposit required) |
| 11 | **Nado** | Wallet-first | None | Pure wallet signatures | Low (deposit-first) |
| 12 | **StandX** | Wallet (BSC + Solana) | None | JWT via SIWE + ed25519 body sig | Medium-high |
| 13 | **MYX Finance** | Wallet + Particle Network social | Particle + Biconomy AA | On-chain only (no REST trading) | Low for API-first |

## Key Findings

### Embedded Wallet Landscape

**Privy appears in 7 of 13 platforms** — often discovered only through CSP header analysis and JS bundle inspection, not official documentation.

Notable discoveries through second-pass probing:
- **Ethereal**: Privy + Fun.xyz + MoonPay — completely undocumented in dev guides
- **Extended**: Dynamic.xyz embedded in JS bundle — not mentioned in docs
- **EdgeX**: Privy confirmed via CSP headers — docs only described generic "MPC email"
- **MYX Finance**: Broadest stack (Particle + Biconomy + Dynamic + Magic + Safe + WalletConnect + ConnectKit + RainbowKit)

### Web2-Friendliest Onboarding

1. **GRVT** — Full OAuth (email + Google + Apple + Microsoft) + Dfns/Privy SecureKey
2. **trade[XYZ]** — Privy email wallet with minimal friction
3. **Aster** — Native email login + wallet creation

### Most API-Mature (Fastest to First Order)

1. **Extended** — Full testnet write-path proven (onboard → API key → fund → trade → cancel)
2. **StandX** — Clean CEX-like REST + WebSocket API
3. **Hyperliquid** — Well-documented agent wallet pattern

## Project Structure

```
.
├── README.md
│
├── # ── Research Reports ──────────────────────────
├── perp_dex_complete_report_20260321.md    # Full 97KB report (all 13 platforms)
├── full_perp_dex_research_20260321.md      # Research matrix with detailed analysis
├── first_pass_platform_probe.md            # Initial findings (Extended, Ethereal, GRVT, EdgeX)
│
├── # ── Probe Scripts ─────────────────────────────
├── extended_onboarding_probe.py            # Extended: SDK account creation + API key
├── extended_write_probe.py                 # Extended: Full write-path (onboard→trade→cancel)
├── hyperliquid_safe_probe.py               # Hyperliquid: SDK wallet state + signed actions
├── paradex_wallet_probe.mjs                # Paradex: EVM→Starknet key derivation + EIP-712
├── grvt_wallet_login_test.mjs              # GRVT: EIP-712 wallet login + session capture
│
├── # ── Probe Results (JSON) ──────────────────────
├── # First-pass results
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
├── # Second-pass results (deeper analysis)
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
├── # ── Paradex Config Artifacts ──────────────────
├── paradex_testnet_config.json             # Paradex testnet system config
├── paradex_probe_payload.json              # EIP-712 onboarding payload
│
├── # ── Dependencies ──────────────────────────────
├── package.json                            # Node.js deps (ethers, starknet)
└── package-lock.json
```

## Research Methodology

The research follows a **two-pass methodology**:

### First Pass — Documentation & Public Probing
- Official documentation review (GitBook, Notion, GitHub, API docs)
- Public API endpoint testing (zero-auth reads)
- SDK installation and basic connection tests

### Second Pass — Deep Technical Probing
- **CSP Header Extraction** — Reveal hidden embedded wallet providers from production frontends
- **JS Bundle Analysis** — Detect vendor SDKs (Privy, Dynamic.xyz, Fun.xyz, Particle, etc.)
- **Live API Probes** — Authenticated and unauthenticated endpoint testing
- **SDK Write-Path Tests** — Full onboard → fund → trade → cancel cycles where possible
- **OpenAPI/Swagger Spec Analysis** — Endpoint enumeration and schema validation
- **DNS Resolution Checks** — Verify legacy/stale endpoints

## Tech Stack

### Node.js (JavaScript/ESM)
- **ethers** v6.16.0 — EVM wallet operations, EIP-712 typed data signing
- **starknet** v9.4.2 — Starknet L2 account operations
- **@starkware-industries/starkware-crypto-utils** v0.2.1 — Stark key derivation from EVM signatures

### Python 3.11
- **Extended SDK** (x10 perpetual) — Account onboarding, API key creation, trading
- **Hyperliquid SDK** — Exchange client, wallet signing, market queries
- **eth_account** / **requests** — EVM wallet loading, HTTP probes

## Setup

### Prerequisites
- Node.js 18+
- Python 3.11+

### Installation

```bash
# Install Node.js dependencies
npm install

# Set up Python environment for Extended SDK
python3.11 -m venv .pydeps311
source .pydeps311/bin/activate
pip install x10-perpetual eth-account requests

# Set up Python environment for Hyperliquid SDK
python3.11 -m venv .pydeps_hl
source .pydeps_hl/bin/activate
pip install hyperliquid-python-sdk eth-account
```

### Running Probes

```bash
# Paradex: Starknet key derivation + onboarding probe
node paradex_wallet_probe.mjs

# GRVT: Wallet login test
node grvt_wallet_login_test.mjs

# Extended: Full write-path test (requires testnet funds)
source .pydeps311/bin/activate
python extended_write_probe.py

# Hyperliquid: Wallet state + safe order probe
source .pydeps_hl/bin/activate
python hyperliquid_safe_probe.py
```

> **Note:** Most write-path probes require testnet funds in the wallet. Read-only probes work with a fresh wallet.

## API Auth Taxonomy

The 13 platforms use four distinct authentication models:

| Model | Platforms |
|-------|-----------|
| **JWT / Session Cookie** | GRVT, StandX |
| **API Key + HMAC** | Aster (Pro API), Lighter, Extended |
| **Raw Wallet Signing** | Hyperliquid, Nado, Ethereal, trade[XYZ] |
| **L2 Key Derivation** | Paradex (Starknet), EdgeX (custom L2) |

## License

This research is provided for educational and analytical purposes.

## Disclaimer

- All testing was conducted on **testnets** or **public read-only endpoints** with zero real funds
- No private API keys or production credentials were compromised during research
- Findings reflect platform state as of **2026-03-21** and may change as platforms evolve
- This is independent research and is not affiliated with any of the platforms analyzed
