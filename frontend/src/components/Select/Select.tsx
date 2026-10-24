import { ChevronDown, type LucideIcon } from "lucide-react";
import styles from "./Select.module.css";

interface SelectProps<T extends string> {
  icon?: LucideIcon;
  label: string;
  onChange: (value: T) => void;
  options: { value: T; label: string }[];
  value: T;
}

export const Select = <T extends string>({
  icon: Icon,
  label,
  onChange,
  options,
  value,
}: SelectProps<T>) => (
  <div className={styles.container}>
    {Icon && (
      <Icon
        aria-hidden="true"
        className={`${styles.icon} ${styles.leadingIcon}`}
        size={16}
      />
    )}
    <select
      aria-label={label}
      className={`${styles.select} ${Icon ? styles.withIcon : ""}`}
      onChange={(e) => onChange(e.target.value as T)}
      value={value}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
    <ChevronDown
      aria-hidden="true"
      className={`${styles.icon} ${styles.chevron}`}
      size={16}
    />
  </div>
);
