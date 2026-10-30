import { LinkButton } from "@/components/Button/LinkButton";
import { SUBMIT_LINK } from "@/lib/constants";
import styles from "./Intro.module.css";

export const Intro = () => (
  <div className={styles.container}>
    <div className={styles.text}>
      <h1>Hardware for automated insect monitoring</h1>
      <p>
        This is the InsectAI hardware database, designed to collate information
        on devices used for automated monitoring of insects. Here you can submit
        details about systems and explore the data we have collected to choose a
        system for your needs.
      </p>
    </div>
    <div className={`dark ${styles.card}`}>
      <div>
        <h3>Built or deployed a device?</h3>
        <p>
          Add it to the database through our submission form. Entries are
          published openly so others can learn from your design.
        </p>
      </div>
      <LinkButton external href={SUBMIT_LINK}>
        Open submission form
      </LinkButton>
    </div>
  </div>
);
