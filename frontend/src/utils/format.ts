import dayjs from "dayjs";

export function formatDate(value?: string | null) {
  if (!value) {
    return "-";
  }
  return dayjs(value).format("YYYY-MM-DD HH:mm");
}

export function formatMoney(value?: number | null) {
  if (value == null) {
    return "-";
  }
  return `${value.toLocaleString()} Rials`;
}

export function toTitleCase(value: string) {
  return value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
