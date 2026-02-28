import matplotlib.pyplot as plt
import json
import os
import numpy as np
import time  # Aggiunto per calcolare il tempo REALE
from modello_gurobi import risolvi_layout
from geometria import conta_incroci_totali

PERCORSO_BASE = os.path.dirname(os.path.abspath(__file__))
CARTELLA_DATI = os.path.join(PERCORSO_BASE, "dataset")

# --- CONFIGURAZIONE ---
TAGLIA = 20
SEEDS = [1, 2, 3] 

for s in SEEDS:
    nome_file = os.path.join(CARTELLA_DATI, f"instance_{TAGLIA}_s{s}.json")
    if not os.path.exists(nome_file): 
        print(f"File non trovato: {nome_file}")
        continue

    with open(nome_file, 'r') as f: 
        dati = json.load(f)

    print(f"\n--- Analisi Istanza N={TAGLIA} Seed={s} ---")
    
    # --- CALCOLO TEMPO TOTALE ---
    inizio_mesh = time.time()
    ris_mesh = risolvi_layout(dati, modalita="reduced", gap_ottimo=0.0)
    tempo_tot_mesh = time.time() - inizio_mesh

    inizio_full = time.time()
    ris_full = risolvi_layout(dati, modalita="full", gap_ottimo=0.0)
    tempo_tot_full = time.time() - inizio_full

    coords = np.array(ris_mesh["coords"])
    n_ss = ris_mesh["n_ss"]

    # --- SETUP VISUALIZZAZIONE ---
    
    fig, axs = plt.subplots(2, 2, figsize=(20, 14), constrained_layout=True)
    
    fig.suptitle(f"CONFRONTO MODELLI - {TAGLIA} TURBINE (Seed {s})", fontsize=22, fontweight='bold')
    
    def draw_links(ax, archi, color, lw, alpha=1.0, ls='-'):
        for a in archi:
            u, v = int(a[0]), int(a[1])
            ax.plot([coords[u,0], coords[v,0]], [coords[u,1], coords[v,1]], 
                    color=color, lw=lw, alpha=alpha, linestyle=ls, zorder=1)

    # 1. SPAZIO DI RICERCA: Mesh A+
    axs[0,0].set_title("1. SPAZIO DI RICERCA: Mesh A+\n(Delaunay + Diagonali)", fontsize=14, fontweight='bold')
    draw_links(axs[0,0], ris_mesh.get("archi_delaunay", []), 'gray', 0.8, 0.4)
    draw_links(axs[0,0], ris_mesh.get("archi_diagonali", []), 'green', 1.2, 0.6, '--')

    # 2. SPAZIO DI RICERCA: Grafo Completo
    axs[0,1].set_title("2. SPAZIO DI RICERCA: Grafo Completo\n(Tutte le connessioni possibili)", fontsize=14, fontweight='bold')
    draw_links(axs[0,1], ris_full.get("archi_full", []), 'gray', 0.6, 0.25)

    # 3. SOLUZIONE MESH A+ 
    inc_m = conta_incroci_totali(ris_mesh["archi"], coords)
    c_m = ris_mesh["costo"]
    # Font ridotto a 16 per dare più spazio al grafico e tutto su una riga se possibile
    axs[1,0].set_title(f"3. SOLUZIONE MESH A+\nCosto: {c_m:.2f} m | Tempo Totale: {tempo_tot_mesh:.3f} s | Incroci: {inc_m}", 
                       color='blue', fontsize=15, fontweight='bold')
    draw_links(axs[1,0], ris_mesh["archi"], 'blue', 2.5)

    # 4. SOLUZIONE FULL GRAPH
    inc_f = conta_incroci_totali(ris_full["archi"], coords)
    c_f = ris_full["costo"]
    axs[1,1].set_title(f"4. SOLUZIONE FULL GRAPH\nCosto: {c_f:.2f} m | Tempo Totale: {tempo_tot_full:.3f} s | Incroci: {inc_f}", 
                       color='red', fontsize=15, fontweight='bold')
    draw_links(axs[1,1], ris_full["archi"], 'red', 2.5)

    # Formattazione punti e griglia proporzionata
    for ax in axs.flat:
        ax.scatter(coords[n_ss:,0], coords[n_ss:,1], c='black', s=50, zorder=5, label='Turbine' if ax == axs[0,0] else "")
        ax.scatter(coords[:n_ss,0], coords[:n_ss,1], c='red', s=160, marker='s', zorder=5, label='Sottostazioni' if ax == axs[0,0] else "")
        ax.set_aspect('equal')
        ax.tick_params(axis='both', labelsize=11)
        ax.grid(True, ls=':', alpha=0.6)

    axs[0,0].legend(loc='best', fontsize=11)

    
    print(f"Mesh A+    -> Costo: {c_m:.2f} m | Tempo: {tempo_tot_mesh:.3f} s | Incroci: {inc_m}")
    print(f"Full Graph -> Costo: {c_f:.2f} m | Tempo: {tempo_tot_full:.3f} s | Incroci: {inc_f}")

    nome_img = os.path.join(PERCORSO_BASE, f"Confronto_N{TAGLIA}_S{s}_Completo.png")
    plt.savefig(nome_img, dpi=300)
    
    plt.show()