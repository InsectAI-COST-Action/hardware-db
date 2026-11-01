import { X } from "lucide-react";
import { type ReactNode, useEffect, useRef } from "react";
import styles from "./Sheet.module.css";

interface SheetProps {
  children: ReactNode;
  onClose: () => void;
  open: boolean;
  title: string;
}

/**
 * A modal panel sliding in from the right. Built on `<dialog>`, which handles
 * focus trapping, Escape and restoring focus on close.
 */
export const Sheet = ({ children, onClose, open, title }: SheetProps) => {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;

    if (open && !dialog?.open) {
      dialog?.showModal();
    } else if (!open && dialog?.open) {
      dialog.close();
    }
  }, [open]);

  return (
    <dialog
      aria-label={title}
      className={styles.sheet}
      onClick={(event) => {
        // Clicks on the backdrop land on the dialog itself
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
      onClose={onClose}
      ref={ref}
    >
      <div className={styles.header}>
        <h2 className={styles.title}>{title}</h2>
        <button
          aria-label="Close"
          className={styles.closeButton}
          onClick={onClose}
          type="button"
        >
          <X aria-hidden="true" size={20} />
        </button>
      </div>
      <div className={styles.body}>{children}</div>
    </dialog>
  );
};
