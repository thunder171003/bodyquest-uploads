# BodyQuest 3D render guards
- `patch_project.py <project>` – run right after new_video.sh: forces the 3D picture to finish drawing before each frame is saved, and redraws any frame that comes out with black blocks.
- `find_glitch_frames.py <video>` – lists half-drawn (black-block) frames; no output = clean.
- `repair_video.py <video> [<project>]` – re-renders (or, without a project, replaces with the nearest clean frame) every half-drawn frame and re-encodes in place; exit 0 = clean.
