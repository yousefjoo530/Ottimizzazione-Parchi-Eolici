import numpy as np
import gurobipy as gp
from gurobipy import GRB
from scipy.spatial import Delaunay
import time
from geometria import verifica_incrocio

def risolvi_layout(dati, modalita="reduced", limite_tempo=300, gap_ottimo=0.02, capacita_cavo=4):
    """
    Risolve il problema del routing dei cavi con Gurobi MILP.
    Implementazione fedele del modello matematico "branched topology".
    """
    n_ss = int(dati['n_ss'])
    coordinate = np.vstack([np.array(dati['substations']), np.array(dati['turbines'])])
    n_punti = len(coordinate)

    archi_potenziali = set()
    lista_delaunay = []
    lista_diagonali = []
    
    # --- FASE 1: DEFINIZIONE SPAZIO DI RICERCA ---
    if modalita == "reduced":
        tri = Delaunay(coordinate)
        for s in tri.simplices:
            for i in range(3): 
                e = tuple(sorted((int(s[i]), int(s[(i+1)%3]))))
                if e not in archi_potenziali:
                    archi_potenziali.add(e)
                    lista_delaunay.append(e)
        
        for i, vicini in enumerate(tri.neighbors):
            for k in range(3):
                nb = int(vicini[k])
                if nb > i:
                    s1, s2 = set(tri.simplices[i]), set(tri.simplices[nb])
                    condivisi = s1 & s2
                    diversi = tuple(sorted(s1 ^ s2))
                    if len(diversi) == 2 and len(condivisi) == 2:
                        nA, nB = list(condivisi)
                        nC, nD = list(diversi)
                        if verifica_incrocio(coordinate[nA], coordinate[nB], coordinate[nC], coordinate[nD]):
                            if diversi[0] >= n_ss and diversi[1] >= n_ss:
                                archi_potenziali.add(diversi)
                                lista_diagonali.append(diversi)
                            
        for t in range(n_ss, n_punti):
            for ss in range(n_ss): 
                archi_potenziali.add((int(ss), int(t)))
    else:
        for u in range(n_punti):
            for v in range(u + 1, n_punti):
                if not (u < n_ss and v < n_ss): 
                    archi_potenziali.add((u, v))

    # --- FASE 2: MODELLO MATEMATICO ---
    env = gp.Env(empty=True)
    env.setParam('OutputFlag', 0) 
    env.start()
    
    modello = gp.Model("WFCRP_Optimization", env=env)
    modello.setParam('TimeLimit', limite_tempo)
    modello.setParam('MIPGap', gap_ottimo) 
    modello.setParam('LazyConstraints', 1)

    archi_modello = []
    for u, v in archi_potenziali:
        dist = int(np.linalg.norm(coordinate[u]-coordinate[v]))
        if u < n_ss or v < n_ss: 
            archi_modello.append((max(u,v), min(u,v), dist))
        else: 
            archi_modello.extend([(u,v,dist), (v,u,dist)])

    coppie_nodi = [(a[0], a[1]) for a in archi_modello]
    
    # Variabili decisionali (link-is-active e link power flow)
    x = modello.addVars(coppie_nodi, vtype=GRB.BINARY, name="x")
    f = modello.addVars(coppie_nodi, vtype=GRB.CONTINUOUS, name="f")

    # Funzione Obiettivo: Minimizzare la lunghezza totale dei cavi pesata sulle distanze
    modello.setObjective(gp.quicksum(a[2]*x[a[0],a[1]] for a in archi_modello), GRB.MINIMIZE)

    # --- VINCOLI DEL MODELLO MATEMATICO ---

    # (1a) no bidirectional links: si impedisce il doppio flusso tra la stessa coppia di nodi
    for u, v in coppie_nodi:
        if u < v and (v, u) in x:
            modello.addConstr(x[u, v] + x[v, u] <= 1, name=f"1a_nobidir_{u}_{v}")

    # (1d) feeders carry all power: l'energia ai feeder equivale alla somma dell'energia delle turbine
    potenza_totale = n_punti - n_ss
    modello.addConstr(gp.quicksum(f[u, v] for u, v in coppie_nodi if v < n_ss) == potenza_totale, name="1d_feeders_power")

    for t in range(n_ss, n_punti):
        # (1c) single export per turbine: un cavo in uscita per ogni turbina
        modello.addConstr(x.sum(t, '*') == 1, name=f"1c_single_exp_{t}")
        
        # (1b) flow balance: Flusso uscente - Flusso entrante = Potenza generata (1 unità)
        modello.addConstr(f.sum(t, '*') - f.sum('*', t) == 1, name=f"1b_flow_bal_{t}")
        
    for k in coppie_nodi:
        # (1e) bind x and f: Flusso vincolato dalla capacità del cavo e dall'attivazione dello stesso
        modello.addConstr(f[k] <= capacita_cavo * x[k], name=f"1e_bind_upper_{k}")
        modello.addConstr(f[k] >= x[k], name=f"1e_bind_lower_{k}")

    # (1f) e (1g) no crossings: Sostituiti ed efficientati dinamicamente tramite Lazy Constraints
    def callback_incroci(model, where):
        if where == GRB.Callback.MIPSOL:
            val_x = model.cbGetSolution(x)
            attivi = []
            for (u, v), val in val_x.items():
                if val > 0.5:
                    if modalita == "reduced" and (u < n_ss or v < n_ss): 
                        continue 
                    arco = tuple(sorted((u, v)))
                    if arco not in attivi: 
                        attivi.append(arco)
            
            for i in range(len(attivi)):
                for j in range(i + 1, len(attivi)):
                    e1, e2 = attivi[i], attivi[j]
                    if verifica_incrocio(coordinate[e1[0]], coordinate[e1[1]], coordinate[e2[0]], coordinate[e2[1]]):
                        model.cbLazy(x.get(e1, 0) + x.get((e1[1], e1[0]), 0) + 
                                     x.get(e2, 0) + x.get((e2[1], e2[0]), 0) <= 1)

    modello.optimize(callback_incroci)
    
    archi_risultanti = []
    if modello.SolCount > 0:
        for k in coppie_nodi:
            if x[k].X > 0.5:
                archi_risultanti.append(k)
                
    env.dispose()
    return {
        "costo": modello.objVal if modello.SolCount > 0 else 0,
        "archi": archi_risultanti,
        "coords": coordinate,
        "n_ss": n_ss,
        "tempo": modello.Runtime,
        "archi_delaunay": lista_delaunay,
        "archi_diagonali": lista_diagonali,
        "archi_full": list(archi_potenziali) if modalita == "full" else []
    }