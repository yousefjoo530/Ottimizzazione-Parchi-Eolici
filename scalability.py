import json
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from modello_gurobi import risolvi_layout
from geometria import conta_incroci_totali

# --- CONFIGURAZIONE PERCORSI ---
PERCORSO_BASE = os.path.dirname(os.path.abspath(__file__))
CARTELLA_DATI = os.path.join(PERCORSO_BASE, "dataset")
FILE_CSV = os.path.join(PERCORSO_BASE, "risultati_scalabilita.csv")

istanze_disponibili = []

# Scansione automatica del dataset
if os.path.exists(CARTELLA_DATI):
    for nome_file in os.listdir(CARTELLA_DATI):
        if nome_file.startswith("instance_") and nome_file.endswith(".json"):
            parti = nome_file.replace(".json", "").split("_")
            try:
                n = int(parti[1])
                s = int(parti[2].replace("s", ""))
                istanze_disponibili.append((n, s, os.path.join(CARTELLA_DATI, nome_file)))
            except:
                pass

# Ordinamento per taglia N e seed S
istanze_disponibili.sort(key=lambda x: (x[0], x[1]))
risultati = []

# Intestazione Tabella (Allineamento fisso per evitare sovrapposizioni)
print("\n" + "="*105)
print(f"{'N':<5} | {'S':<3} | {'T_Mesh(s)':^12} | {'T_Full(s)':^12} | {'Obj_Mesh':^12} | {'Obj_Full':^12} | {'Inc_M':^5} | {'Inc_F':^5}")
print("="*105)

for n, s, percorso in istanze_disponibili:
    
    with open(percorso, 'r') as f: 
        dati = json.load(f)
        
    # --- TRUCCO PER IL MESSAGGIO DI CARICAMENTO ---
    # Il comando end='\r' fa sì che la riga successiva sovrascriva questa.
    # I molti spazi vuoti alla fine servono a "pulire" lo schermo da vecchi caratteri.
    print(f"{n:<5} | {s:<3} | ⏳ Calcolo in corso...{' '*50}", end='\r', flush=True)
    
    try:
        # 1. RISOLUZIONE MESH A+ (Modalità Ridotta)
        r_m = risolvi_layout(dati, modalita="reduced", limite_tempo=300, gap_ottimo=0.02)
        i_m = conta_incroci_totali(r_m["archi"], r_m["coords"])
        
        # 2. RISOLUZIONE FULL GRAPH (Modalità Completa)
        t_f_val, obj_f_val = np.nan, np.nan
        i_f_val, t_f_str, obj_f_str = "---", "TIMEOUT", "---"
        
        try:
            r_f = risolvi_layout(dati, modalita="full", limite_tempo=300, gap_ottimo=0.02)
            
            # Se risolto entro il limite di tempo
            if r_f["tempo"] < 299 and len(r_f["archi"]) > 0:
                i_f_val = conta_incroci_totali(r_f["archi"], r_f["coords"])
                t_f_val, obj_f_val = r_f["tempo"], r_f["costo"]
                t_f_str = f"{t_f_val:>12.2f}"
                obj_f_str = f"{obj_f_val:>12.2f}"
        except:
            pass
            
        # Stampa riga dei risultati (Questa riga cancella il "Calcolo in corso" e fissa i dati)
        print(f"{n:<5} | {s:<3} | {r_m['tempo']:>12.2f} | {t_f_str:>12} | {r_m['costo']:>12.2f} | {obj_f_str:>12} | {i_m:^5} | {i_f_val:^5}")
        
        # Salvataggio dati per i grafici
        risultati.append({
            "N": n, "S": s, 
            "T_M": r_m['tempo'], "T_F": t_f_val, 
            "Obj_Mesh": r_m['costo'], "Obj_Full": obj_f_val,
            "I_M": i_m, "I_F": (i_f_val if isinstance(i_f_val, int) else np.nan)
        })

    except Exception as e:
        # In caso di errore, puliamo la riga e mostriamo l'errore
        print(f"Errore istanza N={n}, S={s}: {e}{' '*50}")
        continue

# --- GENERAZIONE REPORT FINALE E GRAFICI ---
if risultati:
    df = pd.DataFrame(risultati)
    df.to_csv(FILE_CSV, index=False)

    # Calcolo medie per il plotting
    df_medie = df.groupby('N').mean(numeric_only=True).reset_index()
    df_full_valido = df_medie.dropna(subset=['T_F'])

    # 1. Grafico Tempi
    plt.figure(figsize=(10, 6))
    plt.plot(df_medie['N'], df_medie['T_M'], marker='o', label='Mesh A+')
    plt.plot(df_full_valido['N'], df_full_valido['T_F'], marker='x', label='Full Graph', ls='--')
    plt.yscale('log')
    plt.title('Scalabilità: Tempo di Esecuzione')
    plt.xlabel('Numero Turbine (N)')
    plt.ylabel('Secondi (Log)')
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.legend()
    plt.savefig(os.path.join(PERCORSO_BASE, "scalabilita_tempi.png"))

    # 2. Grafico Costi
    plt.figure(figsize=(10, 6))
    plt.plot(df_medie['N'], df_medie['Obj_Mesh'], marker='o', label='Mesh A+')
    plt.plot(df_full_valido['N'], df_full_valido['Obj_Full'], marker='x', label='Full Graph', ls='--')
    plt.title('Qualità: Costo Totale Cavi Mesh A+ Vs Full')
    plt.xlabel('Numero Turbine (N)')
    plt.ylabel('Metri')
    plt.grid(True, ls="--", alpha=0.5)
    plt.legend()
    plt.savefig(os.path.join(PERCORSO_BASE, "scalabilita_costi.png"))

    print(f"\n✅ Analisi completata. CSV salvato in: {FILE_CSV}")
    
    plt.show()