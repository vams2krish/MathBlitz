import { cp, mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));

export async function stageGuest(directory) {
  const dest = resolve(directory);
  const source = resolve(root, 'frontend');
  if (dest === source) throw new Error('The guest output must not overwrite the account frontend.');
  await mkdir(dest, { recursive: true });
  await cp(resolve(source, 'assets'), resolve(dest, 'assets'), { recursive: true });
  const marker = '<meta name="mathblitz-mode" content="accounts">';
  const html = await readFile(resolve(source, 'index.html'), 'utf8');
  if (!html.includes(marker)) throw new Error('Missing MathBlitz mode marker.');
  const csp = `<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'">`;
  await writeFile(resolve(dest, 'index.html'), html.replace(marker, `${marker.replace('accounts', 'guest')}\n    ${csp}`));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (!process.argv[2]) throw new Error('Usage: node scripts/stage_guest.mjs OUTPUT_DIRECTORY');
  await stageGuest(process.argv[2]);
}
