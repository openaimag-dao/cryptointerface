import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  // Editorial serif treatment for the public News Portal's section
  // headings — the private terminal's dashboard-style pages leave this
  // off and keep the default sans weight.
  serif?: boolean;
}

export function PageHeader({ title, description, actions, serif }: PageHeaderProps) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1
          className={cn(
            "text-xl font-semibold tracking-tight text-foreground",
            serif && "font-serif text-3xl font-semibold",
          )}
        >
          {title}
        </h1>
        {description ? <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{description}</p> : null}
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </div>
  );
}
