#!/usr/bin/env -S npx -y tsx

import { spawnSync, SpawnSyncOptions } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as readline from 'node:readline';

const AIX: string = process.env.AIX_BIN ?? 'aix';

const SCRIPT_PATH: string = process.argv[1] ?? path.resolve('.');

const PUBLIC_REPO: string =
   process.env.AIX_PUBLIC_REPO ??
   (process.env.AIX_PROJECTS_DIR
      ? path.resolve(process.env.AIX_PROJECTS_DIR, 'aix-config')
      : path.resolve(SCRIPT_PATH, '..', '..', '..'));

const PRIVATE_REPO: string =
   process.env.AIX_PRIVATE_REPO ??
   (process.env.AIX_PROJECTS_DIR
      ? path.resolve(process.env.AIX_PROJECTS_DIR, 'aix-config-private')
      : path.resolve(PUBLIC_REPO, '..', 'aix-config-private'));

const SKILL_DIR: string = 'skills';

/** Outcome of running a subprocess for aix-skill commands. */
interface RunResult {
   stdout: string;
   stderr: string;
   status: number | null;
   error?: Error;
}

/** Parsed CLI arguments. */
interface ParsedArgs {
   command: string;
   positional: string[];
   options: {
      description?: string;
      category?: string;
      visibility?: string;
      keep: boolean;
   };
}

/** Print an error message and exit the process. */
function fail(message: string): never {
   console.error(`ERROR ${message}`);
   process.exit(1);
}

/** Run a command and return the captured or inherited result. */
function run(command: string[], options: { cwd?: string; stdio?: 'pipe' | 'inherit'; check?: boolean } = {}): RunResult {
   const { cwd, stdio = 'pipe', check = true } = options;
   const opts: SpawnSyncOptions = { cwd, stdio, encoding: 'utf8' };
   const result = spawnSync(command[0], command.slice(1), opts);
   const stdout = (result.stdout ?? '').toString();
   const stderr = (result.stderr ?? '').toString();
   if (check && result.status !== 0) {
      throw new Error(stderr || `Command failed: ${command.join(' ')}`);
   }
   return {
      stdout,
      stderr,
      status: result.status,
      error: result.error ?? undefined,
   };
}

/** Run the aix CLI. */
function aix(args: string[], options: { cwd?: string; stdio?: 'pipe' | 'inherit'; check?: boolean } = {}): RunResult {
   return run([AIX, ...args], options);
}

/** Exit if the aix binary cannot be found. */
function ensureAix(): void {
   const result = aix(['--version'], { stdio: 'pipe', check: false });
   if (result.error || result.status !== 0) {
      fail(`Could not find aix binary: ${AIX}`);
   }
}

/** Return the local path to a skill's SKILL.md. */
function skillFile(name: string): string {
   return path.join(SKILL_DIR, name, 'SKILL.md');
}

/** Check whether a local skill already exists. */
function skillExists(name: string): boolean {
   return fs.existsSync(skillFile(name));
}

/** Create ai.json in the current project if it is missing. */
function initProject(): void {
   if (!fs.existsSync('ai.json')) {
      aix(['init']);
   }
}

/** Create a draft skill in the current project and install it. */
function newSkill(name: string, description?: string): void {
   if (!name) {
      fail('Skill name is required');
   }
   if (skillExists(name)) {
      fail(`Skill already exists: ${skillFile(name)}`);
   }
   initProject();
   const file = skillFile(name);
   fs.mkdirSync(path.dirname(file), { recursive: true });
   const content = `---
name: ${name}
description: ${description ?? `Skill for ${name}`}
---

# ${name}

TODO: describe what this skill does and when to use it.
`;
   fs.writeFileSync(file, content);
   aix(['add', 'skill', `./${SKILL_DIR}/${name}`, '--name', name]);
   console.info(`Draft skill created: ${file}`);
}

