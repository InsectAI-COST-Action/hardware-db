import type { Dispatch, SetStateAction } from "react";
import { useOutletContext } from "react-router";
import type { ViewMode } from "../lib/types";
import type { useDeviceFilters } from "./useDeviceFilters";
import type { useDevices } from "./useDevices";

/**
 * State shared by all routes. It lives in the App layout so devices are only
 * fetched once, and filters, sort and view mode survive navigating away.
 */
export type AppContext = ReturnType<typeof useDevices> &
  ReturnType<typeof useDeviceFilters> & {
    setViewMode: Dispatch<SetStateAction<ViewMode>>;
    viewMode: ViewMode;
  };

export const useAppContext = () => useOutletContext<AppContext>();
