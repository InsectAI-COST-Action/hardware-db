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

export interface SpecGroup {
  title: string;
  specs: Spec[];
}

export interface TeamMember {
  name: string;
  role: string;
}

export type Theme = "light" | "dark";

export type ViewMode = "gallery" | "table" | "compare";
