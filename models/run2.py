import sys; sys.path.insert(0, '.')
import pams as P, impossible as I
for t in (11, 12):
    ok = [A for A in range(-300, 300) if all(P.check_simple(d + t, d, A) == 0 for d in (4, 5, 10, 11))]
    print(f'simple t={t}: exact top-bits offsets A in [-300, 300):', ok[:10], 'count', len(ok))
