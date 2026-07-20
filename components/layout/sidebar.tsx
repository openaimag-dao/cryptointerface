"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { ChevronsLeft, ChevronsRight, Zap } from "lucide-react";

import { NAV_ITEMS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/store/ui-store";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export function Sidebar() {
  const pathname = usePathname();
  const collapsed = useUiStore((state) => state.sidebarCollapsed);
  const toggleSidebar = useUiStore((state) => state.toggleSidebar);

  return (
    <motion.aside
      animate={{ width: collapsed ? 76 : 248 }}
      initial={false}
      transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
      className="sticky top-0 z-40 flex h-screen shrink-0 flex-col border-r border-border-subtle bg-surface/80 backdrop-blur-xl"
    >
      <div className={cn("flex h-16 items-center gap-2.5 px-4", collapsed && "justify-center px-0")}>
        <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-accent-dim text-accent shadow-[0_0_20px_rgba(0,230,118,0.25)]">
          <Zap className="size-[18px]" strokeWidth={2.5} />
        </div>
        {!collapsed && (
          <span className="whitespace-nowrap text-sm font-bold tracking-wide text-foreground">
            AIMAG <span className="text-accent">AI</span>
          </span>
        )}
      </div>

      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto px-3 py-2">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;

          const link = (
            <Link
              href={item.href}
              className={cn(
                "group relative flex h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-white/[0.05] hover:text-foreground",
                collapsed && "justify-center px-0",
                isActive && "bg-accent-dim text-accent hover:bg-accent-dim hover:text-accent",
              )}
            >
              {isActive && (
                <motion.span
                  layoutId="sidebar-active-indicator"
                  className="absolute left-0 h-5 w-0.5 rounded-full bg-accent"
                  transition={{ duration: 0.2 }}
                />
              )}
              <Icon className="size-[18px] shrink-0" strokeWidth={isActive ? 2.4 : 2} />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </Link>
          );

          if (!collapsed) return <div key={item.href}>{link}</div>;

          return (
            <Tooltip key={item.href}>
              <TooltipTrigger asChild>{link}</TooltipTrigger>
              <TooltipContent side="right">{item.label}</TooltipContent>
            </Tooltip>
          );
        })}
      </nav>

      <div className="border-t border-border-subtle p-3">
        <button
          type="button"
          onClick={toggleSidebar}
          className={cn(
            "flex h-9 w-full items-center justify-center gap-2 rounded-lg text-muted-foreground transition-colors hover:bg-white/[0.05] hover:text-foreground",
          )}
        >
          {collapsed ? <ChevronsRight className="size-4" /> : <ChevronsLeft className="size-4" />}
          {!collapsed && <span className="text-xs font-medium">Collapse</span>}
        </button>
      </div>
    </motion.aside>
  );
}
