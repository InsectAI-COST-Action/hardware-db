import styles from "./Input.module.css";

interface InputProps {
  className?: string;
  label: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: "text" | "search";
  value: string;
}

export const Input = ({
  className,
  label,
  onChange,
  placeholder,
  type = "text",
  value,
}: InputProps) => (
  <input
    aria-label={label}
    className={`${styles.input} ${className ?? ""}`}
    onChange={(e) => onChange(e.target.value)}
    placeholder={placeholder}
    type={type}
    value={value}
  />
);
