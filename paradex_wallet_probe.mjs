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
