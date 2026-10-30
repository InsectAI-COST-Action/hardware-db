import type { LucideIcon } from "lucide-react";

export interface Device {
  deviceName: string;
  deviceDescription: string;
  contactName: string;
  /** A `mailto:` link or a web URL, or empty if neither. */
  contactUrl: string;
  contactInstitution: string;
  documentationUrl: string;
  deviceConstruction: string[];
  powerSources: string[];
  processingUnits: string[];
  modelProcessing: string[];
  captureModes: string[];
  taxonomicGroups: string[];
  team: TeamMember[];
  specifications: SpecGroup[];
  ecology: SpecGroup[];
  slug: string;
  raw: Record<string, string>;
}

export interface FilterOption {
  value: string;
  count: number;
}

export type FilterSelections = Partial<Record<ListField, string[]>>;

export type ListField = {
  [K in keyof Device]-?: Device[K] extends string[] ? K : never;
}[keyof Device];

export type SortOption = "random" | "name";

export interface Spec {
  label: string;
  value: string;
}

/**
 * How each specification is read from its column: as free text, as a `;`
 * separated list, or as a 1-5 score.
 */
export type SpecFormat = "text" | "list" | "score";

export type SpecGroupColumns = {
  title: string;
  icon: LucideIcon;
  specs: { label: string; column: string; format?: SpecFormat }[];
}[];

export interface SpecGroup {
  title: string;
  icon: LucideIcon;
  specs: Spec[];
}

export interface TeamMember {
  name: string;
  role: string;
}

export type Theme = "light" | "dark";

export type ViewMode = "gallery" | "table";
