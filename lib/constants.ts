import {
  Activity,
  Bot,
  Flame,
  Globe2,
  LayoutDashboard,
  LineChart,
  MessageSquareText,
  Newspaper,
  Settings,
  Wallet,
  Waves,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: typeof LayoutDashboard;
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Markets", href: "/markets", icon: LineChart },
  { label: "AI Signals", href: "/signals", icon: Bot },
  { label: "Whale Tracker", href: "/whales", icon: Waves },
  { label: "Liquidations", href: "/liquidations", icon: Flame },
  { label: "News", href: "/news", icon: Newspaper },
  { label: "Macro", href: "/macro", icon: Globe2 },
  { label: "Portfolio", href: "/portfolio", icon: Wallet },
  { label: "Backtesting", href: "/backtesting", icon: Activity },
  { label: "AI Chat", href: "/ai-chat", icon: MessageSquareText },
  { label: "Settings", href: "/settings", icon: Settings },
];
