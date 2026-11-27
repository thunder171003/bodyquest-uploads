"""Find half-drawn frames: a block of pure black that appears for 1-3 frames and then
disappears again (the picture comes back in the same place). Real dark shots or cuts to a
dark scene last longer, so they are not flagged. Prints one frame index per line.
Usage: python3 find_glitch_frames.py video.mp4 [--verbose]"""
import subprocess, sys, numpy as np
f = sys.argv[1]; verbose = '--verbose' in sys.argv
W, H = 108, 192; WIN = 3; MIN = 0.04          # look 3 frames each way; block >= 4% of the picture
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-vf', f'scale={W}:{H}:flags=neighbor',
                      '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True, check=True).stdout
blk = np.frombuffer(raw, np.uint8).reshape(-1, H, W) <= 4
n = len(blk); bad = []
for i in range(8, n - 12):                      # skip the designed fade-in / fade-out
    m = blk[i]
    if m.mean() < MIN: continue
    best = None
    for j in range(i - WIN, i):                 # pixels black now but visible shortly before
        new = m & ~blk[j]
        if best is None or new.sum() > best.sum(): best = new
    if best.mean() < MIN: continue
    back = max((best & ~blk[j]).mean() for j in range(i + 1, min(n, i + WIN + 1)))
    if back >= MIN: bad.append(i)               # ...and visible again shortly after = glitch
if verbose: print(f, n, 'frames; glitch frames:', len(bad), file=sys.stderr)
for i in bad: print(i)
