import clsx from "clsx";
import type { HTMLAttributes, PropsWithChildren } from "react";

type CardProps = PropsWithChildren<HTMLAttributes<HTMLDivElement>>;

export function Card({ children, className, ...rest }: CardProps) {
  return (
    <article className={clsx("ui-card", className)} {...rest}>
      {children}
    </article>
  );
}
