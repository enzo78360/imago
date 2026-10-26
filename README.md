# Imago

**Convertis et allège tes images sur Mac, en un geste.** Les photos d'iPhone en HEIC qu'aucun site n'accepte, les captures d'écran PNG de 6 Mo, les WebP téléchargés qu'on ne peut pas ouvrir… Imago les transforme en JPEG légers, à côté des originaux.

```
$ python3 imago.py ~/Desktop/Captures --max 2000
✓ IMG_0001.HEIC → IMG_0001.jpg  3,1 Mo → 890 Ko (-71 %)
✓ capture.png → capture.jpg  6,4 Mo → 412 Ko (-94 %)

2 images converties · 9,5 Mo → 1,3 Mo · 8,2 Mo gagnés
```

- **Entrées** : HEIC, PNG, WebP, TIFF, BMP, GIF, AVIF, RAW (DNG, CR2, NEF, ARW)… — tout ce que macOS sait lire.
- **Sorties** : JPEG (par défaut), PNG ou HEIC.
- **Redimensionnement** : `--max 2000` limite le plus grand côté, parfait pour un e-mail ou un formulaire en ligne.
- **Qualité réglable** : `--qualite 70` pour encore plus léger (82 par défaut).
- **Sans risque** : les originaux ne sont jamais modifiés, aucun fichier n'est écrasé, la date d'origine est conservée.
- **Rapide** : toutes les images sont traitées en parallèle.
- **App à glisser-déposer** : `--installer` crée une app *Imago* : dépose des images ou un dossier sur son icône (dans le Dock, par exemple) et une notification t'annonce le résultat.
- Aucune dépendance : utilise `sips`, l'outil d'images intégré à macOS.

## Utilisation

```bash
python3 imago.py IMG_0001.HEIC                    # → IMG_0001.jpg
python3 imago.py *.png --max 1600 --qualite 75
python3 imago.py ~/Desktop/Photos --sortie ~/Desktop/Web
python3 imago.py photo.jpg --format png
```

## L'app à glisser-déposer

```bash
python3 imago.py --installer
```

Crée `~/Applications/Imago.app`. Les options données avec `--installer` deviennent celles de l'app, par exemple :

```bash
python3 imago.py --installer --max 2000 --qualite 80
```

Garde le fichier `imago.py` au même endroit : l'app l'utilise.

## Licence

MIT
