import { createOpenAPI } from "fumadocs-openapi/server";

// Same env var and default as scripts/generate-reference.mjs — both must
// resolve to the identical schema URL string, since the generated MDX
// bakes that URL in literally (`document="..."`) and this loader plugin is
// what lets the Source API resolve it back to the bundled schema at
// render time (see lib/source.ts's `plugins`).
export const apiBaseUrl = process.env.API_BASE_URL ?? "http://api:8000";

export const openapi = createOpenAPI({ input: [`${apiBaseUrl}/openapi.json`] });
