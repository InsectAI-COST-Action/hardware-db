import styles from "./Tabs.module.css";

interface TabsProps<T extends string> {
  label: string;
  onChange: (value: T) => void;
  tabs: { value: T; label: string }[];
  value: T;
}

export const Tabs = <T extends string>({
  label,
  onChange,
  tabs,
  value,
}: TabsProps<T>) => (
  <div aria-label={label} className={styles.container} role="tablist">
    {tabs.map((tab) => (
      <button
        aria-selected={tab.value === value}
        className={`${styles.tab} ${tab.value === value ? styles.selected : ""}`}
        key={tab.value}
        onClick={() => onChange(tab.value)}
        role="tab"
        type="button"
      >
        {tab.label}
      </button>
    ))}
  </div>
);
