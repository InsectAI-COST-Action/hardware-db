import { useCallback, useMemo, useState } from "react";
import { FILTER_DEFINITIONS } from "../lib/constants";
import type {
  Device,
  FilterOption,
  FilterSelections,
  ListField,
  SortOption,
} from "../lib/types";

export const useDeviceFilters = (devices: Device[]) => {
  const [search, setSearch] = useState("");
  const [selections, setSelections] = useState<FilterSelections>({});
  const [sort, setSort] = useState<SortOption>("random");

  const searchedDevices = useMemo(
    () => devices.filter((device) => matchesSearch(device, search)),
    [devices, search],
  );

  const filteredDevices = useMemo(
    () =>
      sortDevices(
        searchedDevices.filter((device) =>
          matchesSelections(device, selections),
        ),
        sort,
      ),
    [searchedDevices, selections, sort],
  );

  const sections = useMemo(
    () =>
      FILTER_DEFINITIONS.map(({ field, title }) => {
        const facetDevices = searchedDevices.filter((device) =>
          matchesSelections(device, selections, field),
        );

        return {
          field,
          title,
          options: getFilterOptions(devices, facetDevices, field),
          selected: selections[field] ?? [],
        };
      }),
    [devices, searchedDevices, selections],
  );

  const setSelected = useCallback((field: ListField, selected: string[]) => {
    setSelections((prev) => ({ ...prev, [field]: selected }));
  }, []);

  return {
    filteredDevices,
    search,
    sections,
    setSearch,
    setSelected,
    setSort,
    sort,
  };
};

const countValues = (devices: Device[], field: ListField) => {
  const counts = new Map<string, number>();

  devices.forEach((device) => {
    device[field]?.forEach((value) => {
      counts.set(value, (counts.get(value) ?? 0) + 1);
    });
  });

  return counts;
};

/**
 * Options are taken from all devices so the list stays stable, while counts
 * reflect `facetDevices` (the devices matching everything but this field).
 */
const getFilterOptions = (
  allDevices: Device[],
  facetDevices: Device[],
  field: ListField,
): FilterOption[] => {
  const totals = countValues(allDevices, field);
  const facetCounts = countValues(facetDevices, field);

  return [...totals.entries()]
    .sort(([a, aTotal], [b, bTotal]) => bTotal - aTotal || a.localeCompare(b))
    .map(([value]) => ({ value, count: facetCounts.get(value) ?? 0 }));
};

const matchesSearch = (device: Device, query: string) => {
  const normalizedQuery = query.trim().toLowerCase();

  if (!normalizedQuery) {
    return true;
  }

  return [device.deviceName].some((field) =>
    field?.toLowerCase().includes(normalizedQuery),
  );
};

/**
 * A device matches when, for every field with a selection, it has at least
 * one of the selected values (OR within a field, AND across fields).
 */
const matchesSelections = (
  device: Device,
  selections: FilterSelections,
  ignoreField?: ListField,
) =>
  Object.entries(selections).every(([field, selected]) => {
    if (field === ignoreField || !selected?.length) {
      return true;
    }

    const values = device[field as ListField] ?? [];

    return selected.some((value) => values.includes(value));
  });

/**
 * Devices arrive already shuffled, so "random" keeps the incoming order.
 */
const sortDevices = (devices: Device[], sort: SortOption) => {
  if (sort === "name") {
    return [...devices].sort((a, b) =>
      (a.deviceName ?? "").localeCompare(b.deviceName ?? ""),
    );
  }

  return devices;
};
