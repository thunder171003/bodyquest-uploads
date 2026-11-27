"""Check a finished Short for half-drawn (black-block) frames and repair them.
Usage: python3 repair_video.py <video.mp4> [<project dir>]
With a project dir, each bad frame is re-rendered (capture.mjs frames, with the frame guard);
without one, or if a re-render is still bad, the nearest clean frame is used.
Rewrites the video in place only if something was repaired; prints a short report; exit 0 = clean now."""
import subprocess, sys, os, shutil, tempfile, pathlib, numpy as np
here = pathlib.Path(__file__).parent; video = pathlib.Path(sys.argv[1]).resolve()
proj = pathlib.Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
FPS = 24
def bad_frames(v):
    out = subprocess.run([sys.executable, str(here / 'find_glitch_frames.py'), str(v)], capture_output=True, text=True, check=True).stdout
    return [int(x) for x in out.split()]
def black(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-vf', 'scale=108:192:flags=neighbor', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True, check=True).stdout
    return (np.frombuffer(raw, np.uint8) <= 4).mean()
bad = bad_frames(video)
if not bad: print('CLEAN: no half-drawn frames'); sys.exit(0)
print('found', len(bad), 'half-drawn frames:', bad)
tmp = pathlib.Path(tempfile.mkdtemp(prefix='bqfix-')); fr = tmp / 'f'; fr.mkdir()
subprocess.run(['ffmpeg', '-v', 'error', '-i', str(video), '-q:v', '1', str(fr / '%05d.jpg')], check=True)
files = sorted(fr.iterdir()); n = len(files); badset = set(bad)
if proj:
    times = [i / FPS for i in bad]; out = tmp / 're'
    env = dict(os.environ, SOFTWARE_GL=os.environ.get('SOFTWARE_GL', '1'), QS=os.environ.get('QS', '&res=1&aa=4'))
    r = subprocess.run(['node', 'tools/capture.mjs', 'frames', str(out), ','.join(f'{t:.4f}' for t in times)], cwd=proj, env=env)
    for i, t in zip(bad, times):
        cand = out / f't{t:.2f}.jpg'
        nb = [files[j] for j in (i - 1, i + 1) if 0 <= j < n and j not in badset]
        ref = min((black(x) for x in nb), default=1)
        if cand.exists() and black(cand) <= ref + 0.02:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(cand), '-q:v', '1', str(files[i])], check=True); badset.discard(i)
for i in sorted(badset):   # fallback: copy the nearest clean frame
    for d in range(1, 30):
        j = next((k for k in (i - d, i + d) if 0 <= k < n and k not in badset), None)
        if j is not None: shutil.copy(files[j], files[i]); break
fixed = tmp / 'fixed.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', str(fr / '%05d.jpg'), '-i', str(video), '-map', '0:v', '-map', '1:a?',
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', str(fixed)], check=True)
left = bad_frames(fixed)
shutil.move(str(fixed), str(video)); shutil.rmtree(tmp, ignore_errors=True)
print('REPAIRED', len(bad), 'frames;', 'now CLEAN' if not left else f'still flagged: {left}')
sys.exit(0 if not left else 1)
