#!/usr/bin/env node
'use strict';

// Thin delegation to the Python implementation. There is deliberately no
// postinstall step: `npx fsa-trainer-skills install --platform all` has to
// work on a machine that has Node and a system Python and nothing else.

const { spawnSync } = require('node:child_process');
const path = require('node:path');
const { findPython, MIN_VERSION, PACKAGE_NAME } = require('../lib/locate.js');

const found = findPython();
if (!found) {
  const want = MIN_VERSION.join('.');
  process.stderr.write(
    `ERROR: ${PACKAGE_NAME} needs Python ${want} or newer on PATH.\n` +
      '       Install Python, or point FSA_TRAINER_SKILLS_PYTHON at an interpreter.\n' +
      '       You can also install directly with: pip install ' +
      PACKAGE_NAME +
      '\n'
  );
  process.exit(127);
}

const pythonDir = path.join(__dirname, '..', 'python');
const env = { ...process.env };
env.PYTHONPATH = [pythonDir, env.PYTHONPATH].filter(Boolean).join(path.delimiter);

const result = spawnSync(found.executable, ['-m', 'fsa_trainer_skills', ...process.argv.slice(2)], {
  stdio: 'inherit',
  env
});

if (result.error) {
  process.stderr.write(`ERROR: could not run ${found.executable}: ${result.error.message}\n`);
  process.exit(126);
}
process.exit(result.status === null ? 1 : result.status);
