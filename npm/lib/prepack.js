'use strict';

// `npm prepack` hook: stage a copy of the Python package inside npm/python so
// the published tarball is self-contained. The copy is generated, never edited
// by hand, and is git-ignored.

const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..', '..');
const source = path.join(root, 'src', 'get_fsa_training_done');
const target = path.join(root, 'npm', 'python', 'get_fsa_training_done');

const SKIP_DIRS = new Set(['__pycache__', '.pytest_cache']);
const SKIP_EXTENSIONS = new Set(['.pyc', '.pyo']);

function copyTree(from, to) {
  fs.mkdirSync(to, { recursive: true });
  for (const entry of fs.readdirSync(from, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      if (SKIP_DIRS.has(entry.name)) continue;
      copyTree(path.join(from, entry.name), path.join(to, entry.name));
    } else if (entry.isFile()) {
      if (SKIP_EXTENSIONS.has(path.extname(entry.name))) continue;
      if (entry.name === '.DS_Store') continue;
      fs.copyFileSync(path.join(from, entry.name), path.join(to, entry.name));
    }
  }
}

fs.rmSync(path.join(root, 'npm', 'python'), { recursive: true, force: true });
copyTree(source, target);

const version = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8')).version;
const about = fs.readFileSync(path.join(target, '__about__.py'), 'utf8');
const match = about.match(/^__version__\s*=\s*"([^"]+)"/m);
if (!match || match[1] !== version) {
  process.stderr.write(
    `ERROR: package.json is ${version} but __about__.py is ${match ? match[1] : 'unreadable'}.\n` +
      '       Run: python scripts/sync_version.py\n'
  );
  process.exit(1);
}

process.stdout.write(`staged get_fsa_training_done ${version} into npm/python\n`);
