import { createOpenAPI } from "fumadocs-openapi/server";

// Same resolution logic as scripts/generate-reference.mjs — both must
// resolve to the identical `input` string, since the generated MDX bakes
// it in literally (`document="..."`) and openapi.preloadOpenAPIPage()
// (called per-page in app/docs/[[...slug]]/page.tsx) has to look that
// exact key up again at render time.
//
// OPENAPI_SCHEMA_PATH (a local file) is used by the "Deploy Docs" GitHub
// Actions workflow, which generates a schema snapshot without a live API
// running (see .github/workflows/deploy-docs.yml). Local dev/docker-compose
// leave it unset and fetch from the live API instead.
export const schemaInput =
  process.env.OPENAPI_SCHEMA_PATH ??
  `${process.env.API_BASE_URL ?? "http://api:8000"}/openapi.json`;

export const openapi = createOpenAPI({ input: [schemaInput] });
