import { loader } from "fumadocs-core/source";
import { defineDocs } from "fumadocs-mdx/macro";
import { openapiPlugin } from "fumadocs-openapi/server";

const docs = defineDocs({ dir: "content/docs" });

export const source = loader({
  baseUrl: "/docs",
  source: docs.toFumadocsSource(),
  // Cosmetic only (adds a method badge to reference pages in the sidebar) —
  // the actual schema resolution happens per-page in page.tsx via
  // openapi.preloadOpenAPIPage(), not here.
  plugins: [openapiPlugin()],
});
