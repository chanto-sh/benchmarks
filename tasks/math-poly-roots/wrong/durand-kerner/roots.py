"""Real roots via Durand-Kerner on all complex roots, keeping the real ones."""


def evaluate(coeffs, x):
    y = 0
    for c in coeffs:
        y = y * x + c
    return y


def real_roots(coeffs, lo, hi):
    while coeffs and coeffs[0] == 0:
        coeffs = coeffs[1:]
    n = len(coeffs) - 1
    if n < 1:
        return []
    a = [c / coeffs[0] for c in coeffs]
    z = [complex(0.4, 0.9) ** k for k in range(n)]
    for _ in range(2000):
        new = []
        for i, zi in enumerate(z):
            den = 1
            for j, zj in enumerate(z):
                if i != j:
                    den *= zi - zj
            if den == 0:
                den = 1e-12
            new.append(zi - evaluate(a, zi) / den)
        z = new
    out = []
    for r in sorted(w.real for w in z if abs(w.imag) < 1e-6):
        if float(lo) - 1e-9 <= r <= float(hi) + 1e-9 and not any(abs(r - o) < 1e-6 for o in out):
            out.append(min(max(r, float(lo)), float(hi)))
    return out
