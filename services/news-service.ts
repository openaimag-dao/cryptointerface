import { getMockNews } from "@/lib/mock/news";
import { mockDelay } from "@/lib/mock/delay";
import type { NewsItem } from "@/types";

export async function fetchNews(): Promise<NewsItem[]> {
  return mockDelay(getMockNews());
}