/** Open a draft skill in $EDITOR and refresh the install. */
function editSkill(name: string): void {
   if (!name) {
      fail('Skill name is required');
   }
   const file = skillFile(name);
   if (!fs.existsSync(file)) {
      fail(`Skill not found: ${file}`);
   }
   const editor = process.env.EDITOR;
   if (editor) {
      run([...editor.split(' '), file], { stdio: 'inherit' });
      aix(['install']);
   } else {
      console.info(`Open ${file} in your editor, then run "aix-skill install" to refresh.`);
   }
}

/** Re-install the current project's ai.json. */
function installSkills(): void {
   if (!fs.existsSync('ai.json')) {
      fail('No ai.json found. Run "aix-skill new <name>" first.');
   }
   aix(['install']);
}

/** Ask the user whether to publish as public or private. */
function promptVisibility(): Promise<string> {
   return new Promise((resolve, reject) => {
      if (!process.stdin.isTTY) {
         reject(new Error('Use --public or --private when not running in a terminal'));
         return;
      }
      const rl = readline.createInterface({
         input: process.stdin,
         output: process.stdout,
      });
      rl.question('Publish as public or private? ', (answer: string) => {
         rl.close();
         const chosen = answer.trim().toLowerCase();
         if (chosen === 'public' || chosen === 'private') {
            resolve(chosen);
         } else {
            reject(new Error("Answer must be 'public' or 'private'"));
         }
      });
   });
}

/** Return the destination path for a skill in a target repo. */
function targetSkillDir(repo: string, name: string, category?: string): string {
   if (category) {
      return path.join(repo, SKILL_DIR, category, name);
   }
   return path.join(repo, SKILL_DIR, name);
}

/** Remove a skill from the current project. */
function removeLocalSkill(name: string): void {
   const hasConfig = fs.existsSync('ai.json') || fs.existsSync('ai.local.json');
   if (hasConfig) {
      aix(['remove', 'skill', name, '--yes', '--no-delete'], {
         stdio: 'pipe',
         check: false,
      });
   }
   const dir = path.join(SKILL_DIR, name);
   if (fs.existsSync(dir)) {
      fs.rmSync(dir, { recursive: true, force: true });
   }
}

/** Promote a local draft skill to the public or private aix-config repo. */
async function pushSkill(name: string, visibility: string | undefined, category: string | undefined, keep: boolean): Promise<void> {
   if (!name) {
      fail('Skill name is required');
   }
   const sourceDir = path.join(SKILL_DIR, name);
   if (!fs.existsSync(path.join(sourceDir, 'SKILL.md'))) {
      fail(`Skill not found: ${sourceDir}`);
   }
   const chosen = visibility ?? (await promptVisibility());
   const targetRepo = chosen === 'public' ? PUBLIC_REPO : PRIVATE_REPO;
   if (!fs.existsSync(targetRepo)) {
      fail(`Target repo not found: ${targetRepo}`);
   }
   if (!fs.existsSync(path.join(targetRepo, '.git'))) {
      fail(`Not a git repository: ${targetRepo}`);
   }
   const targetDir = targetSkillDir(targetRepo, name, category);
   if (fs.existsSync(targetDir)) {
      fs.rmSync(targetDir, { recursive: true, force: true });
   }
   fs.cpSync(sourceDir, targetDir, { recursive: true, force: true });
   const relParts = [SKILL_DIR];
   if (category) {
      relParts.push(category);
   }
   relParts.push(name);
   const relPath = `./${relParts.join('/')}`;
   aix(['add', 'skill', relPath, '--name', name, '--no-install'], { cwd: targetRepo });
   const addPaths = [path.join(targetRepo, 'ai.json')];
   const lockFile = path.join(targetRepo, 'ai.lock.json');
   if (fs.existsSync(lockFile)) {
      addPaths.push(lockFile);
   }
   addPaths.push(targetDir);
   run(['git', 'add', ...addPaths], { cwd: targetRepo });
   const diff = run(['git', 'diff', '--cached', '--quiet'], {
      cwd: targetRepo,
      stdio: 'pipe',
      check: false,
   });
   if (diff.status !== 0) {
      run(['git', 'commit', '-m', `feat: add skill ${name}`], { cwd: targetRepo });
      run(['git', 'push', 'origin', 'master'], { cwd: targetRepo });
   } else {
      console.info('No changes to commit');
   }
   aix(['install'], { cwd: targetRepo });
   console.info(`Pushed ${name} to ${chosen} repo`);
   if (!keep) {
      removeLocalSkill(name);
   }
}

