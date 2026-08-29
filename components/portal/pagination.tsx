import Link from "next/link";

interface PortalPaginationProps {
  basePath: string;
  page: number;
  totalPages: number;
  // Extra query params to carry across page links (e.g. a search page's
  // ?q=...) — merged in alongside `page`.
  extraParams?: Record<string, string>;
}

export function PortalPagination({ basePath, page, totalPages, extraParams }: PortalPaginationProps) {
  if (totalPages <= 1) return null;

  function hrefForPage(targetPage: number): string {
    const params = new URLSearchParams(extraParams);
    params.set("page", String(targetPage));
    return `${basePath}?${params.toString()}`;
  }

  const prevHref = page > 1 ? hrefForPage(page - 1) : null;
  const nextHref = page < totalPages ? hrefForPage(page + 1) : null;

  return (
    <nav className="mt-8 flex items-center justify-between text-sm" aria-label="Pagination">
      {prevHref ? (
        <Link href={prevHref} className="text-muted-foreground transition-colors hover:text-foreground">
          ← Previous
        </Link>
      ) : (
        <span />
      )}
      <span className="text-xs text-muted-foreground">
        Page {page} of {totalPages}
      </span>
      {nextHref ? (
        <Link href={nextHref} className="text-muted-foreground transition-colors hover:text-foreground">
          Next →
        </Link>
      ) : (
        <span />
      )}
    </nav>
  );
}
