import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import styles from "./Button.module.css";

interface ButtonProps {
  children: ReactNode;
  className?: string;
  disabled?: boolean;
  icon?: LucideIcon;
  onClick: () => void;
  variant?: "ghost" | "outline" | "primary";
}

/** A `<button>` styled like `LinkButton`. */
export const Button = ({
  children,
  className,
  disabled,
  icon: Icon,
  onClick,
  variant = "primary",
}: ButtonProps) => (
  <button
    className={`${styles.button} ${styles[variant]} ${className ?? ""}`}
    disabled={disabled}
    onClick={onClick}
    type="button"
  >
    {Icon && <Icon aria-hidden="true" className={styles.icon} size={16} />}
    {children}
  </button>
);
