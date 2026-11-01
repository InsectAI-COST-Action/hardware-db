import { SpecList } from "@/components/SpecList/SpecList";
import type { SpecGroup } from "@/lib/types";
import styles from "./SpecGroups.module.css";

interface SpecGroupsProps {
  groups: SpecGroup[];
}

export const SpecGroups = ({ groups }: SpecGroupsProps) => {
  if (!groups.length) {
    return null;
  }

  return (
    <div className={styles.grid}>
      {groups.map(({ title, icon: Icon, specs }) => (
        <section className={styles.card} key={title}>
          <h3 className={styles.title}>
            <Icon aria-hidden="true" className={styles.icon} size={24} />
            {title}
          </h3>
          <SpecList specs={specs} variant="table" />
        </section>
      ))}
    </div>
  );
};
