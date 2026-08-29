// Regenerates content/docs/reference/ from the Finance API's OpenAPI schema
// (fumadocs-openapi) — never hand-edit that directory, it's fully derived
// and gitignored. Runs via predev/prebuild (see package.json).
//
// Two modes, matching lib/openapi.ts's resolution logic exactly (both must
// agree on the same `input` string):
// - OPENAPI_SCHEMA_PATH set (CI / "Deploy Docs" workflow): read a local
//   file, no live API needed — see .github/workflows/deploy-docs.yml.
// - Unset (local dev / docker-compose, the default): fetch from a live API
//   at {API_BASE_URL}/openapi.json, default http://api:8000 (the
//   docker-compose service hostname), with retries since the API container
//   may not be ready yet when this runs.
import { generateFiles } from "fumadocs-openapi";
import { createOpenAPI } from "fumadocs-openapi/server";

const schemaPath = process.env.OPENAPI_SCHEMA_PATH;
const baseUrl = process.env.API_BASE_URL ?? "http://api:8000";
const schemaUrl = `${baseUrl}/openapi.json`;
const schemaInput = schemaPath ?? schemaUrl;

const RETRY_ATTEMPTS = 10;
const RETRY_DELAY_MS = 2000;

async function waitForSchema() {
  for (let attempt = 1; attempt <= RETRY_ATTEMPTS; attempt++) {
    try {
      const response = await fetch(schemaUrl);
      if (response.ok) return;
      throw new Error(`HTTP ${response.status}`);
    } catch (error) {
      if (attempt === RETRY_ATTEMPTS) {
        throw new Error(
          `Finance API not reachable at ${schemaUrl} after ${RETRY_ATTEMPTS} attempts: ${error}`,
        );
      }
      console.log(
        `[generate-reference] ${schemaUrl} not ready yet (attempt ${attempt}/${RETRY_ATTEMPTS}), retrying...`,
      );
      await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
    }
  }
}

if (!schemaPath) await waitForSchema();

const openapi = createOpenAPI({ input: [schemaInput] });

await generateFiles({
  input: openapi,
  output: "./content/docs/reference",
  meta: true,
});

console.log(`[generate-reference] Generated reference docs from ${schemaInput}`);
