import styles from "./Checkbox.module.css";

interface CheckboxProps {
  checked: boolean;
  className?: string;
  /** Omit when the checkbox is wrapped in a visible `<label>`. */
  label?: string;
  onChange: (checked: boolean) => void;
  size?: "default" | "large";
}

export const Checkbox = ({
  checked,
  className,
  label,
  onChange,
  size = "default",
}: CheckboxProps) => (
  <input
    aria-label={label}
    checked={checked}
    className={`${styles.checkbox} ${styles[size]} ${className ?? ""}`}
    onChange={(e) => onChange(e.target.checked)}
    type="checkbox"
  />
);
