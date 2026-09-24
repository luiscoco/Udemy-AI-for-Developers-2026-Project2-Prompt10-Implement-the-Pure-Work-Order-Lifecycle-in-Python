// Contract drift guard (`npm run verify:contract`).
//
// Regenerates the TypeScript and Python models from packages/contract/openapi.yaml into
// temporary files and compares them byte-for-byte with the committed generated files.
// The working tree is never written to. Exits non-zero, naming each stale file, when
// either output differs, or when a generator fails.
import { spawnSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const contractDir = join(root, 'packages/contract');
const backendDir = join(root, 'apps/backend');

/**
 * Runs a command without a shell (the repo path may contain spaces) and throws on failure.
 * @param {string} command @param {string[]} args @param {string} cwd
 */
function run(command, args, cwd) {
  const result = spawnSync(command, args, { cwd, stdio: ['ignore', 'pipe', 'pipe'], encoding: 'utf8' });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`\`${command} ${args.join(' ')}\` exited with ${String(result.status)}\n${result.stderr}`);
  }
}

/**
 * Each generator mirrors a root `contract:generate:*` script, with only the output path
 * redirected into a temporary directory created under `tmpParent`.
 * @type {{ label: string, committed: string, tmpParent: string, generate: (tmp: string) => string }[]}
 */
const generators = [
  {
    label: 'TypeScript (openapi-typescript)',
    committed: 'packages/contract/src/types.gen.ts',
    tmpParent: tmpdir(),
    generate: (tmp) => {
      // Same CLI and arguments as the `generate` script in packages/contract/package.json.
      const require = createRequire(join(contractDir, 'package.json'));
      const pkgPath = require.resolve('openapi-typescript/package.json');
      /** @type {{ bin: Record<string, string> }} */
      const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
      const cli = join(dirname(pkgPath), pkg.bin['openapi-typescript'] ?? '');
      const output = join(tmp, 'types.gen.ts');
      run(process.execPath, [cli, 'openapi.yaml', '--output', output], contractDir);
      return output;
    },
  },
  {
    label: 'Python (datamodel-codegen)',
    committed: 'apps/backend/app/generated/contract_models.py',
    // The output is post-formatted by ruff, which reads its settings (line length, ...) from
    // the pyproject.toml nearest to the output file. Under the OS temp dir it would fall back
    // to ruff's defaults and never match, so the temp dir lives inside apps/backend.
    tmpParent: backendDir,
    generate: (tmp) => {
      // All other options come from [tool.datamodel-codegen] in apps/backend/pyproject.toml.
      const output = join(tmp, 'contract_models.py');
      run('uv', ['run', '--directory', backendDir, 'datamodel-codegen', '--output', output], backendDir);
      return output;
    },
  },
];

/** @type {string[]} */
const stale = [];
let failed = false;
for (const generator of generators) {
  const tmp = mkdtempSync(join(generator.tmpParent, '.verify-contract-'));
  let fresh;
  try {
    fresh = readFileSync(generator.generate(tmp));
  } catch (error) {
    failed = true;
    console.error(`verify:contract: ${generator.label} generation failed.`);
    console.error(error instanceof Error ? error.message : error);
    continue;
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
  const committedPath = join(root, generator.committed);
  const committed = existsSync(committedPath) ? readFileSync(committedPath) : undefined;
  const ok = committed?.equals(fresh) ?? false;
  console.log(`  ${ok ? 'ok   ' : 'STALE'}  ${generator.committed}`);
  if (!ok) stale.push(`${generator.committed}  (${generator.label}${committed ? '' : ', file missing'})`);
}

if (failed) process.exit(1);

if (stale.length > 0) {
  console.error('\nverify:contract: FAILED. Committed generated files differ from packages/contract/openapi.yaml:');
  for (const line of stale) console.error(`  - ${line}`);
  console.error('\nRun `npm run contract:generate`, review the diff, and commit the result.');
  console.error('Never edit generated files by hand.');
  process.exit(1);
}

console.log('\nverify:contract: generated TypeScript and Python models match openapi.yaml.');
