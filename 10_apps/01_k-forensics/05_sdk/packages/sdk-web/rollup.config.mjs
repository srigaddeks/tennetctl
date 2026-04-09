import typescript from '@rollup/plugin-typescript';
import replace from '@rollup/plugin-replace';
import terser from '@rollup/plugin-terser';
import { readFileSync } from 'fs';

// ─── Worker inline plugin ────────────────────────────────────────────────────

function workerInlinePlugin(workerPath) {
  return {
    name: 'worker-inline',
    resolveId(source) {
      if (source === '\0worker-source') return source;
      return null;
    },
    load(id) {
      if (id === '\0worker-source') {
        try {
          const src = readFileSync(workerPath, 'utf-8');
          return `export default ${JSON.stringify(src)};`;
        } catch {
          return 'export default "";';
        }
      }
      return null;
    },
    transform(code) {
      if (code.includes('__WORKER_SOURCE__')) {
        return code
          .replace(
            "declare const __WORKER_SOURCE__: string;",
            "import __WORKER_SOURCE__ from '\\0worker-source';",
          )
          .replace(
            /typeof __WORKER_SOURCE__ !== 'undefined' \? __WORKER_SOURCE__ : ''/,
            '__WORKER_SOURCE__',
          );
      }
      return null;
    },
  };
}

// ─── Build mode ──────────────────────────────────────────────────────────────

const isProd = process.env.BUILD_MODE === 'production';

const tsPlugin = (tsconfig) =>
  typescript({ tsconfig, declaration: false, declarationMap: false });

const prodTerser = () =>
  terser({
    compress: { drop_console: true, drop_debugger: true, passes: 3, pure_getters: true },
    mangle: { properties: { regex: /^_/ } },
    format: { comments: false },
  });

// ═════════════════════════════════════════════════════════════════════════════
// STEP 1: Worker bundle (built first, then inlined into main bundle)
// ═════════════════════════════════════════════════════════════════════════════

const workerBundle = {
  input: 'src/runtime/worker-entry.ts',
  output: {
    file: 'dist/kprotect.worker.js',
    format: 'iife',
    name: 'KProtectWorker',
    sourcemap: !isProd,
    compact: true,
  },
  plugins: [
    tsPlugin('./tsconfig.worker.json'),
    replace({ preventAssignment: true, values: { 'process.env.NODE_ENV': JSON.stringify(isProd ? 'production' : 'development') } }),
    ...(isProd ? [prodTerser()] : []),
  ],
};

// ═════════════════════════════════════════════════════════════════════════════
// STEP 2: Main bundle (IIFE for <script> tag)
// ═════════════════════════════════════════════════════════════════════════════

const mainBundle = {
  input: 'src/index.ts',
  output: {
    file: isProd ? 'dist/kprotect.min.js' : 'dist/kprotect.dev.js',
    format: 'iife',
    name: 'KProtectModule',
    sourcemap: !isProd,
    compact: isProd,
    footer: 'window.KProtect = KProtectModule.KProtect;',
  },
  plugins: [
    workerInlinePlugin('dist/kprotect.worker.js'),
    tsPlugin('./tsconfig.json'),
    replace({ preventAssignment: true, values: { 'process.env.NODE_ENV': JSON.stringify(isProd ? 'production' : 'development') } }),
    ...(isProd ? [prodTerser()] : []),
  ],
};

// ═════════════════════════════════════════════════════════════════════════════
// STEP 3: ESM bundle
// ═════════════════════════════════════════════════════════════════════════════

const esmBundle = {
  input: 'src/index.ts',
  output: {
    file: 'dist/kprotect.esm.js',
    format: 'es',
    sourcemap: true,
  },
  plugins: [
    workerInlinePlugin('dist/kprotect.worker.js'),
    tsPlugin('./tsconfig.json'),
  ],
};

export default [workerBundle, mainBundle, esmBundle];
