import Link from "next/link";

interface PortalPaginationProps {
  basePath: string;
  page: number;
  totalPages: number;
}

export function PortalPagination({ basePath, page, totalPages }: PortalPaginationProps) {
  if (totalPages <= 1) return null;

  const prevHref = page > 1 ? `${basePath}?page=${page - 1}` : null;
  const nextHref = page < totalPages ? `${basePath}?page=${page + 1}` : null;

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
