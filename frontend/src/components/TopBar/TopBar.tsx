import { EXTERNAL_LINKS } from "../../constants";
import styles from "./TopBar.module.css";

export const TopBar = () => (
  <div className={styles.container}>
    <a className={styles.homeLink} href="/">
      <img alt="" className={styles.logo} src="/images/logo.svg" />
      <span>InsectAI Hardware Database</span>
    </a>
    <nav className={styles.externalLinks}>
      {EXTERNAL_LINKS.map(({ label, href }) => (
        <a
          className={styles.externalLink}
          href={href}
          key={label}
          rel="noopener noreferrer"
          target="_blank"
        >
          {label}
          <span aria-hidden="true" className={styles.externalIcon} />
        </a>
      ))}
    </nav>
  </div>
);
