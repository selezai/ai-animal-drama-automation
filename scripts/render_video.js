/**
 * Render a pet tip video using Remotion.
 * Usage: node scripts/render_video.js --props='{"petType":"dog","hook":"...","teach":"...","why":"...","cta":"...","audioSrc":"audio/narration.mp3"}' --output=output/video/tip.mp4
 */
const path = require('path');
const fs = require('fs');
const {bundle} = require('@remotion/bundler');
const {renderMedia, renderStill, selectComposition} = require('@remotion/renderer');

// Use local ffmpeg/ffprobe if available (avoids macOS SDK mismatch with Remotion's bundled binaries)
const localFfmpeg = path.resolve(__dirname, '..', 'bin', 'ffmpeg');
const localFfprobe = path.resolve(__dirname, '..', 'bin', 'ffprobe');
const ffmpegExecutable = fs.existsSync(localFfmpeg) ? localFfmpeg : undefined;
const ffprobeExecutable = fs.existsSync(localFfprobe) ? localFfprobe : undefined;
if (ffmpegExecutable) console.log(`Using local ffmpeg: ${ffmpegExecutable}`);

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

  const FPS = 30;
  const audioDurationSecs = inputProps.audioDurationSecs || 30;
  const durationInFrames = Math.ceil(audioDurationSecs * FPS);
  console.log(`Audio duration: ${audioDurationSecs.toFixed(2)}s → ${durationInFrames} frames`);

  console.log('Selecting composition...');
  const composition = await selectComposition({
    serveUrl: bundleLocation,
    id: 'PetTip',
    inputProps,
    timeoutInMilliseconds: 30000,
  });

  // Override duration to match actual audio length
  composition.durationInFrames = durationInFrames;
  composition.fps = FPS;

  console.log(`Rendering ${composition.durationInFrames} frames → ${outputFile}`);
  await renderMedia({
    composition,
    serveUrl: bundleLocation,
    codec: 'h264',
    outputLocation: outputFile,
    inputProps,
    ffmpegExecutable,
    ffprobeExecutable,
    onProgress: ({progress}) => {
      process.stdout.write(`\rProgress: ${Math.round(progress * 100)}%`);
    },
  });

  console.log(`\nVideo rendered: ${outputFile}`);

  // Render thumbnail at frame 1 (first scene fully visible)
  const thumbFile = outputFile.replace(/\.mp4$/, '_thumb.jpg');
  console.log(`Rendering thumbnail → ${thumbFile}`);
  await renderStill({
    composition,
    serveUrl: bundleLocation,
    output: thumbFile,
    inputProps,
    frame: 1,
    imageFormat: 'jpeg',
    jpegQuality: 90,
    ffmpegExecutable,
    ffprobeExecutable,
  });
  console.log(`Thumbnail rendered: ${thumbFile}`);

  // Print thumb path so Python can read it from stdout
  console.log(`THUMBNAIL_PATH=${thumbFile}`);
  return outputFile;
}

main().catch((err) => {
  console.error('Render failed:', err.message);
  process.exit(1);
});
