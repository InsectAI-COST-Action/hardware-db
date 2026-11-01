# InsectAI Hardware Database - Frontend

A website for browsing, filtering and comparing the automated insect monitoring devices in the [InsectAI hardware database](../README.md).

This frontend replaces the legacy static landing page formerly served from `docs/`. Its initial GitHub Pages prototype was introduced in [commit 8fecfca](https://github.com/InsectAI-COST-Action/hardware-db/commit/8fecfca69586634ddf66bb3726fb19e4f882484e).

## Run it locally

You need [Node.js](https://nodejs.org/) (version 20.19 or newer). Then, from this `frontend` folder:

```sh
npm install   # first time only
npm run dev
```

Open the address it prints (usually http://localhost:5173). The page reloads automatically when you save a file.

The local dev server and the regular `npm run build` read `GOOGLE_FORM_ID` from the repository-root `.env` file. Restart the dev server or rebuild after changing that value.

> [!NOTE]
> The app loads device data from the CSV file on GitHub's `main` branch, not from your local `data/` folder. Changes to the local CSV only show up after they're merged into `main`. To test with other data, change `DEVICE_CSV_URL` in `src/lib/constants.ts`.

## Where things are

| To change…                                        | Look in                                           |
| ------------------------------------------------- | ------------------------------------------------- |
| Which specs are shown, their labels and units     | `SPEC_GROUP_COLUMNS` in `src/lib/constants.ts`    |
| Ecology & deployment fields                       | `ECOLOGY_GROUP_COLUMNS` in `src/lib/constants.ts` |
| Filters in the sidebar                            | `FILTER_DEFINITIONS` in `src/lib/constants.ts`    |
| Device CSV and external links                     | `src/lib/constants.ts`                            |
| Submit form link                                  | Root `.env` (`GOOGLE_FORM_ID`); loaded in `src/components/Intro/Intro.tsx` |
| How CSV rows are turned into devices              | `src/hooks/useDevices.ts`                         |
| Pages (device list, device details)               | `src/pages/`                                      |
| Reusable building blocks (cards, table, buttons…) | `src/components/`                                 |
| Colours, fonts and light/dark theme               | `src/index.css`                                   |

Each component keeps its styles next to it in a `.module.css` file.

## Before you share a change

```sh
npm run lint    # checks for common mistakes
npm run build   # checks types and builds the site into dist/
```

Both should finish without errors.

## GitHub Pages

The site is deployed from the `main` branch by `.github/workflows/deploy-frontend.yml`. In repository settings, Pages must use **GitHub Actions** as its source. Pull requests build the frontend for validation but do not deploy it.

The deployment workflow runs `npm run build:pages`, which sets Vite's base path to `/hardware-db/`. The public site fetches the CSV and the repository's public `.env` from `main` when a visitor loads the page.

To build locally for GitHub Pages, run `npm run build:pages` from this folder. For ordinary local development and builds, use `npm run dev` and `npm run build`; these use the local repository-root `.env` value instead.

## Built with

[React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/) and [Vite](https://vite.dev/). Icons come from [Lucide](https://lucide.dev/icons/).
