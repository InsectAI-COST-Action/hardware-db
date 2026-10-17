import type { CSSProperties } from "react";
import styles from "./Select.module.css";

interface SelectProps<T extends string> {
  icon?: string;
  label: string;
  onChange: (value: T) => void;
  options: { value: T; label: string }[];
  value: T;
}

export const Select = <T extends string>({
  icon,
  label,
  onChange,
  options,
  value,
}: SelectProps<T>) => (
  <div className={styles.container}>
    {icon && (
      <span
        aria-hidden="true"
        className={`${styles.icon} ${styles.leadingIcon}`}
        style={{ "--icon": `url("${icon}")` } as CSSProperties}
      />
    )}
    <select
      aria-label={label}
      className={`${styles.select} ${icon ? styles.withIcon : ""}`}
      onChange={(e) => onChange(e.target.value as T)}
      value={value}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
    <span
      aria-hidden="true"
      className={`${styles.icon} ${styles.chevron}`}
      style={{ "--icon": 'url("/images/chevron-down.svg")' } as CSSProperties}
    />
  </div>
);
