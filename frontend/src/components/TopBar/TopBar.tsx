import { LinkButton } from "@/components/LinkButton/LinkButton";
import { Switch } from "@/components/Switch/Switch";
import { useTheme } from "@/hooks/useTheme";
import { EXTERNAL_LINKS, THEME_OPTIONS } from "@/lib/constants";
import styles from "./TopBar.module.css";

export const TopBar = () => {
  const { theme, setTheme } = useTheme();

  return (
    <div className={styles.container}>
      <a className={styles.homeLink} href="/">
        <img alt="" className={styles.logo} src="/images/logo.svg" />
        <span>InsectAI Hardware Database</span>
      </a>
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
