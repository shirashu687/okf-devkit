#!/usr/bin/env node
// Stable entrypoint for existing npm installations, hooks and direct invocations.
// Implementation belongs in src/node/; keep this file free of command logic.
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { main } from "../src/node/cli.mjs";

export { main };

if (
  process.argv[1] &&
  fs.realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)
)
  process.exitCode = await main();
