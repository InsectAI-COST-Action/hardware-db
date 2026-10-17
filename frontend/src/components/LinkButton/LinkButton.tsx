import type { ReactNode } from "react";
import styles from "./LinkButton.module.css";

interface LinkButtonProps {
  children: ReactNode;
  className?: string;
  external?: boolean;
  href: string;
  variant?: "ghost" | "outline" | "primary";
}

export const LinkButton = ({
  children,
  className,
  external = false,
  href,
  variant = "primary",
}: LinkButtonProps) => (
  <a
    className={`${styles.linkButton} ${styles[variant]} ${className ?? ""}`}
    href={href}
    {...(external && { rel: "noopener noreferrer", target: "_blank" })}
  >
    {children}
    {external && <span aria-hidden="true" className={styles.externalIcon} />}
  </a>
);
