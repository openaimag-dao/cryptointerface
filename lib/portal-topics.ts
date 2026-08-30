import type { PortalTopic } from "@/types";

export interface PortalTopicDef {
  slug: string;
  value: PortalTopic;
  label: string;
  description: string;
}

export const PORTAL_TOPICS: PortalTopicDef[] = [
  { slug: "crypto", value: "CRYPTO", label: "Crypto", description: "Markets, exchanges, and on-chain activity" },
  { slug: "ai", value: "AI", label: "AI", description: "Artificial intelligence research, products, and policy" },
  {
    slug: "blockchain",
    value: "BLOCKCHAIN",
    label: "Blockchain",
    description: "Protocols, infrastructure, and Web3 development",
  },
  { slug: "innovation", value: "INNOVATION", label: "Innovation", description: "Emerging tech across the industry" },
];

export function portalTopicForSlug(slug: string): PortalTopicDef | undefined {
  return PORTAL_TOPICS.find((topic) => topic.slug === slug);
}

export function portalTopicForValue(value: PortalTopic): PortalTopicDef | undefined {
  return PORTAL_TOPICS.find((topic) => topic.value === value);
}
