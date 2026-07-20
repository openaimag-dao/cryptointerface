"use client";

import * as React from "react";
import * as SwitchPrimitive from "@radix-ui/react-switch";

import { cn } from "@/lib/utils";

function Switch({ className, ...props }: React.ComponentProps<typeof SwitchPrimitive.Root>) {
  return (
    <SwitchPrimitive.Root
      data-slot="switch"
      className={cn(
        "peer inline-flex h-5 w-9 shrink-0 items-center rounded-full border border-border-subtle bg-white/[0.06] transition-colors data-[state=checked]:border-accent/40 data-[state=checked]:bg-accent-dim disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    >
      <SwitchPrimitive.Thumb
        data-slot="switch-thumb"
        className={cn(
          "pointer-events-none block size-3.5 translate-x-1 rounded-full bg-muted-foreground shadow transition-transform data-[state=checked]:translate-x-[18px] data-[state=checked]:bg-accent",
        )}
      />
    </SwitchPrimitive.Root>
  );
}

export { Switch };
