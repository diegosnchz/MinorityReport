import xgboost as xgb
import shap
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging
from app.core import hardware_switch as hw

class HybridRiskEngine:
    """
    Motor híbrido que usa XGBoost para calcular un 'Base Risk Score'
    antes de pasar los datos a la GAT (Graph Attention Network).
    Ahora con soporte para RAPIDS (cuDF) y aceleración por GPU.
    """
    
    def __init__(self):
        # Configurar modelo con soporte GPU si es posible
        base_params = {
            'n_estimators': 100, 
            'max_depth': 4, 
            'learning_rate': 0.05,
            'use_label_encoder': False,
            'eval_metric': 'logloss'
        }
        
        self.params = hw.get_xgboost_params(base_params)
        
        if hw.HAS_GPU:
            print("Hybrid Engine: Initializing in GPU Mode (RAPIDS+CUDA)")
        else:
            print("Hybrid Engine: Initializing in CPU Mode")
            
        self.xgb_model = xgb.XGBClassifier(**self.params)
        self.explainer = None
        self.is_trained = False

    def train_preprocessor(self, X: pd.DataFrame, y: pd.Series):
        """
        Entrena el pre-procesador XGBoost.
        Soporta DataFrames de Pandas o cuDF.
        """
        # Si tenemos GPU y data es Pandas, intentar pasar a cuDF (Opcional, XGBoost maneja ambos)
        self.xgb_model.fit(X, y)
        
        # TreeExplainer funciona mejor en CPU para modelos pequeños, 
        # pero 'gpu_predictor' puede usarse para inferencia
        self.explainer = shap.TreeExplainer(self.xgb_model)
        self.is_trained = True
        print(f"Hybrid Engine: XGBoost Preprocessor Trained (GPU={hw.HAS_GPU}).")

    def get_base_risk(self, node_features: Dict[str, Any]) -> float:
        """
        Calcula el riesgo base de un nodo/situación.
        Este valor se usará como embedding inicial en la GAT.
        """
        if not self.is_trained:
            return 0.5 # Default uncertainty
            
        # Inferencia rápida
        # Si la entrada es un dict, convertimos a DF
        if hw.HAS_GPU:
            # Para 1 fila, la sobrecarga de cuDF puede no valer la pena, 
            # pero mantenemos la coherencia si el pipeline es full GPU.
            df = hw.cudf.DataFrame([node_features])
        else:
            df = pd.DataFrame([node_features])

        # Retorna la probabilidad de la clase 1 (Captura)
        preds = self.xgb_model.predict_proba(df)
        
        # Manejo de salida (numpy vs cupy/cudf)
        if hw.HAS_GPU:
             # XGBoost devuelve numpy array incluso con input gpu si no se especifica output
             return float(preds[:, 1][0])
        else:
             return float(preds[:, 1][0])

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
