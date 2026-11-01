import { LinkButton } from "@/components/Button/LinkButton";
import { Switch } from "@/components/Switch/Switch";
import { useTheme } from "@/hooks/useTheme";
import { EXTERNAL_LINKS, THEME_OPTIONS } from "@/lib/constants";
import { Link } from "react-router";
import styles from "./TopBar.module.css";

export const TopBar = () => {
  const { theme, setTheme } = useTheme();

  return (
    <div className={styles.container}>
      <Link className={styles.homeLink} to="/">
        <img alt="" className={styles.logo} src="/images/logo.svg" />
        <span>InsectAI Hardware Database</span>
      </Link>
      <nav className={styles.externalLinks}>
        {EXTERNAL_LINKS.map(({ label, href }) => (
          <LinkButton external href={href} key={label} variant="ghost">
            {label}
          </LinkButton>
        ))}
      </nav>
      <Switch
        label="Theme"
        onChange={setTheme}
        options={THEME_OPTIONS}
        value={theme}
      />
    </div>
  );
};
