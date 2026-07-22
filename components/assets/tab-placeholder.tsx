import { Card, CardContent } from "@/components/ui/card";

export function TabPlaceholder({ label }: { label: string }) {
  return (
    <Card>
      <CardContent className="flex h-40 items-center justify-center pt-5">
        <p className="text-sm text-muted-foreground">{label} is coming in a future update.</p>
      </CardContent>
    </Card>
  );
}
