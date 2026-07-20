"use client";

import { useEffect, useState, type ReactNode } from "react";
import { KeyRound, Palette, ShieldAlert } from "lucide-react";

import { useTheme } from "next-themes";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

function SettingsRow({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-6 py-4">
      <div>
        <p className="text-sm font-medium text-foreground">{title}</p>
        <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
      </div>
      {children}
    </div>
  );
}

export function NotificationSettings() {
  const [priceAlerts, setPriceAlerts] = useState(true);
  const [signalAlerts, setSignalAlerts] = useState(true);
  const [liquidationAlerts, setLiquidationAlerts] = useState(false);
  const [newsDigest, setNewsDigest] = useState(true);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-foreground">
          <ShieldAlert className="size-4 text-accent" />
          Notifications
        </CardTitle>
        <CardDescription>Choose which alerts AIMAG AI sends you</CardDescription>
      </CardHeader>
      <CardContent className="divide-y divide-border-subtle pt-0">
        <SettingsRow title="Price Alerts" description="Notify me on significant price moves">
          <Switch checked={priceAlerts} onCheckedChange={setPriceAlerts} />
        </SettingsRow>
        <SettingsRow title="AI Signal Alerts" description="Notify me when a new high-confidence signal fires">
          <Switch checked={signalAlerts} onCheckedChange={setSignalAlerts} />
        </SettingsRow>
        <SettingsRow title="Liquidation Alerts" description="Notify me on large liquidation clusters">
          <Switch checked={liquidationAlerts} onCheckedChange={setLiquidationAlerts} />
        </SettingsRow>
        <SettingsRow title="Daily News Digest" description="Summarized market news every morning">
          <Switch checked={newsDigest} onCheckedChange={setNewsDigest} />
        </SettingsRow>
      </CardContent>
    </Card>
  );
}

export function AppearanceSettings() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const activeTheme = mounted ? theme : "dark";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-foreground">
          <Palette className="size-4 text-accent" />
          Appearance
        </CardTitle>
        <CardDescription>Customize how the terminal looks</CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <SettingsRow title="Theme" description="Switch between dark and light mode">
          <div className="flex gap-2">
            <Button
              variant={activeTheme === "dark" ? "default" : "secondary"}
              size="sm"
              onClick={() => setTheme("dark")}
            >
              Dark
            </Button>
            <Button
              variant={activeTheme === "light" ? "default" : "secondary"}
              size="sm"
              onClick={() => setTheme("light")}
            >
              Light
            </Button>
          </div>
        </SettingsRow>
      </CardContent>
    </Card>
  );
}

export function ApiSettings() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-foreground">
          <KeyRound className="size-4 text-accent" />
          Exchange API
        </CardTitle>
        <CardDescription>
          Connect your Binance account in a future sprint to enable live trading and data
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 pt-0">
        <div className="space-y-1.5">
          <Label htmlFor="api-key">API Key</Label>
          <Input id="api-key" placeholder="Not connected" disabled />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="api-secret">API Secret</Label>
          <Input id="api-secret" type="password" placeholder="Not connected" disabled />
        </div>
        <Separator />
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">Trading logic and live data are disabled in this sprint.</p>
          <Button variant="secondary" disabled>
            Connect Binance
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
