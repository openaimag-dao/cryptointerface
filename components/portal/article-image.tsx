"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";

interface ArticleImageProps {
  src: string;
  className: string;
  // Wraps the image in a link (news-card thumbnails); omit for a static
  // hero image that isn't itself clickable (the article page).
  href?: string;
}

/**
 * A real image URL from the source's own RSS feed can go stale (the
 * publisher deletes or moves it) well after we've stored it, so this has
 * to fail gracefully — the whole element disappears rather than leaving a
 * broken-image icon sitting in an otherwise-empty box. Client-only
 * because detecting the load failure needs `onError`.
 */
export function ArticleImage({ src, className, href }: ArticleImageProps) {
  const [failed, setFailed] = useState(false);
  if (failed) return null;

  const image = (
    <Image
      src={src}
      alt=""
      width={800}
      height={450}
      unoptimized
      className={href ? "size-full object-cover" : className}
      onError={() => setFailed(true)}
    />
  );

  if (href) {
    return (
      <Link href={href} className={className}>
        {image}
      </Link>
    );
  }
  return image;
}
