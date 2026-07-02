function parseNum(amount: string | number): number {
  return typeof amount === "string" ? parseFloat(amount) : amount;
}

function intlFormat(num: number, opts: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat("es-ES", opts).format(num);
}

export function formatCurrency(amount: string | number, currency = "EUR"): string {
  return intlFormat(parseNum(amount), {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function formatPercent(ratio: number): string {
  return intlFormat(ratio, {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

export function formatNumber(amount: string | number): string {
  return intlFormat(parseNum(amount), {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
