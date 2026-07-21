/**
 * Mirrors the backend's Whale Engine response shape (see
 * backend/app/schemas/whale.py). Transfers are Etherscan-tracked (ETH +
 * a small set of ERC-20 tokens) touching a curated list of known exchange
 * wallets, classified deterministically — see
 * backend/app/intelligence/whales/classifier.py.
 */
export type WhaleWalletType = "EXCHANGE" | "UNKNOWN";
export type WhaleDirection = "TO_EXCHANGE" | "FROM_EXCHANGE";

export interface WhaleTransaction {
  id: string;
  asset: string;
  amount: number;
  usdValue: number;
  walletType: WhaleWalletType;
  direction: WhaleDirection;
  exchange: string | null;
  confidence: number;
  fromAddress: string;
  toAddress: string;
  txHash: string;
  timestamp: string;
}
