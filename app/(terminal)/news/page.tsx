import { PageHeader } from "@/components/common/page-header";
import { NewsFeed } from "@/components/news/news-feed";

export default function NewsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="News" description="Curated market-moving headlines with AI sentiment tagging" />
      <NewsFeed />
    </div>
  );
}
