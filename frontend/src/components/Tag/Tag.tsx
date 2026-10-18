import type { ReactNode } from "react";
import styles from "./Tags.module.css";

interface TagProps {
  children: ReactNode;
  onClick?: () => void;
}

export const Tag = ({ children, onClick }: TagProps) => {
  if (onClick) {
    return (
      <button
        className={`${styles.tag} ${styles.clickable}`}
        onClick={onClick}
        type="button"
      >
        {children}
      </button>
    );
  }

  return <span className={styles.tag}>{children}</span>;
};
