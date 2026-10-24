import { ExternalLink, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import styles from "./LinkButton.module.css";

interface LinkButtonProps {
  children: ReactNode;
  className?: string;
  external?: boolean;
  href: string;
  icon?: LucideIcon;
  variant?: "ghost" | "outline" | "primary";
}

export const LinkButton = ({
  children,
  className,
  external = false,
  href,
  icon: Icon,
  variant = "primary",
}: LinkButtonProps) => (
  <a
    className={`${styles.linkButton} ${styles[variant]} ${className ?? ""}`}
    href={href}
    {...(external && { rel: "noopener noreferrer", target: "_blank" })}
  >
    {Icon && <Icon aria-hidden="true" className={styles.icon} size={16} />}
    {children}
    {external && (
      <ExternalLink aria-hidden="true" className={styles.icon} size={16} />
    )}
  </a>
);
