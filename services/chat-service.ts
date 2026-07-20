import { mockDelay } from "@/lib/mock/delay";

const STUB_RESPONSES = [
  "This is a placeholder response. In Sprint 2, this will be powered by the AIMAG AI reasoning engine connected to live Binance data.",
  "I don't have live market access yet — once the AI module is connected, I'll be able to analyze this in real time.",
  "Great question. For now this terminal runs on mock data; the AI Chat backend will be wired up in the next sprint.",
];

export async function sendChatMessage(): Promise<string> {
  const response = STUB_RESPONSES[Math.floor(Math.random() * STUB_RESPONSES.length)];
  return mockDelay(response, 700);
}
