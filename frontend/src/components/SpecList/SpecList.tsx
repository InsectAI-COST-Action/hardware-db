import styles from "./SpecList.module.css";

interface SpecListProps {
  specs: { label: string; value?: string }[];
  variant?: "compact" | "table";
}

export const SpecList = ({ specs, variant = "compact" }: SpecListProps) => {
  if (!specs.length) {
    return null;
  }

  return (
    <dl className={`${styles.specs} ${styles[variant]}`}>
      {specs.map(({ label, value }) => (
        <div className={styles.spec} key={label}>
          <dt className={styles.specLabel}>{label}</dt>
          <dd className={styles.specValue}>{value}</dd>
        </div>
      ))}
    </dl>
  );
};
