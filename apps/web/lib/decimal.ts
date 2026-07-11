export type DecimalValue = string | number;

export function decimalToInput(value: DecimalValue | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "";
  }
  return trimDecimal(String(value));
}

export function decimalToNumber(value: DecimalValue | null | undefined): number {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function formatDecimal(value: DecimalValue | null | undefined): string {
  return trimDecimal(decimalToNumber(value).toFixed(2));
}

export function sumDecimalValues(values: Array<DecimalValue | null | undefined>): string {
  const totalHundredths = values.reduce<number>((sum, value) => sum + Math.round(decimalToNumber(value) * 100), 0);
  return formatDecimal(totalHundredths / 100);
}

function trimDecimal(value: string): string {
  if (!value.includes(".")) {
    return value;
  }
  return value.replace(/(\.\d*?[1-9])0+$/, "$1").replace(/\.0+$/, "");
}
