import { readFile } from "node:fs/promises";

const requiredFiles = [
  "index.html",
  "package.json",
  "tsconfig.json",
  "tsconfig.app.json",
  "tsconfig.node.json",
  "vite.config.ts",
  "src/App.tsx",
  "src/main.tsx",
  "src/styles.css",
];

const readText = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

await Promise.all(requiredFiles.map(readText));

const [indexHtml, packageJson, appSource, mainSource] = await Promise.all([
  readText("index.html"),
  readText("package.json"),
  readText("src/App.tsx"),
  readText("src/main.tsx"),
]);

const packageManifest = JSON.parse(packageJson);

const checks = [
  [indexHtml.includes('<div id="root"></div>'), "index.html must expose the React root"],
  [Boolean(packageManifest.scripts?.build), "package.json must define a build script"],
  [Boolean(packageManifest.scripts?.typecheck), "package.json must define a typecheck script"],
  [appSource.includes("Technician Console"), "App shell must render the technician console"],
  [mainSource.includes("createRoot(rootElement)"), "main.tsx must mount the React app"],
];

const failures = checks.filter(([passed]) => !passed).map(([, message]) => message);

if (failures.length > 0) {
  throw new Error(`Frontend scaffold verification failed:\n- ${failures.join("\n- ")}`);
}

console.log("Frontend scaffold verification passed.");
