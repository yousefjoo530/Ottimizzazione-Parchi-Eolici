import numpy as np

def orientamento_punti(p, q, r):
    """
    Ritorna l'orientamento di una terna di punti:
    0: Collineari
    1: Orario
    2: Antiorario
    """
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if val == 0: return 0 
    return 1 if val > 0 else 2

def verifica_incrocio(A, B, C, D):
    """
    Verifica se i segmenti AB e CD si incrociano geometricamente.
    Utilizza il test dell'orientamento per determinare l'intersezione.
    """
    # Se i segmenti condividono un estremo (es. due cavi che partono dalla stessa turbina),
    # non è considerato un incrocio fisico.
    if np.array_equal(A, C) or np.array_equal(A, D) or np.array_equal(B, C) or np.array_equal(B, D):
        return False
    
    # Calcolo dei 4 orientamenti necessari
    o1 = orientamento_punti(A, B, C)
    o2 = orientamento_punti(A, B, D)
    o3 = orientamento_punti(C, D, A)
    o4 = orientamento_punti(C, D, B)

    # Caso generale: i segmenti si incrociano se le coppie di orientamenti sono diverse
    if o1 != o2 and o3 != o4:
        return True
        
    return False

def conta_incroci_totali(archi, coordinate):
    """
    Analizza l'intero layout finale e conta il numero totale di incroci.
    Viene utilizzata per validare la soluzione trovata da Gurobi.
    """
    contatore = 0
    lista_archi = list(archi)
    
    # Confronto ogni coppia di archi una sola volta (complessità O(N^2))
    for i in range(len(lista_archi)):
        for j in range(i + 1, len(lista_archi)):
            e1, e2 = lista_archi[i], lista_archi[j]
            
            # Recupero le coordinate reali dai nodi degli archi
            if verifica_incrocio(coordinate[e1[0]], coordinate[e1[1]], 
                                coordinate[e2[0]], coordinate[e2[1]]):
                contatore += 1
                
    return contatore


