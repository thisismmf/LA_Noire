import clsx from "clsx";
import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type ButtonProps = PropsWithChildren<
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: "primary" | "secondary" | "danger" | "ghost";
  }
>;

export function Button({ children, className, variant = "primary", ...rest }: ButtonProps) {
  return (
    <button className={clsx("ui-button", `ui-button-${variant}`, className)} {...rest}>
      {children}
    </button>
  );
}
