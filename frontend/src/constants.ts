import type { ListField, SortOption, Theme, ViewMode } from "./types";

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

export const THEME_OPTIONS: { value: Theme; label: string; icon: string }[] = [
  { value: "light", label: "Light mode", icon: "/images/sun.svg" },
  { value: "dark", label: "Dark mode", icon: "/images/moon.svg" },
];

export const VIEW_MODE_OPTIONS: {
  value: ViewMode;
  label: string;
  icon: string;
}[] = [
  { value: "gallery", label: "Gallery", icon: "/images/grid-2x2.svg" },
  { value: "table", label: "Table", icon: "/images/table.svg" },
];
