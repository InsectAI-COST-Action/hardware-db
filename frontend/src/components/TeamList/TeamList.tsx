import styles from "./TeamList.module.css";

interface TeamListProps {
  members: {
    name: string;
    role: string;
  }[];
}

export const TeamList = ({ members }: TeamListProps) => {
  if (!members.length) {
    return null;
  }

  return (
    <ul className={styles.list}>
      {members.map(({ name, role }) => (
        <li className={styles.member} key={name}>
          <span aria-hidden="true" className={styles.avatar}>
            {getInitials(name)}
          </span>
          <div>
            <p className={styles.name}>{name}</p>
            {role ? <p className={styles.role}>{role}</p> : null}
          </div>
        </li>
      ))}
    </ul>
  );
};

const getInitials = (name: string) => {
  const words = name.split(/\s+/).filter(Boolean);
  const first = words[0]?.[0] ?? "";
  const last = words.length > 1 ? words[words.length - 1][0] : "";

  return `${first}${last}`.toUpperCase();
};
