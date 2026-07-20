import { useEffect, useState } from "react";

import { formatUtcClock } from "@/lib/utils";

export function useUtcClock(): string | null {
  const [time, setTime] = useState<string | null>(null);

  useEffect(() => {
    setTime(formatUtcClock(new Date()));
    const interval = setInterval(() => {
      setTime(formatUtcClock(new Date()));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return time;
}
