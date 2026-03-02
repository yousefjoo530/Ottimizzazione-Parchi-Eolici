Wind Farm Cable Routing Optimization (MILP)

Questo progetto contiene il codice sviluppato. L'obiettivo è risolvere il problema dell'ottimizzazione del layout dei cavi sottomarini per parchi eolici (Wind Farm Cable Routing Problem) minimizzando la lunghezza totale dei cavi.

## Modelli Confrontati
Il progetto implementa e confronta due approcci modellistici basati su Programmazione Lineare Intera Mista (MILP):
1. **Full Graph**: Considera tutte le connessioni possibili tra le turbine .
2. **Mesh A+ (Delaunay + Diagonali)**: Un approccio geometrico avanzato che riduce lo spazio di ricerca mantenendo solo le connessioni rilevanti (Triangolazione di Delaunay e test di intersezione), garantendo l'ottimo globale con tempi di calcolo drasticamente inferiori per istanze di grandi dimensioni.

Il modello matematico è stato implementato utilizzando il solver **Gurobi**.

Si Inizia con il file **Data-set.py**


```bash
pip install -r requirements.txt
