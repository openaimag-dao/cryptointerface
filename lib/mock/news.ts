import type { NewsItem } from "@/types";

const NEWS_SEEDS: Omit<NewsItem, "id" | "publishedAt">[] = [
  {
    title: "Bitcoin ETF inflows hit $620M as institutional demand accelerates",
    summary: "Spot Bitcoin ETFs recorded their largest single-day inflow in three months, led by BlackRock's IBIT.",
    source: "Bloomberg Crypto",
    sentiment: "BULLISH",
    tags: ["BTC", "ETF", "Institutional"],
    url: "#",
  },
  {
    title: "Ethereum staking withdrawals spike ahead of network upgrade",
    summary: "Analysts note the surge is largely rotational as validators reposition for the upcoming Pectra upgrade.",
    source: "The Block",
    sentiment: "NEUTRAL",
    tags: ["ETH", "Staking"],
    url: "#",
  },
  {
    title: "Solana DEX volume surpasses Ethereum for third consecutive week",
    summary: "On-chain data shows sustained retail and bot activity driving Solana's DeFi ecosystem growth.",
    source: "CoinDesk",
    sentiment: "BULLISH",
    tags: ["SOL", "DeFi"],
    url: "#",
  },
  {
    title: "Regulators signal tighter scrutiny on stablecoin reserves",
    summary: "A new proposal could require weekly attestations for issuers with more than $10B in circulation.",
    source: "Reuters",
    sentiment: "BEARISH",
    tags: ["Regulation", "Stablecoins"],
    url: "#",
  },
  {
    title: "Whale wallets accumulate 18,000 BTC over the past 48 hours",
    summary: "On-chain trackers flagged unusually large cold-wallet inflows coinciding with reduced exchange supply.",
    source: "Glassnode Insights",
    sentiment: "BULLISH",
    tags: ["BTC", "Whales", "On-chain"],
    url: "#",
  },
  {
    title: "Funding rates turn negative across major perpetual markets",
    summary: "Short positioning has increased sharply, a contrarian signal some traders read as bullish.",
    source: "CoinGlass",
    sentiment: "NEUTRAL",
    tags: ["Derivatives", "Funding"],
    url: "#",
  },
  {
    title: "Macro headwinds: Fed minutes hint at delayed rate cuts",
    summary: "Risk assets wobbled after FOMC minutes showed officials favor a cautious approach through Q3.",
    source: "Wall Street Journal",
    sentiment: "BEARISH",
    tags: ["Macro", "Fed"],
    url: "#",
  },
  {
    title: "Chainlink expands CCIP integrations with three new L2 networks",
    summary: "The cross-chain protocol now supports over 40 networks, boosting institutional interoperability use cases.",
    source: "The Defiant",
    sentiment: "BULLISH",
    tags: ["LINK", "Infrastructure"],
    url: "#",
  },
];

export function getMockNews(): NewsItem[] {
  return NEWS_SEEDS.map((item, index) => ({
    ...item,
    id: `news-${index}`,
    publishedAt: new Date(Date.now() - index * 1000 * 60 * 47).toISOString(),
  }));
}
