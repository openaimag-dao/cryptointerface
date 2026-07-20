export type WhaleTxType = "TRANSFER" | "DEPOSIT" | "WITHDRAWAL" | "SWAP";

export interface WhaleTransaction {
  id: string;
  symbol: string;
  type: WhaleTxType;
  amount: number;
  amountUsd: number;
  from: string;
  to: string;
  exchange: string | null;
  timestamp: string;
  txHash: string;
}
