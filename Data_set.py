import numpy as np
from sklearn.cluster import KMeans
import json
import os

# --- CONFIGURAZIONE PERCORSI ---
# Identifico la cartella di lavoro per salvare i file 
PERCORSO_BASE = os.path.dirname(os.path.abspath(__file__))
CARTELLA_DATASET = os.path.join(PERCORSO_BASE, "dataset")

# Parametri per la scalabilità (da 20 a 1000 turbine)
TAGLIE_TEST = [20, 50, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000]
SEEDS_CASUALI = [1, 2, 3] 
DISTANZA_MINIMA = 400  # Distanza minima tra turbine per evitare sovrapposizioni reali

def genera_mappa_turbine(n_turbine, dist_min, seed_corrente):
    """
    Genera le coordinate delle turbine in un'area quadrata proporzionale al numero di turbine.
    
    """
    lato_campo = int(np.sqrt(n_turbine) * 1000)
    coordinate = []
    generatore_random = np.random.default_rng(seed_corrente + n_turbine) 
    tentativi = 0
    max_tentativi = n_turbine * 5000 
    
    while len(coordinate) < n_turbine and tentativi < max_tentativi:
        nuova_pos = generatore_random.random(2) * lato_campo
        
        if not coordinate:
            coordinate.append(nuova_pos)
        else:
            # Calcolo distanza dalle turbine già posizionate
            distanze = np.linalg.norm(np.array(coordinate) - nuova_pos, axis=1)
            if np.all(distanze >= dist_min):
                coordinate.append(nuova_pos)
        tentativi += 1
        
    return np.array(coordinate), lato_campo

# Controllo se esiste la cartella, altrimenti la creo
if not os.path.exists(CARTELLA_DATASET):
    os.makedirs(CARTELLA_DATASET)

print(f"--- AVVIO GENERAZIONE DEL DATASET  ---")

for n in TAGLIE_TEST:
    for s in SEEDS_CASUALI:
        # 1. Generazione delle turbine
        coordinate_turbine, lato = genera_mappa_turbine(n, DISTANZA_MINIMA, s)
        
        # 2. Posizionamento delle sottostazioni tramite Clustering (K-Means)
        # Decido il numero di sottostazioni per ogni 10 turbine (minimo 2)
        n_sottostazioni = max(2, int(n / 10))
        clusterizzatore = KMeans(n_clusters=n_sottostazioni, n_init=10, random_state=1)
        clusterizzatore.fit(coordinate_turbine)
        
        # 3. Organizzazione dei dati 
        dati_istanza = {
            "id": f"istanza_{n}_s{s}", 
            "n_turbines": n, 
            "n_ss": n_sottostazioni, 
            "seed": s,
            "turbines": coordinate_turbine.tolist(), 
            "substations": clusterizzatore.cluster_centers_.tolist(),
            "labels": clusterizzatore.labels_.tolist()
        }
        
        # 4. Salvataggio in formato JSON
        nome_file = os.path.join(CARTELLA_DATASET, f"instance_{n}_s{s}.json")
        with open(nome_file, 'w') as f:
            json.dump(dati_istanza, f, indent=4)

print(f"Generazione completata. Tutti i file si trovano in: {CARTELLA_DATASET}")