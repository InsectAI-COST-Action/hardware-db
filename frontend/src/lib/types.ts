export interface Device {
  deviceName: string;
  deviceDescription: string;
  contactName: string;
  contactInstitution: string;
  documentationUrl: string;
  deviceConstruction: string[];
  powerSources: string[];
  processingUnit: string;
  modelProcessing: string[];
  captureModes: string[];
  taxonomicGroups: string[];
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

export type Theme = "light" | "dark";

export type ViewMode = "gallery" | "table" | "compare";
