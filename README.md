# SubGHz Flipper Zero Converter

Ce script Python est un outil de production optimisé permettant de convertir, analyser et visualiser les captures de signaux radio bruts (`.sub`) issues d'un **Flipper Zero**.

---

## Sommaire

* [Caractéristiques & Améliorations (V4)]()
* [Installation]() 
* [Prérequis]() 
* [Déploiement depuis Git]() 


* [Utilisation du Script]() 
* [Syntaxe de base]() 
* [Options disponibles]() 


* [Exemples Pratiques]()
* [1. Analyse statistique complète d'un signal]()
* [2. Export audio pour exploitation (Audacity, GQRX)]()
* [3. Export léger pour Universal Radio Hacker (URH)]()
* [4. Traitement total en une seule passe (Optimal)]()



---
## Installation

### Prérequis

Le cœur du script utilise uniquement la bibliothèque standard de Python 3 (`struct`, `wave`, `pathlib`, `argparse`).
La dépendance suivante est optionnelle et sert uniquement si vous souhaitez générer ou afficher des graphiques de l'onde :

* **Python 3.8+**
* **Matplotlib** (Optionnel)

### Déploiement depuis Git

1. Clonez le dépôt contenant le script :
```bash
git clone 

```


2. Accédez au dossier du projet :
```bash
cd flipper-sub-converter

```


3. (Optionnel) Installez la dépendance pour la visualisation graphique :
```bash
pip install matplotlib

```


4. Rendez le script exécutable (Linux/macOS) :
```bash
chmod +x flipper_sub_converter_v4.py

```



---

## Utilisation du Script

### Syntaxe de base

```bash
python3 flipper_sub_converter_v4.py -f <chemin_fichier.sub> [OPTIONS]

```

### Options disponibles

| Option | Description |
| --- | --- |
| `-f`, `--file` | **[Requis]** Chemin vers le fichier `.sub` extrait du Flipper Zero. |
| `--csv-transitions` | Génère un fichier CSV léger contenant uniquement les changements d'états (Idéal pour URH). |
| `--csv-urh` | Génère un fichier CSV complet ligne par ligne (Attention : fichier de sortie très lourd). |
| `--wav` | Exporte le signal sous forme de fichier audio WAV 16-bit PCM. |
| `--wav-rate` | Fréquence d'échantillonnage du fichier WAV (Défaut : `44100` Hz). |
| `--stats` | Calcule et affiche dans le terminal un rapport métrique complet du signal. |
| `--graph` | Affiche une fenêtre interactive contenant la visualisation de l'onde. |
| `--graph-save <nom.png>` | Sauvegarde le graphique de l'onde au format PNG sans ouvrir de fenêtre. |
| `--all` | Active toutes les options de traitement (CSV transitions, WAV, stats) en un seul passage. |
| `--sample-rate` | Ajuste la fréquence de capture d'origine (Défaut : `1000000` Hz / 1 MHz). |

---

## Exemples Pratiques

### 1. Analyse statistique complète d'un signal

Pour comprendre la structure d'une capture (identifier s'il s'agit d'un code fixe, d'un protocole connu, mesurer les durées des impulsions HIGH/LOW) sans générer de fichier sur votre disque :

```bash
python3 flipper_sub_converter_v4.py -f capture_portail.sub --stats

```

**Aperçu du retour :**

```text
=================================================================
                METRIQUES DU SIGNAL (STREAMING V4)
=================================================================
Impulsions Valides : 14205 (HIGH: 7102 | LOW: 7103)
Plage des Durées   : Min: 120 µs  |  Max: 1240 µs
Profil Temporel    : Moyenne: 432 µs | Écart-type: 12.4 µs
Durée Totale RF    : 6.1365 secondes
Débit Échantillon  : 2315 bps (~2.32 kbps)
-----------------------------------------------------------------
Top 10 des motifs récurrents :
  [01]   350 µs :  6840 occurrences ( 48.1%)
  [02]  1150 µs :  5210 occurrences ( 36.7%)
...

```

### 2. Export audio pour exploitation (Audacity, GQRX)

Générez un fichier audio haute fidélité échantillonné à 44.1 kHz pour écouter le signal ou l'analyser visuellement dans un éditeur audio :

```bash
python3 flipper_sub_converter_v4.py -f sonnette.sub --wav --wav-rate 44100

```

*Génère un fichier : `sonnette.wav`.*

### 3. Export ultra-léger pour Universal Radio Hacker (URH)

Si vous devez importer vos signaux Flipper dans URH pour faire de l'ingénierie inverse ou de la rétro-conception de protocole, l'option `--csv-transitions` est la plus adaptée car elle n'enregistre que les fronts montants/descendants, économisant des gigaoctets d'espace disque :

```bash
python3 flipper_sub_converter_v4.py -f alarme.sub --csv-transitions

```

*Génère un fichier : `alarme_transitions.csv` prêt à être importé via le menu "Import CSV" d'URH.*

### 4. Traitement total en une seule passe (Optimal)

Vous souhaitez générer le graphique, extraire le fichier audio, obtenir le CSV pour URH et afficher l'analyse statistique d'un coup, tout en protégeant les performances de votre ordinateur :

```bash
python3 flipper_sub_converter_v4.py -f telecommande.sub --all --graph-save vue_onde.png

```
