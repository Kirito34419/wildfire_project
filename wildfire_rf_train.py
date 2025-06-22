import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os

# Load the training data
data = pd.read_csv('/home/unknown/wildfire_project/global_fire_training_data.csv')

# Drop rows with missing or extreme values (optional cleanup)
data = data.replace([np.inf, -np.inf], np.nan).dropna()

# Feature columns (adjust based on your actual columns)
features = [
    'NDVI', 'elevation', 'temperature_2m',
    'u_component_of_wind_10m', 'v_component_of_wind_10m',
    'frp', 'FireConfidence', 'BrightTi4', 'BrightTi5'
]

# Target: we'll use frp (fire radiative power) as a proxy for spread severity
X = data[features]
y = data['frp']

# Split into training and internal validation set (80/20)
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize the model
model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)

# Train the model
model.fit(X_train, y_train)

# Predict on validation set
y_pred = model.predict(X_val)

# Evaluate
rmse = np.sqrt(mean_squared_error(y_val, y_pred))
r2 = r2_score(y_val, y_pred)

print(f"Validation RMSE: {rmse:.2f}")
print(f"Validation R^2 Score: {r2:.2f}")

os.makedirs('models', exist_ok=True)
joblib.dump(model, 'models/wildfire_rf_model.pkl')
print("✅ Model saved as 'wildfire_rf_model.pkl'")