/** Remove a draft skill from the current project. */
function rmSkill(name: string): void {
   if (!name) {
      fail('Skill name is required');
   }
   if (!skillExists(name)) {
      fail(`Skill not found: ${skillFile(name)}`);
   }
   removeLocalSkill(name);
   console.info(`Removed ${name} from current project`);
}

/** Show local drafts and configured repo paths. */
function showStatus(): void {
   const skillEntries = fs.existsSync(SKILL_DIR) ? fs.readdirSync(SKILL_DIR) : [];
   const drafts = skillEntries
      .filter((entry: string) => {
         return fs.statSync(path.join(SKILL_DIR, entry)).isDirectory();
      })
      .sort();
   console.info(`Local drafts: ${drafts.length ? drafts.join(', ') : 'none'}`);
   console.info(`Public repo: ${PUBLIC_REPO} (${fs.existsSync(PUBLIC_REPO) ? 'found' : 'not found'})`);
   console.info(`Private repo: ${PRIVATE_REPO} (${fs.existsSync(PRIVATE_REPO) ? 'found' : 'not found'})`);
}

/** Print usage information. */
function usage(): void {
   console.info(`Usage: aix-skill <command> [args]

Commands:
  new <name> [--description "..."]      Create a draft skill in the current project
  edit <name>                           Open a draft skill in $EDITOR
  install                               Re-install ai.json to refresh skills
  push <name> --public|--private        Promote a draft to aix-config
           [--category <dir>] [--keep]
  rm <name>                             Remove a draft skill from the current project
  status                                Show drafts and configured repo paths
  help                                  Show this message

Environment:
  AIX_PUBLIC_REPO   Path to public aix-config clone (auto-detected from aix-skill)
  AIX_PRIVATE_REPO  Path to private aix-config clone (auto-detected sibling)
  AIX_PROJECTS_DIR  Base directory for aix-config clones (overrides auto-detection)
  AIX_BIN           aix binary name or path (default aix)
  EDITOR            Editor used by edit command
`);
}

/** Parse command-line arguments into a structured object. */
function parseArgs(argv: string[]): ParsedArgs {
   const args = argv.slice(2);
   if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
      return { command: 'help', positional: [], options: { keep: false } };
   }
   const command = args.shift() as string;
   const positional: string[] = [];
   const options: ParsedArgs['options'] = { keep: false };
   for (let i = 0; i < args.length; i += 1) {
      const arg = args[i];
      if (arg === '--description') {
         options.description = args[i + 1];
         i += 1;
      } else if (arg === '--category') {
         options.category = args[i + 1];
         i += 1;
      } else if (arg === '--public') {
         options.visibility = 'public';
      } else if (arg === '--private') {
         options.visibility = 'private';
      } else if (arg === '--keep') {
         options.keep = true;
      } else if (arg.startsWith('-')) {
         fail(`Unknown flag: ${arg}`);
      } else {
         positional.push(arg);
      }
   }
   return { command, positional, options };
}

/** Dispatch to the requested command. */
async function main(): Promise<void> {
   const { command, positional, options } = parseArgs(process.argv);
   const name = positional[0];
   if (command === 'help') {
      usage();
      return;
   }
   ensureAix();
   switch (command) {
      case 'new':
         newSkill(name, options.description);
         break;
      case 'edit':
         editSkill(name);
         break;
      case 'install':
         installSkills();
         break;
      case 'push':
         await pushSkill(name, options.visibility, options.category, options.keep);
         break;
      case 'rm':
         rmSkill(name);
         break;
      case 'status':
         showStatus();
         break;
      default:
         fail(`Unknown command: ${command}`);
   }
}

main().catch((err: unknown) => {
   console.error(`ERROR ${err instanceof Error ? err.message : String(err)}`);
   process.exit(1);
});
