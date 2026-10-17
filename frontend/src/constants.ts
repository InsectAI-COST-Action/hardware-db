import type { ListField, SortOption } from "./types";

export const DEVICE_CSV_URL =
  "https://raw.githubusercontent.com/InsectAI-COST-Action/hardware-db/main/data/_InsectAI_hardware-db.csv";

export const FILTER_DEFINITIONS: {
  field: ListField;
  title: string;
}[] = [
  { field: "deviceConstruction", title: "Construction" },
  { field: "taxonomicGroups", title: "Target taxa" },
  { field: "captureModes", title: "Capture mode" },
  { field: "powerSources", title: "Power source" },
  { field: "modelProcessing", title: "Image processing" },
];

export const SORT_OPTIONS: {
  value: SortOption;
  label: string;
}[] = [
  { value: "random", label: "Random" },
  { value: "name", label: "Name (A-Z)" },
];
