"""
Model training module for flood risk prediction.

This module implements the training pipeline including hyperparameter tuning,
model evaluation, and validation.

Requirements: 1.5
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import logging
import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from .data_preparation import TrainingData

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    """Container for model evaluation metrics."""
    mse: float
    rmse: float
    mae: float
    r2: float
    accuracy_80_threshold: float  # % of predictions within 20% of actual


@dataclass
class TrainingResult:
    """Result of model training."""
    model: Any
    scaler: Any
    metrics: ModelMetrics
    best_params: Dict[str, Any]
    feature_importance: Dict[str, float]


class ModelTrainer:
    """
    Model trainer for flood risk prediction.
    
    This class handles:
    - Model selection
    - Hyperparameter tuning
    - Model training
    - Model evaluation
    
    Requirements: 1.5
    """

    def __init__(self, model_type: str = "random_forest"):
        """
        Initialize model trainer.
        
        Args:
            model_type: Type of model to train ("random_forest", "gradient_boosting", "ridge")
        """
        self.model_type = model_type
        self.model = None
        self.best_params = {}

    def train(
        self,
        training_data: TrainingData,
        tune_hyperparameters: bool = True,
        cv_folds: int = 5
    ) -> TrainingResult:
        """
        Train the flood risk prediction model.
        
        This method:
        1. Optionally tunes hyperparameters using grid search
        2. Trains the model on training data
        3. Evaluates on validation and test sets
        4. Returns trained model with metrics
        
        Args:
            training_data: Prepared training data
            tune_hyperparameters: Whether to perform hyperparameter tuning
            cv_folds: Number of cross-validation folds
            
        Returns:
            TrainingResult with trained model and metrics
            
        Requirements: 1.5
        """
        logger.info(f"Training {self.model_type} model...")
        
        # Get base model and parameter grid
        base_model = self._get_base_model()
        param_grid = self._get_param_grid()
        
        # Hyperparameter tuning
        if tune_hyperparameters and param_grid:
            logger.info("Performing hyperparameter tuning...")
            self.model, self.best_params = self._tune_hyperparameters(
                base_model,
                param_grid,
                training_data.X_train,
                training_data.y_train,
                cv_folds
            )
        else:
            self.model = base_model
            self.model.fit(training_data.X_train, training_data.y_train)
            self.best_params = {}
        
        logger.info("Model training completed")
        
        # Evaluate model
        metrics = self._evaluate_model(
            self.model,
            training_data.X_test,
            training_data.y_test
        )
        
        logger.info(f"Test metrics: RMSE={metrics.rmse:.2f}, R²={metrics.r2:.3f}, "
                   f"Accuracy@80%={metrics.accuracy_80_threshold:.1f}%")
        
        # Calculate feature importance
        feature_importance = self._calculate_feature_importance(
            self.model,
            training_data.feature_names
        )
        
        return TrainingResult(
            model=self.model,
            scaler=training_data.scaler,
            metrics=metrics,
            best_params=self.best_params,
            feature_importance=feature_importance
        )

    def _get_base_model(self) -> Any:
        """
        Get base model based on model type.
        
        Returns:
            Scikit-learn model instance
        """
        if self.model_type == "random_forest":
            return RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == "gradient_boosting":
            return GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        elif self.model_type == "ridge":
            return Ridge(alpha=1.0, random_state=42)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def _get_param_grid(self) -> Dict[str, list]:
        """
        Get hyperparameter grid for tuning.
        
        Returns:
            Dictionary of parameter names to lists of values
        """
        if self.model_type == "random_forest":
            return {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
        elif self.model_type == "gradient_boosting":
            return {
                'n_estimators': [50, 100, 200],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1, 0.2]
            }
        elif self.model_type == "ridge":
            return {
                'alpha': [0.1, 1.0, 10.0, 100.0]
            }
        else:
            return {}

    def _tune_hyperparameters(
        self,
        base_model: Any,
        param_grid: Dict[str, list],
        X_train: np.ndarray,
        y_train: np.ndarray,
        cv_folds: int
    ) -> tuple:
        """
        Tune hyperparameters using grid search with cross-validation.
        
        Args:
            base_model: Base model to tune
            param_grid: Parameter grid
            X_train: Training features
            y_train: Training targets
            cv_folds: Number of CV folds
            
        Returns:
            Tuple of (best_model, best_params)
        """
        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=cv_folds,
            scoring='neg_mean_squared_error',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        logger.info(f"Best parameters: {grid_search.best_params_}")
        logger.info(f"Best CV score: {-grid_search.best_score_:.2f}")
        
        return grid_search.best_estimator_, grid_search.best_params_

    def _evaluate_model(
        self,
        model: Any,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> ModelMetrics:
        """
        Evaluate model on test set.
        
        Args:
            model: Trained model
            X_test: Test features
            y_test: Test targets
            
        Returns:
            ModelMetrics with evaluation results
        """
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Calculate accuracy within 20% threshold (requirement: 80% accuracy)
        # A prediction is "accurate" if it's within 20% of the actual value
        relative_errors = np.abs(y_pred - y_test) / (y_test + 1e-6)  # Avoid division by zero
        accuracy_80 = np.mean(relative_errors <= 0.20) * 100
        
        return ModelMetrics(
            mse=mse,
            rmse=rmse,
            mae=mae,
            r2=r2,
            accuracy_80_threshold=accuracy_80
        )

    def _calculate_feature_importance(
        self,
        model: Any,
        feature_names: list
    ) -> Dict[str, float]:
        """
        Calculate feature importance.
        
        Args:
            model: Trained model
            feature_names: List of feature names
            
        Returns:
            Dictionary of feature names to importance scores
        """
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            return dict(zip(feature_names, importances))
        else:
            # For models without feature_importances_ (e.g., Ridge)
            if hasattr(model, 'coef_'):
                importances = np.abs(model.coef_)
                return dict(zip(feature_names, importances))
            else:
                return {}

    def save_model(
        self,
        model: Any,
        scaler: Any,
        model_path: str,
        version: str = "1.0.0"
    ) -> None:
        """
        Save trained model to file.
        
        Args:
            model: Trained model
            scaler: Fitted scaler
            model_path: Path to save model
            version: Model version string
        """
        model_data = {
            'model': model,
            'scaler': scaler,
            'version': version,
            'model_type': self.model_type,
            'best_params': self.best_params
        }
        
        save_path = Path(model_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {model_path}")


def train_and_save_model(
    training_data: TrainingData,
    model_path: str,
    model_type: str = "random_forest",
    tune_hyperparameters: bool = True,
    version: str = "1.0.0"
) -> TrainingResult:
    """
    Convenience function to train and save a model.
    
    Args:
        training_data: Prepared training data
        model_path: Path to save trained model
        model_type: Type of model to train
        tune_hyperparameters: Whether to tune hyperparameters
        version: Model version string
        
    Returns:
        TrainingResult with trained model and metrics
    """
    trainer = ModelTrainer(model_type=model_type)
    
    result = trainer.train(
        training_data,
        tune_hyperparameters=tune_hyperparameters
    )
    
    trainer.save_model(
        result.model,
        result.scaler,
        model_path,
        version
    )
    
    return result
