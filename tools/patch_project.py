"""Patch a faceless-shorts Deep Dive 3D project so frames can't be saved half-drawn.
1) blit(): gl.finish() before copying the 3D canvas, so the software renderer has finished every tile.
2) OP.frame(): if a frame suddenly has a lot more pure-black pixels than the previous frame,
   redraw it (up to 4 tries) and keep the most complete version.
Usage: python3 patch_project.py <project dir>   (safe to run twice)"""
import sys, pathlib
m = pathlib.Path(sys.argv[1]) / 'src' / 'main.js'; s = m.read_text()
if 'BQ_FRAME_GUARD' in s: print('already patched'); sys.exit(0)
old_blit = "const blit = () => ctx.drawImage(GL, 0, 0, W, H);"
new_blit = "const blit = () => { const g = GL.getContext('webgl2') || GL.getContext('webgl'); if (g) g.finish(); ctx.drawImage(GL, 0, 0, W, H); }; // BQ_FRAME_GUARD"
old_frame = "OP.frame = (t, q = 0.92) => { draw(t); return cv.toDataURL('image/jpeg', q); };"
new_frame = """OP.blackShare = () => { const d = ctx.getImageData(0, 0, W, H).data; let b = 0, n = 0; for (let i = 0; i < d.length; i += 4 * 61) { n++; if (d[i] <= 4 && d[i + 1] <= 4 && d[i + 2] <= 4) b++; } return b / n; };
    OP.frame = (t, q = 0.92) => { // BQ_FRAME_GUARD: redraw frames that come out with missing (black) tiles
      let best = null, bestS = 2;
      for (let k = 0; k < 4; k++) {
        draw(t); const s = OP.blackShare();
        if (s < bestS) { bestS = s; best = cv.toDataURL('image/jpeg', q); }
        if (OP._prevBlack === undefined || s <= OP._prevBlack + 0.03) break;
      }
      OP._prevBlack = bestS; return best;
    };"""
assert old_blit in s and old_frame in s, 'main.js changed: patch by hand'
m.write_text(s.replace(old_blit, new_blit).replace(old_frame, new_frame)); print('patched', m)
