import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const isGitHubPages = mode === "github-pages";
  const repositoryRoot = fileURLToPath(new URL("..", import.meta.url));
  const googleFormId = isGitHubPages
    ? ""
    : loadEnv(mode, repositoryRoot, "GOOGLE_FORM_ID").GOOGLE_FORM_ID;

  if (!isGitHubPages && !googleFormId) {
    throw new Error(
      "GOOGLE_FORM_ID is missing from the repository root .env file.",
    );
  }

  return {
    base: isGitHubPages ? "/hardware-db/" : "/",
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
