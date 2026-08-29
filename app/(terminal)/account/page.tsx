"use client";

import { useRouter } from "next/navigation";

import { useCurrentUser } from "@/hooks/use-current-user";
import { logoutUser } from "@/services/auth-client-service";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function AccountPage() {
  const router = useRouter();
  const { data: user, isLoading } = useCurrentUser();

  async function handleLogout() {
    await logoutUser();
    router.push("/login");
    router.refresh();
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Account" description="Your AIMAG account" />

      {isLoading ? (
        <Skeleton className="h-40 rounded-xl" />
      ) : (
        <Card className="max-w-md">
          <CardContent className="space-y-4 pt-6">
            <div>
              <p className="text-xs text-muted-foreground">Email</p>
              <p className="text-sm text-foreground">{user?.email}</p>
            </div>
            {user?.displayName ? (
              <div>
                <p className="text-xs text-muted-foreground">Name</p>
                <p className="text-sm text-foreground">{user.displayName}</p>
              </div>
            ) : null}
            <div>
              <p className="text-xs text-muted-foreground">Role</p>
              <p className="text-sm text-foreground">{user?.role}</p>
            </div>
            <Button variant="outline" onClick={handleLogout}>
              Sign out
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
