const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

export const formatNumber = (value: number) => number.format(value);

export function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${bytes} B`;
}
