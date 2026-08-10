# aix-config

[AIX](https://github.com/a1st-dev/aix) config, skills, and prompts.

## Set up a New Repo

```bash
npx @a1st/aix install https://github.com/MrMarCode/aix-config/blob/master/ai.json
```

## Skill authoring with `aix-skill`

`skills/skill-author/aix-skill` is a TypeScript helper for drafting and publishing
AIX skills. The script runs through `npx tsx`, so it needs no build step. Add the
`skills/skill-author` directory to your `PATH` and run `aix-skill` from any
project.

```bash
export PATH="/path/to/aix-config/skills/skill-author:$PATH"
aix-skill new my-skill --description "What this skill does"
aix-skill edit my-skill
aix-skill status
aix-skill push my-skill --public --category productivity
```

### Optional environment overrides

- `AIX_PUBLIC_REPO` — path to your public aix-config clone
  (auto-detected from the aix-skill script location)
- `AIX_PRIVATE_REPO` — path to your private aix-config clone
  (auto-detected as a sibling of the public clone)
- `AIX_PROJECTS_DIR` — base directory for local aix-config clones; when set,
  overrides auto-detection for both public and private defaults
- `AIX_BIN` — `aix` binary name or path (default `aix`)
- `EDITOR` — editor used by `aix-skill edit`

### Development

To type-check the helper, install dependencies inside the skill directory and
run `tsc`:

```bash
cd skills/skill-author
npm install
npm run typecheck
```
