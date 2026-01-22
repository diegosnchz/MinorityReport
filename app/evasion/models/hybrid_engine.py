import xgboost as xgb
import shap
import pandas as pd
import numpy as np
from typing import List, Dict, Any

class HybridRiskEngine:
    """
    Motor híbrido que usa XGBoost para calcular un 'Base Risk Score'
    antes de pasar los datos a la GAT (Graph Attention Network).
    """
    
    def __init__(self):
        # Modelo ligero y rápido
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=100, 
            max_depth=4, 
            learning_rate=0.05,
            use_label_encoder=False,
            eval_metric='logloss'
        )
        self.explainer = None
        self.is_trained = False

    def train_preprocessor(self, X: pd.DataFrame, y: pd.Series):
        """
        Entrena el pre-procesador XGBoost.
        X: Features tabulares (Hora, Clima, Densidad Patrullas)
        y: Resultado histórico (0: Evasión, 1: Captura)
        """
        self.xgb_model.fit(X, y)
        self.explainer = shap.TreeExplainer(self.xgb_model)
        self.is_trained = True
        print("Hybrid Engine: XGBoost Preprocessor Trained.")

    def get_base_risk(self, node_features: Dict[str, Any]) -> float:
        """
        Calcula el riesgo base de un nodo/situación.
        Este valor se usará como embedding inicial en la GAT.
        """
        if not self.is_trained:
            return 0.5 # Default uncertainty
            
        df = pd.DataFrame([node_features])
        # Retorna la probabilidad de la clase 1 (Captura)
        return float(self.xgb_model.predict_proba(df)[:, 1][0])

    def get_feature_importance(self, node_features: pd.DataFrame):
        """
        Retorna SHAP values para explicar por qué un nodo es riesgoso.
        Vital para el Dashboard de 'Explainability'.
        """
        if not self.is_trained:
            return None
            
        shap_values = self.explainer.shap_values(node_features)
        return shap_values

hybrid_engine = HybridRiskEngine()
