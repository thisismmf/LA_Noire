import clsx from "clsx";
import type { HTMLAttributes } from "react";

export function Skeleton({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx("ui-skeleton", className)} {...rest} />;
}
