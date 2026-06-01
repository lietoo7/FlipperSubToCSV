import sys
import argparse
from pathlib import Path

def convert_sub_to_csv(input_file, output_file="signaux_pour_urh.csv", sample_size=1000000):
    """
    Convertit un fichier .sub (Flipper Zero) en CSV compatible URH.
    
    Args:
        input_file: Chemin du fichier .sub
        output_file: Nom du fichier CSV de sortie
        sample_size: Facteur de conversion (par défaut 1MHz = 1µs/sample)
    """
    try:
        # Vérification du fichier
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé : {input_file}")
        if not input_path.is_file():
            raise ValueError(f"Ce n'est pas un fichier : {input_file}")
        
        # Lecture avec context manager
        with open(input_path, 'r', encoding='utf-8') as f:
            data = f.read().splitlines()
        
        # Extraction des samples
        samples = []
        for line in data:
            if "RAW_Data" in line:
                try:
                    raw_part = line.split(': ')
                    if len(raw_part) < 2:
                        print(f"Ligne mal formatée ignorée : {line[:50]}")
                        continue
                    raw_values = raw_part[1].split()
                    samples.extend(raw_values)
                except Exception as e:
                    print(f"Erreur parsing ligne : {e}")
                    continue
        
        print(f"✓ {len(samples)} impulsions trouvées")
        
        # Génération de l'onde carrée
        values = []
        t = 0.0
        
        for s in samples:
            if not s.strip():
                continue
            try:
                duration = int(s)
                # Logique : durée négative = bit 0, durée positive = bit 1
                bit_val = 0 if duration < 0 else 1
                
                # Génération des points
                for _ in range(abs(duration)):
                    t += 1.0 / sample_size
                    values.append((t, bit_val))
                    
            except ValueError:
                print(f"Valeur non numérique ignorée : {s}")
                continue
        
        # Écriture CSV
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            f.write("Time[s],Ch2\n")  # Header sans espace
            for t_val, bit_val in values:
                f.write(f"{t_val:.12f},{bit_val}\n")
        
        print(f"✓ Terminé ! Fichier généré : {output_path.resolve()}")
        print(f"  → {len(values)} points générés")
        
    except FileNotFoundError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Erreur inattendue : {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convertir un fichier .sub (Flipper Zero) en CSV pour URH"
    )
    parser.add_argument("fichier", help="Fichier .sub à convertir")
    parser.add_argument(
        "-o", "--output",
        default="signaux_pour_urh.csv",
        help="Fichier CSV de sortie (défaut: signaux_pour_urh.csv)"
    )
    parser.add_argument(
        "-s", "--sample-size",
        type=int,
        default=1000000,
        help="Fréquence d'échantillonnage (défaut: 1000000)"
    )
    
    args = parser.parse_args()
    convert_sub_to_csv(args.fichier, args.output, args.sample_size)
