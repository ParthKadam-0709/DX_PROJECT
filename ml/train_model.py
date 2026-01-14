"""
train_model.py
Trains an optimized RandomForest model on crop recommendation data
"""
import os
import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# Load and explore the dataset
def load_and_explore_data():
    """Load dataset and perform exploratory data analysis"""
    try:
        df = pd.read_csv('ml/Crop_recommendation.csv')
        print(f"Dataset loaded successfully. Shape: {df.shape}")
        print("\nDataset Info:")
        print(df.info())
        print("\nFirst 5 rows:")
        print(df.head())
        print("\nColumn names:", df.columns.tolist())
        print("\nMissing values:")
        print(df.isnull().sum())
        print("\nDataset description:")
        print(df.describe())
        print("\nCrop distribution:")
        print(df['label'].value_counts())
        
        return df
    except FileNotFoundError:
        print("Error: Crop_recommendation.csv not found!")
        print("Make sure the file exists in the 'ml' directory")
        return None
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return None

def preprocess_data(df):
    """Preprocess the data for model training"""
    print("\n=== Data Preprocessing ===")
    
    # Create a copy to avoid modifying original
    df_processed = df.copy()
    
    # Encode target variable
    label_encoder = LabelEncoder()
    df_processed['label_encoded'] = label_encoder.fit_transform(df_processed['label'])
    
    # Get feature names
    feature_cols = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    
    # Check for missing values
    if df_processed[feature_cols].isnull().sum().any():
        print("Missing values found. Filling with median...")
        df_processed[feature_cols] = df_processed[feature_cols].fillna(df_processed[feature_cols].median())
    
    # Check for outliers (optional, based on domain knowledge)
    print("\nChecking for potential outliers...")
    for col in feature_cols:
        Q1 = df_processed[col].quantile(0.25)
        Q3 = df_processed[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = ((df_processed[col] < (Q1 - 1.5 * IQR)) | 
                   (df_processed[col] > (Q3 + 1.5 * IQR))).sum()
        if outliers > 0:
            print(f"  {col}: {outliers} potential outliers")
    
    return df_processed, feature_cols, label_encoder

def feature_engineering(df, feature_cols):
    """Create additional features to improve model performance"""
    print("\n=== Feature Engineering ===")
    
    # Create interaction features (domain knowledge about crop requirements)
    df['N_P_ratio'] = df['N'] / (df['P'] + 1)  # N to P ratio
    df['N_K_ratio'] = df['N'] / (df['K'] + 1)  # N to K ratio
    df['temp_humidity'] = df['temperature'] * df['humidity'] / 100  # Combined weather factor
    df['nutrient_sum'] = df['N'] + df['P'] + df['K']  # Total nutrients
    
    # Create categorical features based on optimal ranges (simplified)
    df['ph_category'] = pd.cut(df['ph'], 
                               bins=[0, 5.5, 6.5, 7.5, 8.5, 14],
                               labels=['acidic', 'slightly_acidic', 'neutral', 'slightly_alkaline', 'alkaline'])
    
    # One-hot encode categorical features
    df = pd.get_dummies(df, columns=['ph_category'], drop_first=True)
    
    # Update feature columns
    new_feature_cols = feature_cols + [
        'N_P_ratio', 'N_K_ratio', 'temp_humidity', 'nutrient_sum',
        'ph_category_slightly_acidic', 'ph_category_neutral', 
        'ph_category_slightly_alkaline', 'ph_category_alkaline'
    ]
    
    print(f"Added {len(new_feature_cols) - len(feature_cols)} new features")
    return df, new_feature_cols

def train_optimized_model(X_train, y_train, X_test, y_test):
    """Train and optimize RandomForest model"""
    print("\n=== Model Training ===")
    
    # Base model for comparison
    base_model = RandomForestClassifier(random_state=42, n_jobs=-1)
    base_model.fit(X_train, y_train)
    base_pred = base_model.predict(X_test)
    base_accuracy = accuracy_score(y_test, base_pred)
    print(f"Base RandomForest accuracy: {base_accuracy:.4f}")
    
    # Hyperparameter tuning with GridSearchCV
    print("\nPerforming hyperparameter tuning...")
    
    # Define parameter grid
    param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [10, 20, 30, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2'],
        'bootstrap': [True, False]
    }
    
    # Create and fit GridSearchCV
    rf = RandomForestClassifier(random_state=42, n_jobs=-1)
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=5,
        n_jobs=-1,
        verbose=1,
        scoring='accuracy'
    )
    
    grid_search.fit(X_train, y_train)
    
    # Get best model
    best_model = grid_search.best_estimator_
    print(f"\nBest parameters: {grid_search.best_params_}")
    print(f"Best cross-validation score: {grid_search.best_score_:.4f}")
    
    # Evaluate on test set
    y_pred = best_model.predict(X_test)
    best_accuracy = accuracy_score(y_test, y_pred)
    print(f"Test set accuracy: {best_accuracy:.4f}")
    
    # Detailed evaluation
    print("\n=== Classification Report ===")
    print(classification_report(y_test, y_pred))
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n=== Top 10 Feature Importances ===")
    print(feature_importance.head(10))
    
    return best_model, grid_search.best_params_

