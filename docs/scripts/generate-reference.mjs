// Regenerates content/docs/reference/ from the Finance API's live OpenAPI
// schema (fumadocs-openapi) — never hand-edit that directory, it's fully
// derived and gitignored. Runs via predev/prebuild (see package.json).
//
// API_BASE_URL defaults to the docker-compose service hostname; override to
// point at a different instance (e.g. running `npm run dev` outside compose).
import { generateFiles } from "fumadocs-openapi";
import { createOpenAPI } from "fumadocs-openapi/server";

const baseUrl = process.env.API_BASE_URL ?? "http://api:8000";
const schemaUrl = `${baseUrl}/openapi.json`;

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

await waitForSchema();

const openapi = createOpenAPI({ input: [schemaUrl] });

await generateFiles({
  input: openapi,
  output: "./content/docs/reference",
  meta: true,
});

console.log(`[generate-reference] Generated reference docs from ${schemaUrl}`);
