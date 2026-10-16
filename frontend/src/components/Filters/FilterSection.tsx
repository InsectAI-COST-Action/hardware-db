import type { FilterOption } from "../../types";
import styles from "./Filters.module.css";

interface FilterSectionProps {
  onChange: (selected: string[]) => void;
  options: FilterOption[];
  selected: string[];
  title: string;
}

export const FilterSection = ({
  onChange,
  options,
  selected,
  title,
}: FilterSectionProps) => {
  const toggle = (value: string) => {
    onChange(
      selected.includes(value)
        ? selected.filter((item) => item !== value)
        : [...selected, value],
    );
  };

  return (
    <div className={styles.section}>
      <span className={styles.sectionTitle}>{title}</span>
      {options.map(({ value, count }) => (
        <label className={styles.option} key={value}>
          <input
            checked={selected.includes(value)}
            onChange={() => toggle(value)}
            type="checkbox"
          />
          <span className={styles.optionLabel}>{value}</span>
          <span className={styles.optionCount}>{count}</span>
        </label>
      ))}
    </div>
  );
};
