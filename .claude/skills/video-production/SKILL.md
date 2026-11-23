---
name: video-production
description: Plan and produce a complete narrated video from supplied audio, exact voiceover text, and video content. Use when the user asks to create, edit, render, or quality-check a video.
---

# ZORO Video Production Skill

1. Read root `CLAUDE.md`, `DIRECTOR_SYSTEM.md`, `WORKFLOW.md`, and `QUALITY_CONTROL.md`.
2. Inspect inputs and available tools. Do not assume image/video generation capabilities.
3. Treat supplied audio as the timing master and supplied voiceover text as immutable reference.
4. Create a creative brief and scene plan using `SCENE_SCHEMA.json`.
5. For every scene, select a visual representation that directly explains its narrative beat.
6. If assets are missing, generate them with an actually available tool. Never ask the user to provide ordinary scene images. If no image-generation tool exists, use feasible vector/programmatic graphics or licensed assets and disclose the substitution.
7. Maintain continuity references for recurring people, places, objects, and visual style.
8. Render, generate synchronized subtitles, and run every applicable release gate in `QUALITY_CONTROL.md`.
9. Fix failures and rerun relevant checks. Never report unrun tests as passed.
10. Deliver final video, subtitles, scene plan, asset manifest, and quality report where the environment supports file output.
