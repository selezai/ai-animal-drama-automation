/**
 * Render a pet tip video using Remotion.
 * Usage: node scripts/render_video.js --props='{"petType":"dog","hook":"...","teach":"...","why":"...","cta":"...","audioSrc":"audio/narration.mp3"}' --output=output/video/tip.mp4
 */
const path = require('path');
const {bundle} = require('@remotion/bundler');
const {renderMedia, selectComposition} = require('@remotion/renderer');

async function main() {
  const args = process.argv.slice(2);

  let propsJson = '{}';
  let outputFile = null;

  for (const arg of args) {
    if (arg.startsWith('--props=')) {
      propsJson = arg.slice('--props='.length);
    } else if (arg.startsWith('--output=')) {
      outputFile = arg.slice('--output='.length);
    }
  }

  const inputProps = JSON.parse(propsJson);

  if (!outputFile) {
    const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    outputFile = path.join(__dirname, '..', 'output', 'video', `pet_tip_${ts}.mp4`);
  }

  const entryPoint = path.resolve(__dirname, '..', 'remotion', 'src', 'index.ts');

  console.log('Bundling Remotion project...');
  const bundleLocation = await bundle({
    entryPoint,
    webpackOverride: (config) => config,
  });

  console.log('Selecting composition...');
  const composition = await selectComposition({
    serveUrl: bundleLocation,
    id: 'PetTip',
    inputProps,
  });

  console.log(`Rendering ${composition.durationInFrames} frames → ${outputFile}`);
  await renderMedia({
    composition,
    serveUrl: bundleLocation,
    codec: 'h264',
    outputLocation: outputFile,
    inputProps,
    onProgress: ({progress}) => {
      process.stdout.write(`\rProgress: ${Math.round(progress * 100)}%`);
    },
  });

  console.log(`\nVideo rendered: ${outputFile}`);
  return outputFile;
}

main().catch((err) => {
  console.error('Render failed:', err.message);
  process.exit(1);
});
