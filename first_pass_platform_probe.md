# First Pass Platform Probe

Date: 2026-03-21
Wallet under test: `0x41Deec4e76e46c18719E90920C1efef370B7DB0A`
Scope: `Extended`, `Ethereal`, `GRVT`, `EdgeX`
Mode: `testnet / zero real funds`

## Summary

| Platform | Web2-friendly onboarding signal | Wallet/AA signal | API write-path readiness from raw EVM wallet | First-pass result |
| --- | --- | --- | --- | --- |
| Extended | Weak on public landing flow; public trade page shows `Connect Wallet` | Wallet-first; API requires API key + Stark key per subaccount | Not ready from raw EVM wallet alone; needs UI/SDK onboarding and Stark key material | Public API/docs confirmed, private trading path has high setup overhead |
| Ethereal | Weak on public landing flow; public trade page shows `Connect Wallet` | EOA + subaccount + linked signer model | Partially ready; public API works, but this wallet has no subaccount yet | Public endpoints probed successfully; trading blocked until subaccount creation |
| GRVT | Strongest of this batch; help docs show wallet + email hybrid sign-up | Wallet login + email linking; API key or wallet login | Almost ready, but wallet must be registered first in UI | Live wallet-login probe returned `wallet address not registered` |
| EdgeX | Public trade page shows `Connect Wallet`; API access is separately promoted | Docs and page copy suggest wallet-first; API is professional/HFT-oriented | Not ready from raw EVM wallet alone; likely needs account setup plus L2-specific signing | Public UI and private order API docs confirmed; write path is specialized |

## Live Evidence

### GRVT

- Official help flow indicates hybrid onboarding:
  - Wallet connect
  - Email connect for sign-up
  - Signature confirmation
- Official API supports both:
  - API key login
  - Direct EIP-712 wallet login
- Live wallet login probe against testnet:
  - Endpoint: `https://edge.testnet.grvt.io/auth/wallet/login`
  - Result: `401`
  - Body: `{"status":401,"message":"wallet address not registered"}`

Interpretation:

- GRVT has the cleanest path for Web2 migration in this batch.
- However, raw API wallet login is not a true "first-touch onboarding" primitive.
- The wallet must be registered through the product flow first.

### Ethereal

- Public API is fully reachable.
- Confirmed public product endpoint returns market data.
- Confirmed `rpc/config` exposes the EIP-712 domain and signature schemas.
- Wallet-specific probes:
  - `GET /v1/subaccount?sender=<wallet>` returned `{"data":[],"hasNext":false}`
  - `GET /v1/linked-signer/address/<wallet>` returned `404 Signer not found`

Interpretation:

- Ethereal is developer-friendly at the schema level.
- But a fresh EVM wallet cannot trade immediately through API.
- It first needs a subaccount, then optionally a linked signer for delegated trading / one-click trading.

### Extended

- Public trade page is reachable and immediately presents `Connect Wallet`.
- Official API docs explicitly state:
  - Account can be created through UI or SDK
  - API management page provides API keys, Stark keys, and vault numbers
  - Order management requires both API key and Stark signature
  - Testnet offers daily test USDC claim

Interpretation:

- Extended is friendly for a trader once inside the product.
- It is not friendly for "fresh wallet -> immediate API order" from a raw EVM key.
- It has the highest setup burden in this batch because its private path depends on StarkEx-specific account material.

### EdgeX

- Public trade page is reachable and shows `Connect Wallet`.
- More menu explicitly advertises `API` and says `Apply for access`.
- Official private order docs show highly specialized parameters:
  - `l2Nonce`
  - `l2Value`
  - `l2LimitFee`
  - `l2ExpireTime`
  - `l2Signature`

Interpretation:

- EdgeX appears optimized for advanced/professional API use rather than fast retail onboarding.
- API usability will depend heavily on SDK/reference-client quality because manual signing is non-trivial.

## Key Takeaways

1. `GRVT` currently looks best for Web2 users because it visibly mixes wallet and email.
2. `Ethereal` has the cleanest developer-facing public schema among this batch.
3. `Extended` and `EdgeX` both expose powerful APIs, but their real trading path is materially harder because of exchange-specific signing/account systems.
4. None of the four currently behaves like "drop in any fresh EVM wallet and immediately place API testnet orders" without an initialization step.

## Recommended Next Actions

1. Complete UI registration on `GRVT` with the test wallet, then rerun the wallet-login probe and attempt authenticated private reads.
2. Create the first `Ethereal` subaccount in UI, then link an API signer and test delegated order flow.
3. For `Extended`, inspect the SDK onboarding example and determine whether account creation can be fully scripted from the raw test wallet.
4. For `EdgeX`, inspect account/auth API docs and determine whether API access must be manually approved or whether a self-service path exists.
