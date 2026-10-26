#!/usr/bin/env python3
"""Imago : convertit et allège tes images (HEIC, PNG, WebP, TIFF… → JPEG) en un geste.

Usage :
  python3 imago.py IMG_0001.HEIC capture.png        convertit en JPEG à côté des originaux
  python3 imago.py ~/Desktop/Photos --max 2000      réduit tout un dossier à 2000 px maximum
  python3 imago.py photo.jpg --format png
  python3 imago.py --installer                      crée l'app « Imago » : glisse des images dessus

Utilise « sips », l'outil d'images intégré à macOS : aucune dépendance.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

INPUT_EXT = {'heic', 'heif', 'png', 'jpg', 'jpeg', 'webp', 'tif', 'tiff', 'bmp', 'gif', 'avif', 'dng', 'cr2', 'nef', 'arw'}
FORMATS = {'jpeg': 'jpg', 'png': 'png', 'heic': 'heic'}

TTY = sys.stdout.isatty()
def color(code, s): return '\033[%sm%s\033[0m' % (code, s) if TTY else s
dim = lambda s: color('2', s)
green = lambda s: color('32', s)
red = lambda s: color('31', s)


def fmt(n):
    for unit in ('o', 'Ko', 'Mo', 'Go'):
        if n < 1000 or unit == 'Go':
            return ('%.1f %s' % (n, unit) if unit != 'o' and n < 10 else '%d %s' % (n, unit)).replace('.', ',')
        n /= 1000


def collect(paths):
    """Fichiers images donnés directement ou contenus dans les dossiers donnés."""
    found = []
    for p in paths:
        p = os.path.expanduser(p)
        if os.path.isdir(p):
            for name in sorted(os.listdir(p)):
                full = os.path.join(p, name)
                if os.path.isfile(full) and not name.startswith('.') and ext_of(name) in INPUT_EXT:
                    found.append(full)
        elif os.path.isfile(p):
            found.append(p)
        else:
            print(red('Introuvable : %s' % p), file=sys.stderr)
    return found


def ext_of(name):
    return os.path.splitext(name)[1][1:].lower()


def free_name(path):
    base, ext = os.path.splitext(path)
    candidate, n = path, 2
    while os.path.exists(candidate):
        candidate = '%s (%d)%s' % (base, n, ext)
        n += 1
    return candidate


def convert(src, fmt_name, quality, max_px, out_dir):
    ext = FORMATS[fmt_name]
    folder = out_dir or os.path.dirname(src)
    stem = os.path.splitext(os.path.basename(src))[0]
    dst = os.path.join(folder, stem + '.' + ext)
    if os.path.abspath(dst) == os.path.abspath(src) or os.path.exists(dst):
        dst = free_name(os.path.join(folder, stem + ' (Imago).' + ext))

    cmd = ['sips', '-s', 'format', fmt_name]
    if fmt_name in ('jpeg', 'heic'):
        cmd += ['-s', 'formatOptions', str(quality)]
    if max_px:
        cmd += ['-Z', str(max_px)]
    # Conversion dans un fichier temporaire : un échec ne laisse jamais de fichier à moitié écrit.
    fd, tmp = tempfile.mkstemp(suffix='.' + ext, dir=folder)
    os.close(fd)
    r = subprocess.run(cmd + [src, '--out', tmp], capture_output=True, text=True)
    if r.returncode != 0 or os.path.getsize(tmp) == 0:
        os.remove(tmp)
        return src, None, 'fichier illisible ou format non pris en charge'
    os.replace(tmp, dst)
    shutil.copystat(src, dst)  # garde la date de l'original
    return src, dst, None


def run(paths, fmt_name, quality, max_px, out_dir, notify):
    files = collect(paths)
    if not files:
        sys.exit('Aucune image à convertir.')
    if out_dir:
        out_dir = os.path.expanduser(out_dir)
        os.makedirs(out_dir, exist_ok=True)

    before = after = ok = 0
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        jobs = [pool.submit(convert, f, fmt_name, quality, max_px, out_dir) for f in files]
        for job in jobs:
            src, dst, err = job.result()
            name = os.path.basename(src)
            if err:
                print(red('✗ %s : %s' % (name, err)))
                continue
            a, b = os.path.getsize(src), os.path.getsize(dst)
            before += a
            after += b
            ok += 1
            gain = (1 - b / a) * 100 if a else 0
            print('%s %s → %s  %s' % (green('✓'), name, os.path.basename(dst),
                                      dim('%s → %s (%+d %%)' % (fmt(a), fmt(b), -gain))))

    if ok:
        saved = before - after
        summary = '%d image%s convertie%s · %s → %s' % (ok, 's' if ok > 1 else '', 's' if ok > 1 else '', fmt(before), fmt(after))
        if saved > 0:
            summary += ' · %s gagnés' % fmt(saved)
        print('\n' + green(summary))
        if notify:
            note = summary.replace('"', "'")
            subprocess.run(['osascript', '-e', 'display notification "%s" with title "Imago"' % note])


DROPLET = '''
on open droppedItems
  set args to ""
  repeat with f in droppedItems
    set args to args & " " & quoted form of POSIX path of f
  end repeat
  do shell script "%s %s --notifier %s" & args
end open

on run
  display dialog "Glisse des images (ou un dossier) sur l'icône d'Imago pour les convertir en JPEG." buttons {"OK"} default button 1 with title "Imago"
end run
'''


def install(extra):
    apps = os.path.expanduser('~/Applications')
    os.makedirs(apps, exist_ok=True)
    target = os.path.join(apps, 'Imago.app')
    script = DROPLET % (quote(sys.executable), quote(os.path.abspath(__file__)), ' '.join(quote(a) for a in extra))
    with tempfile.NamedTemporaryFile('w', suffix='.applescript', delete=False, encoding='utf-8') as f:
        f.write(script)
    if os.path.exists(target):
        shutil.rmtree(target)
    subprocess.run(['osacompile', '-o', target, f.name], check=True)
    os.remove(f.name)
    print(green('✓ App créée : %s' % target))
    print(dim('  Glisse-la dans le Dock, puis dépose des images dessus pour les convertir.'))
    subprocess.run(['open', '-R', target])


def quote(s):
    return "'" + s.replace("'", "'\\''") + "'"


def main():
    ap = argparse.ArgumentParser(description='Convertit et allège des images avec les outils intégrés à macOS.')
    ap.add_argument('images', nargs='*', help='images ou dossiers à convertir')
    ap.add_argument('--format', choices=sorted(FORMATS), default='jpeg', help='format de sortie (par défaut : jpeg)')
    ap.add_argument('--qualite', type=int, default=82, help='qualité JPEG/HEIC de 1 à 100 (par défaut : 82)')
    ap.add_argument('--max', type=int, help='taille maximale du plus grand côté, en pixels')
    ap.add_argument('--sortie', help='dossier de destination (par défaut : à côté des originaux)')
    ap.add_argument('--installer', action='store_true', help="créer l'app « Imago » où déposer des images")
    ap.add_argument('--notifier', action='store_true', help=argparse.SUPPRESS)
    args = ap.parse_args()

    if not 1 <= args.qualite <= 100:
        ap.error('la qualité doit être comprise entre 1 et 100')
    if args.installer:
        # Les réglages donnés avec --installer deviennent ceux de l'app.
        extra = ['--format', args.format, '--qualite', str(args.qualite)]
        if args.max:
            extra += ['--max', str(args.max)]
        return install(extra)
    if not args.images:
        ap.print_help()
        return
    run(args.images, args.format, args.qualite, args.max, args.sortie, args.notifier)


if __name__ == '__main__':
    main()
