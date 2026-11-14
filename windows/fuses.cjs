const { join } = require('node:path');
const { flipFuses, FuseVersion, FuseV1Options } = require('@electron/fuses');

module.exports = async ({ appOutDir, packager, electronPlatformName }) => {
  if (electronPlatformName !== 'win32') return;
  await flipFuses(join(appOutDir, `${packager.appInfo.productFilename}.exe`), {
    version: FuseVersion.V1,
    [FuseV1Options.RunAsNode]: false,
    [FuseV1Options.EnableNodeOptionsEnvironmentVariable]: false,
    [FuseV1Options.EnableNodeCliInspectArguments]: false,
    [FuseV1Options.OnlyLoadAppFromAsar]: true,
    [FuseV1Options.EnableEmbeddedAsarIntegrityValidation]: true,
  });
};
