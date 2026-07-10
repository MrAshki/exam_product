import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function displayName(fullName?: string | null, email?: string | null): string {
  return fullName?.trim() || email?.trim() || "کاربر";
}
