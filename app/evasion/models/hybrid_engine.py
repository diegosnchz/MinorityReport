import xgboost as xgb
try:
    import shap
except Exception:  # pragma: no cover - optional dependency
    shap = None
import pandas as pd
from typing import Dict, Any, Optional
import logging
from app.core import hardware_switch as hw

logger = logging.getLogger(__name__)

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
            logger.info("Hybrid Engine: Initializing in GPU Mode (RAPIDS+CUDA)")
        else:
            logger.info("Hybrid Engine: Initializing in CPU Mode")
            
        self.xgb_model = xgb.XGBClassifier(**self.params)
        self.explainer = None
        self.is_trained = False

    def train_preprocessor(self, X: pd.DataFrame, y: pd.Series) -> None:
        """
        Entrena el pre-procesador XGBoost.
        Soporta DataFrames de Pandas o cuDF.
        """
        # Si tenemos GPU, intentamos mover a cuDF cuando sea posible
        X_train = hw.to_gpu_if_possible(X) if hw.HAS_GPU else X
        self.xgb_model.fit(X_train, y)
        
        # TreeExplainer funciona mejor en CPU para modelos pequeños, 
        # pero 'gpu_predictor' puede usarse para inferencia
        if shap is not None:
            self.explainer = shap.TreeExplainer(self.xgb_model)
        else:
            self.explainer = None
            logger.warning("SHAP not available. Explainability disabled.")
        self.is_trained = True
        logger.info("Hybrid Engine: XGBoost Preprocessor Trained (GPU=%s).", hw.HAS_GPU)

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
            # pero mantenemos coherencia si el pipeline es full GPU.
            df = hw.cudf.DataFrame([node_features])
        else:
            df = pd.DataFrame([node_features])

        # Retorna la probabilidad de la clase 1 (Captura)
        preds = self.xgb_model.predict_proba(df)
        
        # Manejo de salida (numpy vs cupy/cudf)
        # XGBoost devuelve numpy array incluso con input GPU si no se especifica output
        return float(preds[:, 1][0])

    def get_feature_importance(self, node_features: pd.DataFrame) -> Optional[Any]:
        """
        Retorna SHAP values para explicar por qué un nodo es riesgoso.
        Vital para el Dashboard de 'Explainability'.
        """
        if not self.is_trained:
            return None
            
        if self.explainer is None:
            return None
        shap_values = self.explainer.shap_values(node_features)
        return shap_values

hybrid_engine = HybridRiskEngine()
