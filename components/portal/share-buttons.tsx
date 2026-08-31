"use client";

import { useState } from "react";
import { Check, Copy, Send } from "lucide-react";

import { cn } from "@/lib/utils";

interface ShareButtonsProps {
  url: string;
  title: string;
  copyLabel: string;
  copiedLabel: string;
}

// Minimal inline mark for X/Twitter — lucide-react (^1.25.0, installed
// here) dropped its dedicated Twitter/X icon, so this is the smallest
// faithful reproduction rather than a generic "share" glyph in its place.
function XIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor" aria-hidden="true">
      <path d="M18.9 2.25h3.68l-8.04 9.19L24 21.75h-7.41l-5.8-7.58-6.64 7.58H.46l8.6-9.83L0 2.25h7.6l5.24 6.93zm-1.29 17.3h2.04L6.48 4.34H4.3z" />
    </svg>
  );
}

export function ShareButtons({ url, title, copyLabel, copiedLabel }: ShareButtonsProps) {
  const [copied, setCopied] = useState(false);

  const twitterHref = `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`;
  const telegramHref = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`;

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard permission denied or unavailable — nothing useful to
      // recover into, the button just silently stays unclicked.
    }
  }

  const buttonClass =
    "inline-flex size-8 items-center justify-center rounded-md border border-border-strong text-muted-foreground transition-colors hover:border-accent hover:text-accent";

  return (
    <div className="flex items-center gap-1.5">
      <a href={twitterHref} target="_blank" rel="noopener noreferrer" className={buttonClass} aria-label="X">
        <XIcon className="size-3.5" />
      </a>
      <a href={telegramHref} target="_blank" rel="noopener noreferrer" className={buttonClass} aria-label="Telegram">
        <Send className="size-3.5" />
      </a>
      <button
        type="button"
        onClick={copyLink}
        className={cn(buttonClass, copied && "border-accent text-accent")}
        aria-label={copied ? copiedLabel : copyLabel}
        title={copied ? copiedLabel : copyLabel}
      >
        {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
      </button>
    </div>
  );
}
