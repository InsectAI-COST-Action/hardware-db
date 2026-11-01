import { LinkButton } from "@/components/Button/LinkButton";
import { PUBLIC_ENV_URL } from "@/lib/constants";
import { useEffect, useState } from "react";
import styles from "./Intro.module.css";

export const Intro = () => {
  const localFormId = import.meta.env.VITE_GOOGLE_FORM_ID;
  const [submitLink, setSubmitLink] = useState(
    localFormId ? buildSubmitLink(localFormId) : "",
  );
  const [submitLinkUnavailable, setSubmitLinkUnavailable] = useState(false);

  useEffect(() => {
    if (localFormId) {
      return;
    }

    const controller = new AbortController();

    fetch(PUBLIC_ENV_URL, { cache: "no-store", signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Could not load the public environment file.");
        }

        return response.text();
      })
      .then((contents) => {
        const formId = contents
          .split(/\r?\n/)
          .map((line) => line.trim())
          .find((line) => line.startsWith("GOOGLE_FORM_ID="))
          ?.slice("GOOGLE_FORM_ID=".length)
          .trim();

        if (!formId) {
          throw new Error("GOOGLE_FORM_ID is missing from the environment file.");
        }

        setSubmitLink(buildSubmitLink(formId));
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setSubmitLinkUnavailable(true);
        }
      });

    return () => controller.abort();
  }, [localFormId]);

  return (
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
        {submitLink ? (
          <LinkButton external href={submitLink}>
            Open submission form
          </LinkButton>
        ) : (
          <p role="status">
            {submitLinkUnavailable
              ? "Submission form unavailable"
              : "Loading submission form..."}
          </p>
        )}
      </div>
      <p className={styles.credit}>
        <span className={styles.creditLight}>Photo by Luca Pegoraro</span>
        <span className={styles.creditDark}>Photo by Jirislav Skuhrovec</span>
      </p>
    </div>
  );
};

const buildSubmitLink = (formId: string) =>
  `https://docs.google.com/forms/d/${formId}/viewform`;
