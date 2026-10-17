import type { ListField, SortOption } from "./types";

export const DEVICE_CSV_URL =
  "https://raw.githubusercontent.com/InsectAI-COST-Action/hardware-db/main/data/_InsectAI_hardware-db.csv";

export const EXTERNAL_LINKS = [
  {
    label: "GitHub",
    href: "https://github.com/InsectAI-COST-Action/hardware-db",
  },
  { label: "InsectAI", href: "https://insectai.eu/" },
];

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

export const SUBMIT_LINK =
  "https://docs.google.com/forms/d/1tEs9BkqGV579_Qd8aOVvAhmVWEfLAnKxa04KMH8Pi3Q/viewform";
