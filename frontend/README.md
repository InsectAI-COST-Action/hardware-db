# InsectAI Hardware Database - Frontend

A website for browsing, filtering and comparing the automated insect monitoring devices in the [InsectAI hardware database](../README.md).

## Run it locally

You need [Node.js](https://nodejs.org/) (version 20.19 or newer). Then, from this `frontend` folder:

```sh
npm install   # first time only
npm run dev
```

Open the address it prints (usually http://localhost:5173). The page reloads automatically when you save a file.

> [!NOTE]
> The app loads device data from the CSV file on GitHub's `main` branch, not from your local `data/` folder. Changes to the local CSV only show up after they're merged into `main`. To test with other data, change `DEVICE_CSV_URL` in `src/lib/constants.ts`.

## Where things are

| To change…                                        | Look in                                           |
| ------------------------------------------------- | ------------------------------------------------- |
| Which specs are shown, their labels and units     | `SPEC_GROUP_COLUMNS` in `src/lib/constants.ts`    |
| Ecology & deployment fields                       | `ECOLOGY_GROUP_COLUMNS` in `src/lib/constants.ts` |
| Filters in the sidebar                            | `FILTER_DEFINITIONS` in `src/lib/constants.ts`    |
| Data source, external links, submit form link     | `src/lib/constants.ts`                            |
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

## Built with

[React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/) and [Vite](https://vite.dev/). Icons come from [Lucide](https://lucide.dev/icons/).
