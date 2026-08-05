#!/usr/bin/env node
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { dirname } from "node:path";
import { qualifyOfflinePwa } from "../src/pwa/qualification/service.js";
import { formatQualificationReceipt } from "../src/pwa/qualification/formatting.js";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(here, "..");
const json = process.argv.includes("--json");
const receipt = await qualifyOfflinePwa({ frontendRoot });
console.log(json ? JSON.stringify(receipt, null, 2) : formatQualificationReceipt(receipt));
process.exitCode = receipt.status === "PASSED" ? 0 : 2;
