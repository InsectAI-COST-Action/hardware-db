import { DeviceDetails } from "@/pages/DeviceDetails/DeviceDetails.tsx";
import { Devices } from "@/pages/Devices/Devices.tsx";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter } from "react-router";
import { RouterProvider } from "react-router/dom";
import App from "./App.tsx";
import "./index.css";

const router = createBrowserRouter([
  {
    path: "/",
    Component: App,
    children: [
      { index: true, Component: Devices },
      { path: "devices/:slug", Component: DeviceDetails },
    ],
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);
