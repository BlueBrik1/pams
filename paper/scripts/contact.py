#!/usr/bin/env python3
"""Contact sheets (3x3 pages per image) of the rendered pages in paper/_preview/p-*.png, for layout inspection."""
import glob, sys
from PIL import Image, ImageDraw
files = sorted(glob.glob('_preview/p-*.png'))
per = 9
for s in range(0, len(files), per):
    ims = [Image.open(f) for f in files[s:s + per]]
    w, h = ims[0].size; W = 3 * w + 20; H = 3 * h + 20
    sheet = Image.new('RGB', (W, H), 'gray')
    for k, im in enumerate(ims):
        x, y = (k % 3) * (w + 10), (k // 3) * (h + 10)
        sheet.paste(im, (x, y)); ImageDraw.Draw(sheet).text((x + 5, y + 5), str(s + k + 1), fill='red')
    sheet.save(f'_preview/sheet_{s // per + 1}.png'); print(f'_preview/sheet_{s // per + 1}.png', files[s], '..', files[min(s + per, len(files)) - 1])
