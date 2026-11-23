# Install ZORO VIDEO DIRECTOR PRO

## Recommended: ask Claude Code to install it

Open Claude Code in the root of the project where you want video-production support, then paste:

```text
Install ZORO VIDEO DIRECTOR PRO directly from https://github.com/tomhek820-stack/wave.git.

First inspect my current project and its CLAUDE.md / .claude directory. Then run the repository installer from a temporary clone, targeting this project root:
git clone --depth 1 https://github.com/tomhek820-stack/wave.git /tmp/zoro-video-director-pro
bash /tmp/zoro-video-director-pro/install.sh

After installation, verify that:
1. .zoro-video-director-pro/ contains the director instructions and schema.
2. .claude/skills/zoro-video-production/SKILL.md exists.
3. CLAUDE.md contains the managed ZORO VIDEO DIRECTOR PRO block and all previous instructions remain intact.
4. zoro-video-input/README_INPUT.md exists.

Do not overwrite unrelated project files. If any target already exists, inspect and preserve user content. Report the exact files installed and any conflicts. Do not start producing a video yet.
```

The installer clones the official repository itself into a temporary directory, then installs its managed instruction package into the current project.

## Manual installation

From the root of the target project:

```bash
git clone --depth 1 https://github.com/tomhek820-stack/wave.git /tmp/zoro-video-director-pro
bash /tmp/zoro-video-director-pro/install.sh
```

## Target another project directory

```bash
ZORO_VIDEO_TARGET="/path/to/project" bash /tmp/zoro-video-director-pro/install.sh
```

## Refresh managed files

By default, existing managed files are preserved and new candidates are written with a `.new` suffix. To intentionally replace managed director files with the latest repository versions:

```bash
ZORO_VIDEO_FORCE=1 bash /tmp/zoro-video-director-pro/install.sh
```

Review your project changes before using force mode. The installer does not delete project files.

## Claude Web

Claude Web cannot run this shell installer in an ordinary chat unless a supported execution environment is available. For Claude Web, upload `CLAUDE.md`, `DIRECTOR_SYSTEM.md`, `WORKFLOW.md`, `QUALITY_CONTROL.md`, `SCENE_SCHEMA.json`, and `CLAUDE_WEB_PROMPT.md` from the repository.
