import { Resvg } from '@resvg/resvg-js';
import { PNG } from 'pngjs';
import { mkdir, readFile, writeFile } from 'node:fs/promises';

const svg = await readFile(new URL('../frontend/assets/logo.svg', import.meta.url), 'utf8');
const icon = (size, source = svg) => new Resvg(source, { fitTo: { mode: 'width', value: size } }).render().asPng();
const iosIcon = new URL('../ios/native/App/App/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png', import.meta.url);
await mkdir(new URL('./', iosIcon), { recursive: true });
const opaqueIcon = PNG.sync.read(icon(1024, svg.replace(' rx="26"', '')));
await writeFile(iosIcon, PNG.sync.write(opaqueIcon, { colorType: 2 }));
const sizes = [16, 32, 48, 64, 128, 256];
const ico = Buffer.alloc(6 + sizes.length * 16);
ico.writeUInt16LE(1, 2);
ico.writeUInt16LE(sizes.length, 4);
let offset = ico.length;
const frames = sizes.map((size, index) => {
  const png = icon(size);
  const entry = 6 + index * 16;
  ico[entry] = ico[entry + 1] = size % 256;
  ico.writeUInt16LE(1, entry + 4);
  ico.writeUInt16LE(32, entry + 6);
  ico.writeUInt32LE(png.length, entry + 8);
  ico.writeUInt32LE(offset, entry + 12);
  offset += png.length;
  return png;
});
await writeFile(new URL('./mathblitz.ico', import.meta.url), Buffer.concat([ico, ...frames]));
const splash = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" fill="#f5f7fb"/><g transform="translate(192 192)">${svg.slice(svg.indexOf('>') + 1, svg.lastIndexOf('</svg>'))}</g></svg>`;
for (const name of ['splash-2732x2732-2.png', 'splash-2732x2732-1.png', 'splash-2732x2732.png']) {
  await writeFile(new URL(`../Splash.imageset/${name}`, iosIcon), icon(1024, splash));
}
