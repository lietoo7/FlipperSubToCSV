#!/usr/bin/env python3
"""
Convertisseur SubGHz Flipper Zero vers CSV
"""

import sys
import struct
import wave
import argparse
from pathlib import Path
from typing import Iterator, Tuple, Dict, Any, Optional

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class SubGhzPipelineV4:
    """
    Framework de conversion de signal radio par flux à passe unique.
    Garantit une consommation RAM < 5 Mo et des accès I/O optimisés.
    """
    FLIPPER_TIMEOUT_THRESHOLD = 5000

    def __init__(self, filename: str, sample_rate: int = 1_000_000):
        self.filename = Path(filename)
        self.sample_rate = sample_rate
        
        if not self.filename.exists():
            raise FileNotFoundError(f"Fichier introuvable : {self.filename}")

    def _stream_raw_timings(self) -> Iterator[int]:
        """lit le fichier ligne par ligne."""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                for line in f:
                    if "RAW_Data:" not in line:
                        continue
                    
                    data_part = line.split("RAW_Data:")[1].strip().rstrip('.')
                    for x in data_part.split():
                        if x:
                            try:
                                yield int(x)
                            except ValueError:
                                continue
        except Exception as e:
            raise IOError(f"Erreur d'accès au fichier source : {e}")

    def execute_pipeline(self, 
                         do_urh: bool = False, 
                         do_trans: bool = False, 
                         do_wav: bool = False, 
                         do_stats: bool = False,
                         wav_sample_rate: int = 44100,
                         max_graph_points: Optional[int] = None) -> Dict[str, Any]:
        """
        Parcourt le fichier une seule fois et alimente
        simultanément tous les exports et calculs statistiques activés.
        """
        # --- INITIALISATION DES DESCRIPTEURS ET BUFFERS ---
        f_urh = f_trans = wav_file = None
        wav_buffer = bytearray()
        WAV_CHUNK_SIZE = 65536
        
        stem = self.filename.stem
        out_files = {}

        # Initialisation Stats (Welford)
        stat_count = high_count = low_count = total_us = 0
        min_dur, max_dur = float('inf'), float('-inf')
        mean = M2 = 0.0
        top_counter: Dict[int, int] = {}

        # Initialisation Graphique
        graph_stream = []

        try:
            # Ouverture conditionnelle des fichiers de sortie
            if do_urh:
                out_files['urh'] = f"{stem}_urh.csv"
                f_urh = open(out_files['urh'], 'w', encoding='utf-8', newline='')
                f_urh.write("Time[s],Ch2\n")

            if do_trans:
                out_files['trans'] = f"{stem}_transitions.csv"
                f_trans = open(out_files['trans'], 'w', encoding='utf-8', newline='')
                f_trans.write("Time[s],Ch2\n")
                f_trans.write("0.000000,0\n")

            if do_wav:
                out_files['wav'] = f"{stem}.wav"
                wav_file = wave.open(out_files['wav'], 'wb')
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(wav_sample_rate)

            # Variables de synchronisation temporelle
            current_sample_idx = 0
            exact_wav_samples_total = 0.0
            wav_samples_written = 0

            # --- PARCOURS UNIQUE DU FLUX ---
            for timing in self._stream_raw_timings():
                if timing <= -self.FLIPPER_TIMEOUT_THRESHOLD:
                    continue

                abs_timing = abs(timing)
                bit_val = 1 if timing >= 0 else 0

                # 1. Pipeline STATISTIQUES (Streaming Welford pur)
                if do_stats:
                    stat_count += 1
                    total_us += abs_timing
                    if timing >= 0: high_count += 1
                    else: low_count += 1
                    
                    if abs_timing < min_dur: min_dur = abs_timing
                    if abs_timing > max_dur: max_dur = abs_timing
                    
                    top_counter[abs_timing] = top_counter.get(abs_timing, 0) + 1
                    
                    # Formule de Welford
                    delta = abs_timing - mean
                    mean += delta / stat_count
                    M2 += delta * (abs_timing - mean)

                # 2. Pipeline GRAPHIQUE (Échantillonnage adaptatif en amont)
                if max_graph_points and len(graph_stream) < max_graph_points:
                    remaining = max_graph_points - len(graph_stream)
                    graph_stream.extend([bit_val] * min(abs_timing, remaining))

                # 3. Pipeline CSV TRANSITIONS
                if do_trans:
                    t_val = current_sample_idx / self.sample_rate
                    f_trans.write(f"{t_val:.6f},{bit_val}\n")

                # 4. Pipeline CSV URH / WAV (Nécessitent le déploiement par échantillon)
                if do_urh or do_wav:
                    # Traitement URH
                    if do_urh:
                        for s_offset in range(abs_timing):
                            t_val = (current_sample_idx + s_offset) / self.sample_rate
                            f_urh.write(f"{t_val:.6f},{bit_val}\n")

                    # Traitement WAV (Calcul d'arrondi anti-dérive)
                    if do_wav:
                        amplitude = 32767 if bit_val == 1 else -32768
                        raw_bytes = struct.pack('<h', amplitude)
                        
                        exact_wav_samples_total += abs_timing * wav_sample_rate / self.sample_rate
                        num_samples = int(round(exact_wav_samples_total)) - wav_samples_written
                        
                        for _ in range(num_samples):
                            wav_buffer.extend(raw_bytes)
                            wav_samples_written += 1
                            
                            if len(wav_buffer) >= WAV_CHUNK_SIZE:
                                wav_file.writeframes(wav_buffer)
                                wav_buffer.clear()

                # Avancement de l'index de temps de référence (1 MHz)
                current_sample_idx += abs_timing

            # --- NETTOYAGE & FERMETURE DES FLUX ---
            if f_urh: f_urh.close()
            if f_trans: f_trans.close()
            if wav_file:
                if wav_buffer:
                    wav_file.writeframes(wav_buffer)
                wav_file.close()

        except Exception as e:
            # Sécurité : Fermeture des descripteurs en cas de crash en cours de route
            for f in [f_urh, f_trans]:
                if f and not f.closed: f.close()
            if wav_file: wav_file.close()
            raise e

        # --- MISE EN FORME DES RÉSULTATS ---
        pipeline_results = {'files': out_files, 'graph_data': graph_stream}

        if do_stats and stat_count > 0:
            variance = M2 / stat_count if stat_count > 1 else 0.0
            total_s = total_us / 1_000_000
            pipeline_results['stats'] = {
                'total_impulsions': stat_count,
                'high_count': high_count,
                'low_count': low_count,
                'min_duration': min_dur,
                'max_duration': max_dur,
                'avg_duration': int(mean),
                'stdev_duration': variance ** 0.5,
                'total_s': total_s,
                'bitrate_bps': stat_count / total_s if total_s > 0 else 0,
                'top_durations': sorted(top_counter.items(), key=lambda x: x[1], reverse=True)[:10]
            }

        return pipeline_results

    def generate_graph(self, stream_data: list, output_file: str = None) -> None:
        """Génère le graphique de l'onde à partir des données extraites du pipeline."""
        if not HAS_MATPLOTLIB:
            print("⚠ matplotlib non disponible. Graphique sauté.")
            return
        if not stream_data:
            return

        fig, ax = plt.subplots(figsize=(16, 5))
        ax.plot(stream_data, linewidth=0.5, color='#1f77b4')
        ax.set_xlabel('Microsecondes (échantillons)')
        ax.set_ylabel('État (0/1)')
        ax.set_title(f'Visualisation Onde - {self.filename.name} ({len(stream_data):,} points)')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-0.5, 1.5)
        
        if output_file:
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            print(f"✓ Graphique sauvegardé : {output_file}")
        else:
            plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Convertisseur SubGHz V4 (Framework Passe-Unique & Streaming Rapproché)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-f', '--file', required=True, help='Fichier .sub source')
    parser.add_argument('--csv-urh', action='store_true', help='Générer le CSV complet (Volumineux)')
    parser.add_argument('--csv-transitions', action='store_true', help='Générer le CSV de transitions (Optimisé)')
    parser.add_argument('--wav', action='store_true', help='Générer le fichier Audio WAV')
    parser.add_argument('--wav-rate', type=int, default=44100, help='Taux WAV (Défaut: 44100 Hz)')
    parser.add_argument('--graph', action='store_true', help='Afficher le graphique')
    parser.add_argument('--graph-save', help='Sauvegarder le graphique en PNG')
    parser.add_argument('--stats', action='store_true', help='Calculer les statistiques globales')
    parser.add_argument('--all', action='store_true', help='Exécuter toutes les actions en une passe')
    parser.add_argument('--sample-rate', type=int, default=1_000_000, help='Fréquence de capture de base')

    args = parser.parse_args()

    do_urh = args.csv_urh or args.all
    do_trans = args.csv_transitions or args.all
    do_wav = args.wav or args.all
    do_stats = args.stats or args.all
    do_graph = args.graph or args.graph_save or args.all

    if not any([do_urh, do_trans, do_wav, do_stats, do_graph]):
        print("ℹ Aucune action demandée. Utilisez --help pour voir les options.")
        return

    try:
        print(f"📂 Ouverture du flux : {args.file}")
        pipeline = SubGhzPipelineV4(args.file, sample_rate=args.sample_rate)
        
        # Configuration de la limite graphique pour ne pas saturer la mémoire graphique
        max_g_points = 50000 if do_graph else None

        # Lancement de la passe unique
        res = pipeline.execute_pipeline(
            do_urh=do_urh, do_trans=do_trans, do_wav=do_wav, do_stats=do_stats,
            wav_sample_rate=args.wav_rate, max_graph_points=max_g_points
        )

        # Affichage des confirmations de création de fichiers
        for k, filepath in res['files'].items():
            size = Path(filepath).stat().st_size / 1024
            unit = "KB" if size < 1024 else "MB"
            display_size = size if size < 1024 else size / 1024
            print(f"   ↳ Fichier écrit : {filepath} ({display_size:.2f} {unit})")

        # Rendu graphique
        if do_graph:
            pipeline.generate_graph(res['graph_data'], output_file=args.graph_save)

        # Rendu des statistiques de Welford
        if do_stats and 'stats' in res:
            s = res['stats']
            print("\n" + "="*65)
            print("METRIQUES DU SIGNAL")
            print("="*65)
            print(f"Impulsions Valides : {s['total_impulsions']} (HIGH: {s['high_count']} | LOW: {s['low_count']})")
            print(f"Plage des Durées   : Min: {s['min_duration']} µs  |  Max: {s['max_duration']} µs")
            print(f"Profil Temporel    : Moyenne: {s['avg_duration']} µs | Écart-type: {s['stdev_duration']:.1f} µs")
            print(f"Durée Totale RF    : {s['total_s']:.4f} secondes")
            print(f"Débit Échantillon  : {s['bitrate_bps']:.0f} bps (~{s['bitrate_bps']/1000:.2f} kbps)")
            print("-"*65 + "\nTop 10 des motifs récurrents :")
            for i, (dur, cnt) in enumerate(s['top_durations'], 1):
                print(f"  [{i:02d}] {dur:5d} µs : {cnt:5d} occurrences ({100 * cnt / s['total_impulsions']:5.1f}%)")
            print("="*65)

        print("\n✓ Traitement multi-flux terminé avec succès !")

    except Exception as e:
        print(f"[!] Échec critique du pipeline : {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
