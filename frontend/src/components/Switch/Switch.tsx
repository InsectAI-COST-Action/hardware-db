import type { LucideIcon } from "lucide-react";
import { useId } from "react";
import styles from "./Switch.module.css";

interface SwitchProps<T extends string> {
  label: string;
  onChange: (value: T) => void;
  options: {
    icon?: LucideIcon;
    label: string;
    value: T;
  }[];
  showLabels?: boolean;
  value: T;
}

export const Switch = <T extends string>({
  label,
  onChange,
  options,
  showLabels,
  value,
}: SwitchProps<T>) => {
  const name = useId();

  return (
    <div aria-label={label} className={styles.container} role="radiogroup">
      {options.map((option) => (
        <label
          className={`${styles.option} ${option.value === value ? styles.selected : ""}`}
          key={option.value}
        >
          <input
            aria-label={showLabels ? undefined : option.label}
            checked={option.value === value}
            className={styles.input}
            name={name}
            onChange={() => onChange(option.value)}
            type="radio"
            value={option.value}
          />
          {option.icon && (
            <option.icon aria-hidden="true" className={styles.icon} size={16} />
          )}
          {showLabels && <span>{option.label}</span>}
        </label>
      ))}
    </div>
  );
};
