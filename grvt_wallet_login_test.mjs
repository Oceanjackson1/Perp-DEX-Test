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
