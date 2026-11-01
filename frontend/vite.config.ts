import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const repositoryRoot = fileURLToPath(new URL("..", import.meta.url));
  const { GOOGLE_FORM_ID: googleFormId } = loadEnv(
    mode,
    repositoryRoot,
    "GOOGLE_FORM_ID",
  );

  if (!googleFormId) {
    throw new Error(
      "GOOGLE_FORM_ID is missing from the repository root .env file.",
    );
  }

  return {
    plugins: [react()],
    define: {
      "import.meta.env.VITE_GOOGLE_FORM_ID": JSON.stringify(googleFormId),
    },
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
  };
});
