import time
import json
import pandas as pd
from rouge_score import rouge_scorer

def simulate_evaluation():
    print(" Evaluando desempeño...")
    time.sleep(2)
    results = {
        "Recall@5": 0.73,
        "MRR": 0.61,
        "nDCG": 0.68,
        "ROUGE-L": 0.54,
        "Latencia promedio (ms)": 220
    }
    pd.DataFrame([results]).to_csv("/reports/resultados_comparativos.csv", index=False)
    print(" Evaluación simulada completada.")

if __name__ == "__main__":
    simulate_evaluation()
