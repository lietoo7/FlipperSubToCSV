# FlipperSubToCSV
## Convertit un fichier .sub (Flipper Zero) en CSV compatible URH.
# Convert.py - Convertisseur Flipper Zero → URH
---

## Table des matières

1. [Installation](#installation)
2. [Utilisation du script](#utilisation-du-script)
3. [Importation dans URH](#importation-dans-urh)
4. [Exemples pratiques](#exemples-pratiques)
5. [Troubleshooting](#troubleshooting)

---

## Installation

### Prérequis

- **Python 3.6+**
- **Universal Radio Hacker (URH)** - [Installation](https://github.com/jopohl/urh)
- Un fichier `.sub` capturé avec votre Flipper Zero

### Installation rapide

#### 1. Sur Linux/Mac
```bash
# Installer URH
pip install urh

# Vérifier l'installation
urh --version
```

#### 2. Sur Windows
```bash
# Installer URH via pip
pip install urh

# Ou télécharger l'exécutable depuis :
# https://github.com/jopohl/urh/releases
```

#### 3. Récupérer le script
```bash
# Cloner ou télécharger le script
wget https://[votre-repo]/convert.py
# ou copier le fichier convert.py dans votre répertoire de travail
```

---

## Utilisation du script

### Syntaxe de base

```bash
python convert.py mon_signal.sub
```

### Avec options personnalisées

```bash
# Spécifier le nom du fichier de sortie
python convert.py mon_signal.sub -o mon_output.csv

# Ajuster la fréquence d'échantillonnage (défaut: 1MHz)
python convert.py mon_signal.sub -s 2000000

# Combiner les options
python convert.py mon_signal.sub -o custom.csv -s 2000000
```

### Options disponibles

| Option | Description | Défaut |
|--------|-------------|--------|
| `fichier` | Chemin du fichier `.sub` | Obligatoire |
| `-o, --output` | Nom du fichier CSV de sortie | `signaux_pour_urh.csv` |
| `-s, --sample-size` | Fréquence d'échantillonnage (Hz) | `1000000` (1 MHz) |
| `-h, --help` | Affiche l'aide | - |

### Exemples d'utilisation

```bash
# Conversion simple
python convert.py rfid_dump.sub

# Conversion avec sortie personnalisée
python convert.py sub_files/garage_door.sub -o garage_door_analysis.csv

# Conversion avec fréquence d'échantillonnage haute (pour plus de détails)
python convert.py infrared_signal.sub -s 5000000
```

### Résultat attendu

```
✓ 4527 impulsions trouvées
✓ Terminé ! Fichier généré : /path/to/signaux_pour_urh.csv
  → 2,345,600 points générés
```

---

## Importation dans URH

### Méthode 1 : Via l'interface graphique (recommandée)

#### Étape 1 : Lancer URH
```bash
urh
```

#### Étape 2 : Importer le CSV
1. Cliquer sur **File → Import Signal** (ou `Ctrl+I`)
2. Sélectionner votre fichier `signaux_pour_urh.csv`
3. Cliquer sur **Open**

#### Étape 3 : Configurer l'import
Une fenêtre de configuration apparaît. Les paramètres à vérifier :

| Paramètre | Valeur recommandée | Notes |
|-----------|-------------------|-------|
| **Sample Rate** | 1.0 MHz | Doit correspondre au `-s` du script |
| **Bits per Symbol** | 1 | Pour une onde carrée brute |
| **Columns** | `Time[s], Ch2` | Dépend de votre CSV |
| **Skip Rows** | 1 | Pour ignorer le header |

#### Étape 4 : Visualisation
- Le signal apparaît dans l'onglet **"Interpretation"**
- Utilisez la molette de la souris pour zoomer
- Double-cliquez pour sélectionner des portions du signal

### Méthode 2 : Import en ligne de commande

```bash
# Importer directement dans URH (mode headless)
urh --import signaux_pour_urh.csv --samplerate 1000000
```

### Méthode 3 : Drag & Drop

1. Lancer URH
2. Glisser-déposer le fichier `signaux_pour_urh.csv` dans la fenêtre URH
3. Configurer les paramètres comme décrit ci-dessus

---

## Analyse dans URH

Une fois le signal importé, vous pouvez :

### 1. **Analyser les modulations**
- Cliquer sur **"Demodulate"** pour tenter une démodulation automatique
- Choisir le type de modulation (OOK, FSK, ASK, etc.)

### 2. **Détecter les motifs**
- Utiliser l'onglet **"Analysis"** → **"Find Protocol Description"**
- URH propose des séquences répétées

### 3. **Extraire les données**
- Sélectionner une portion du signal
- Utiliser **"Copy"** pour exporter les symboles décodés
- Exporter en hexadécimal ou binaire

### 4. **Générer une attaque**
- Modifier les symboles détectés
- Cliquer **"Send"** pour rejouer le signal via SDR (USRP, HackRF, etc.)

---

## Exemples pratiques

### Exemple 1 : Analyser un signal RFID (Flipper Zero)

```bash
# 1. Convertir le signal capturé
python convert.py ./flipper_backups/125khz_rfid.sub -o rfid_signal.csv

# 2. Ouvrir dans URH
urh

# 3. Importer rfid_signal.csv
# File → Import Signal → rfid_signal.csv
# Configure Sample Rate: 125 kHz (125000)

# 4. Analyser
# Cliquer "Demodulate" → Choisir FSK ou OOK
# Extraire les données dans "Messages" tab
```

### Exemple 2 : Signal infrarouge (Flipper Zero)

```bash
# 1. Convertir (IR utilise généralement 38 kHz)
python convert.py ./flipper_backups/ir_remote.sub -o ir_signal.csv -s 38000

# 2. Importer dans URH avec Sample Rate: 38 kHz
# Analyser la structure des impulsions (PWM typique)
```

### Exemple 3 : Signal personnalisé avec haute résolution

```bash
# Capture à 5 MHz pour plus de détails
python convert.py signal_custom.sub -o signal_hires.csv -s 5000000

# Importer avec Sample Rate: 5.0 MHz
```

---

## Troubleshooting

### "Erreur : Fichier non trouvé"
```bash
# Vérifier le chemin du fichier
ls -la mon_signal.sub

# Utiliser le chemin absolu si nécessaire
python convert.py /full/path/to/mon_signal.sub
```

### "Erreur d'encodage UTF-8"
Le fichier `.sub` peut contenir des caractères spéciaux :
```python
# Modifier le script pour accepter un encodage différent
with open(input_path, 'r', encoding='latin-1') as f:  # ou 'cp1252'
```

### CSV vide ou fichier très volumineux
```bash
# Vérifier le nombre d'impulsions trouvées
# Si < 100 : Le format du fichier .sub peut être différent

# Pour très gros fichiers, utiliser l'optimisation de performance
# (voir la version améliorée du script)
```

### URH ne reconnaît pas le CSV
1. **Vérifier le format du CSV** :
   ```bash
   head -5 signaux_pour_urh.csv
   # Doit afficher :
   # Time[s],Ch2
   # 0.000000000001,1
   # ...
   ```

2. **Reconfigurer l'import** :
   - **File → Import Signal → Options**
   - Cocher "Skip header row"
   - Sélectionner les colonnes correctes

3. **Essayer un autre format** :
   - Exporter directement depuis Flipper Zero en `.wav` si possible
   - URH accepte aussi les fichiers audio

### Signal très petit ou très grand
- **Sample Rate trop bas** → Les détails sont perdus
  ```bash
  # Augmenter la sample rate
  python convert.py signal.sub -s 5000000
  ```

- **Sample Rate trop haut** → Fichier énorme (> 1 GB)
  ```bash
  # Diminuer la sample rate
  python convert.py signal.sub -s 500000
  ```

**Règle d'or** : Sample Rate ≥ 2× la fréquence de Nyquist du signal

---

## Ressources supplémentaires

- **URH Documentation** : https://urh.readthedocs.io/
- **Flipper Zero RF Documentation** : https://docs.flipper.zero/development/hardware/protocols
- **GNU Radio Documentation** : https://www.gnuradio.org/

---

## Notes de sécurité

**Légalité** : La transmission de signaux RF peut être réglementée dans votre pays.
- L'analyse (réception) est généralement autorisée
- La transmission (replay) peut nécessiter une autorisation
- L'interférence intentionnelle est **interdite** dans la plupart des juridictions

Consultez les régulations locales (ARCEP en France, FCC aux USA, etc.)

---

## Format du fichier CSV généré

Le fichier CSV contient deux colonnes :

```csv
Time[s],Ch2
0.000000000001,1
0.000000000002,1
0.000000000003,0
0.000000000004,0
...
```

- **Time[s]** : Temps écoulé en secondes (12 décimales de précision)
- **Ch2** : Valeur du signal (0 ou 1)
