'use strict';

// Finding a usable Python, once, and remembering the answer.
//
// The npm package is a shim: all the logic lives in the Python package that
// ships alongside it under npm/python. We only need an interpreter new enough
// to run it. Probing costs a process spawn, so the result is cached next to the
// managed environments and keyed on the candidate's resolved path.

const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const MIN_VERSION = [3, 10];
const PACKAGE_NAME = 'get-fsa-training-done';

function cacheFile() {
  const home = process.env.GET_FSA_TRAINING_DONE_HOME
    ? path.resolve(process.env.GET_FSA_TRAINING_DONE_HOME)
    : path.join(
        process.env.XDG_CACHE_HOME || path.join(os.homedir(), '.cache'),
        PACKAGE_NAME
      );
  return path.join(home, 'node-python.json');
}

function candidates() {
  const explicit = process.env.GET_FSA_TRAINING_DONE_PYTHON;
  const list = explicit ? [explicit] : [];
  if (process.platform === 'win32') {
    list.push('python', 'py');
  } else {
    list.push('python3', 'python');
  }
  return list;
}

function probe(command) {
  const result = spawnSync(
    command,
    ['-c', 'import sys; print("%d.%d" % sys.version_info[:2]); print(sys.executable)'],
    { encoding: 'utf8' }
  );
  if (result.status !== 0 || !result.stdout) return null;
  const [version, executable] = result.stdout.trim().split('\n');
  if (!version || !executable) return null;
  const [major, minor] = version.split('.').map(Number);
  if (major < MIN_VERSION[0] || (major === MIN_VERSION[0] && minor < MIN_VERSION[1])) {
    return null;
  }
  return { executable: executable.trim(), version };
}

function readCache() {
  try {
    const data = JSON.parse(fs.readFileSync(cacheFile(), 'utf8'));
    if (data && data.executable && fs.existsSync(data.executable)) return data;
  } catch {
    // A missing or corrupt cache just means we probe again.
  }
  return null;
}

function writeCache(found) {
  try {
    const file = cacheFile();
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, JSON.stringify(found, null, 2) + '\n');
  } catch {
    // Caching is an optimisation; failing to write it is not an error.
  }
}

function findPython() {
  if (!process.env.GET_FSA_TRAINING_DONE_PYTHON) {
    const cached = readCache();
    if (cached) return cached;
  }
  for (const command of candidates()) {
    const found = probe(command);
    if (found) {
      writeCache(found);
      return found;
    }
  }
  return null;
}

module.exports = { findPython, MIN_VERSION, PACKAGE_NAME };
