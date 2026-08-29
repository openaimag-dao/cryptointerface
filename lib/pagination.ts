export function parsePageParam(pageParam: string | undefined): number {
  const parsed = Number(pageParam);
  return Number.isFinite(parsed) && parsed >= 1 ? Math.floor(parsed) : 1;
}
