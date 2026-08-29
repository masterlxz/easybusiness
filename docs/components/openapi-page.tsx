"use client";

import { createOpenAPIPage } from "fumadocs-openapi/ui";

// createOpenAPIPage() must be invoked from a client boundary — module code
// reachable from a Server Component (mdx.tsx, imported by the docs
// page.tsx) can't call it directly. This file's sole job is to isolate that
// call inside an unambiguous "use client" module; mdx.tsx just imports the
// resulting component reference, which is safe to pass across the boundary.
export const OpenAPIPage = createOpenAPIPage();