def save_model_and_artifacts(model, label_encoder, feature_cols, best_params, accuracy):
    """Save the trained model and related artifacts"""
    print("\n=== Saving Model ===")
    
    # Create artifacts dictionary
    artifacts = {
        'model': model,
        'label_encoder': label_encoder,
        'feature_columns': feature_cols,
        'model_parameters': best_params,
        'accuracy': accuracy,
        'input_features': ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    }
    
    # Define save path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    save_dir = os.path.join(project_root, 'DX_APP', 'model_artifacts')
    
    # Create directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)
    
    # Save artifacts
    model_path = os.path.join(save_dir, 'crop_recommendation_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(artifacts, f)
    
    print(f"Model and artifacts saved to: {model_path}")
    print(f"Model accuracy: {accuracy:.4f}")
    
    # Save metadata
    metadata = {
        'model_type': 'RandomForestClassifier',
        'training_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'num_features': len(feature_cols),
        'num_classes': len(label_encoder.classes_),
        'classes': label_encoder.classes_.tolist(),
        'best_params': best_params,
        'accuracy': float(accuracy)
    }
    
    metadata_path = os.path.join(save_dir, 'model_metadata.json')
    import json
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Metadata saved to: {metadata_path}")
    
    return model_path

def main():
    """Main execution function"""
    print("=" * 60)
    print("CROP RECOMMENDATION MODEL TRAINING")
    print("=" * 60)
    
    # Step 1: Load and explore data
    df = load_and_explore_data()
    if df is None:
        return
    
    # Step 2: Preprocess data
    df_processed, feature_cols, label_encoder = preprocess_data(df)
    
    # Step 3: Feature engineering
    df_engineered, enhanced_feature_cols = feature_engineering(df_processed, feature_cols)
    
    # Prepare data
    X = df_engineered[enhanced_feature_cols]
    y = df_engineered['label_encoded']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTraining set: {X_train.shape}")
    print(f"Test set: {X_test.shape}")
    
    # Step 4: Train optimized model
    model, best_params = train_optimized_model(X_train, y_train, X_test, y_test)
    
    # Step 5: Save model and artifacts
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    model_path = save_model_and_artifacts(model, label_encoder, enhanced_feature_cols, best_params, accuracy)
    
    print("\n" + "=" * 60)
    print("MODEL TRAINING COMPLETE")
    print("=" * 60)
    
    # Quick test prediction
    print("\n=== Sample Prediction ===")
    sample_data = X_test.iloc[0:1]
    prediction_encoded = model.predict(sample_data)[0]
    prediction_label = label_encoder.inverse_transform([prediction_encoded])[0]
    actual_label = label_encoder.inverse_transform([y_test.iloc[0]])[0]
    
    print(f"Sample features:\n{sample_data.iloc[0][:7]}")  # Show original 7 features
    print(f"Predicted crop: {prediction_label}")
    print(f"Actual crop: {actual_label}")
    print(f"Correct: {prediction_label == actual_label}")

if __name__ == "__main__":
    main()