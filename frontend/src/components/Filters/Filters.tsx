import type { FilterOption, ListField } from "../../lib/types";
import { FilterSection } from "./FilterSection";
import styles from "./Filters.module.css";

interface FiltersProps {
  onChange: (field: ListField, selected: string[]) => void;
  sections: {
    field: ListField;
    options: FilterOption[];
    selected: string[];
    title: string;
  }[];
}

export const Filters = ({ sections, onChange }: FiltersProps) => (
  <aside className={styles.container}>
    <h4 className={styles.title}>Filters</h4>
    {sections.map(({ field, title, options, selected }) => (
      <FilterSection
        key={field}
        onChange={(values) => onChange(field, values)}
        options={options}
        selected={selected}
        title={title}
      />
    ))}
  </aside>
);
