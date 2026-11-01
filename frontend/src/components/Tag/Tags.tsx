import { Tag } from "@/components/Tag/Tag";
import styles from "./Tags.module.css";

interface TagsProps {
  className?: string;
  tags?: string[];
}

export const Tags = ({ className, tags }: TagsProps) => {
  if (!tags?.length) {
    return null;
  }

  return (
    <div className={`${styles.tags} ${className ?? ""}`}>
      {tags.map((tag) => (
        <Tag key={tag}>{tag}</Tag>
      ))}
    </div>
  );
};
