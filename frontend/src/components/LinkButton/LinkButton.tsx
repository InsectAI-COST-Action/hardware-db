import type { CSSProperties, ReactNode } from "react";
import styles from "./LinkButton.module.css";

interface LinkButtonProps {
  children: ReactNode;
  className?: string;
  external?: boolean;
  href: string;
  icon?: string;
  variant?: "ghost" | "outline" | "primary";
}

export const LinkButton = ({
  children,
  className,
  external = false,
  href,
  icon,
  variant = "primary",
}: LinkButtonProps) => (
  <a
    className={`${styles.linkButton} ${styles[variant]} ${className ?? ""}`}
    href={href}
    {...(external && { rel: "noopener noreferrer", target: "_blank" })}
  >
    {icon && (
      <span
        aria-hidden="true"
        className={styles.icon}
        style={{ "--icon": `url("${icon}")` } as CSSProperties}
      />
    )}
    {children}
    {external && <span aria-hidden="true" className={styles.externalIcon} />}
  </a>
);
