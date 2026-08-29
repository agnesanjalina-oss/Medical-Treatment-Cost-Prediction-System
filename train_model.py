import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# =====================================================
# PROJECT PATHS
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_PATH = os.path.join(
    BASE_DIR,
    "bangladesh_hospital_medical_cost_dataset.csv"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "model"
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "medical_cost_model.pkl"
)


# =====================================================
# LOAD DATASET
# =====================================================

print()
print("========================================")
print("BANGLADESH HOSPITAL MEDICAL COST MODEL")
print("========================================")
print()

print("Loading dataset...")

if not os.path.exists(DATASET_PATH):
    raise FileNotFoundError(
        f"Dataset not found:\n{DATASET_PATH}"
    )

df = pd.read_csv(DATASET_PATH)

print("Dataset loaded successfully.")
print("Total records:", len(df))


# =====================================================
# REQUIRED COLUMNS
# =====================================================

required_columns = [
    "age",
    "gender",
    "department",
    "disease",
    "treatment_type",
    "hospital_days",
    "icu",
    "hospital_type",
    "hospital_location",
    "doctor_fee",
    "medicine_cost",
    "diagnostic_cost",
    "surgery_cost",
    "room_cost",
    "icu_cost",
    "consultation_cost",
    "treatment_cost"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        "Missing columns: "
        + ", ".join(missing_columns)
    )


# =====================================================
# KEEP REQUIRED COLUMNS
# =====================================================

df = df[required_columns].copy()


# =====================================================
# CLEAN TEXT COLUMNS
# =====================================================

text_columns = [
    "gender",
    "department",
    "disease",
    "treatment_type",
    "hospital_type",
    "hospital_location"
]

for column in text_columns:
    df[column] = (
        df[column]
        .astype(str)
        .str.strip()
    )


# =====================================================
# CLEAN ICU
# =====================================================

df["icu"] = (
    df["icu"]
    .astype(str)
    .str.strip()
    .str.lower()
    .map({
        "yes": 1,
        "no": 0,
        "1": 1,
        "0": 0
    })
)

if df["icu"].isna().any():
    raise ValueError(
        "Invalid ICU values found. "
        "Expected Yes/No or 1/0."
    )


# =====================================================
# NUMERIC COLUMNS
# =====================================================

numeric_columns = [
    "age",
    "hospital_days",
    "doctor_fee",
    "medicine_cost",
    "diagnostic_cost",
    "surgery_cost",
    "room_cost",
    "icu_cost",
    "consultation_cost",
    "treatment_cost"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# =====================================================
# REMOVE INVALID DATA
# =====================================================

df = df.dropna(
    subset=[
        "age",
        "hospital_days",
        "treatment_cost"
    ]
)

print()
print("Records after cleaning:", len(df))


# =====================================================
# VERIFY TREATMENT COST
# =====================================================

cost_columns = [
    "doctor_fee",
    "medicine_cost",
    "diagnostic_cost",
    "surgery_cost",
    "room_cost",
    "icu_cost",
    "consultation_cost"
]

df["calculated_cost"] = df[cost_columns].sum(axis=1)

difference = (
    df["treatment_cost"]
    - df["calculated_cost"]
)

maximum_difference = difference.abs().max()

print()
print("Cost verification")
print("-----------------")
print(
    "Maximum cost difference:",
    maximum_difference,
    "BDT"
)

if maximum_difference != 0:
    print(
        "WARNING: Some treatment costs "
        "do not equal the component cost sum."
    )
else:
    print(
        "All treatment costs verified successfully."
    )


# =====================================================
# INPUT FEATURES
# =====================================================

features = [
    "age",
    "gender",
    "department",
    "disease",
    "treatment_type",
    "hospital_days",
    "icu",
    "hospital_type",
    "hospital_location"
]

X = df[features]


# =====================================================
# TARGET
# =====================================================

y = df["treatment_cost"]


# =====================================================
# CATEGORICAL FEATURES
# =====================================================

categorical_features = [
    "gender",
    "department",
    "disease",
    "treatment_type",
    "hospital_type",
    "hospital_location"
]


# =====================================================
# NUMERICAL FEATURES
# =====================================================

numerical_features = [
    "age",
    "hospital_days",
    "icu"
]


# =====================================================
# PREPROCESSOR
# =====================================================

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            categorical_features
        ),
        (
            "numerical",
            "passthrough",
            numerical_features
        )
    ]
)


# =====================================================
# RANDOM FOREST MODEL
# =====================================================

random_forest = RandomForestRegressor(
    n_estimators=300,
    random_state=42,
    max_depth=20,
    min_samples_split=2,
    min_samples_leaf=1,
    n_jobs=-1
)


# =====================================================
# COMPLETE PIPELINE
# =====================================================

pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "model",
            random_forest
        )
    ]
)


# =====================================================
# TRAIN / TEST SPLIT
# =====================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)


# =====================================================
# DATASET INFORMATION
# =====================================================

print()
print("========================================")
print("DATASET INFORMATION")
print("========================================")

print("Total records     :", len(df))
print("Training records  :", len(X_train))
print("Testing records   :", len(X_test))
print("Input features    :", len(features))
print("Target            : treatment_cost")


# =====================================================
# TRAIN MODEL
# =====================================================

print()
print("Training Random Forest model...")
print("Please wait...")

pipeline.fit(
    X_train,
    y_train
)

print("Model training completed.")


# =====================================================
# TEST MODEL
# =====================================================

print()
print("Testing model...")

y_pred = pipeline.predict(X_test)


# =====================================================
# MODEL PERFORMANCE
# =====================================================

mae = mean_absolute_error(
    y_test,
    y_pred
)

mse = mean_squared_error(
    y_test,
    y_pred
)

rmse = mse ** 0.5

r2 = r2_score(
    y_test,
    y_pred
)


# =====================================================
# DISPLAY PERFORMANCE
# =====================================================

print()
print("========================================")
print("MODEL PERFORMANCE")
print("========================================")

print(
    "MAE  :", 
    round(mae, 2),
    "BDT"
)

print(
    "RMSE :",
    round(rmse, 2),
    "BDT"
)

print(
    "R²   :",
    round(r2, 4)
)


# =====================================================
# SAVE MODEL
# =====================================================

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)

joblib.dump(
    pipeline,
    MODEL_PATH
)


# =====================================================
# VERIFY MODEL FILE
# =====================================================

if os.path.exists(MODEL_PATH):

    model_size = os.path.getsize(
        MODEL_PATH
    )

    print()
    print("========================================")
    print("MODEL SAVED SUCCESSFULLY")
    print("========================================")

    print(
        "Model file:",
        MODEL_PATH
    )

    print(
        "Model size:",
        round(model_size / (1024 * 1024), 2),
        "MB"
    )

else:

    raise RuntimeError(
        "Model file was not created."
    )


# =====================================================
# SAMPLE PREDICTION
# =====================================================

sample = pd.DataFrame([
    {
        "age": 50,
        "gender": "Male",
        "department": "Cardiology",
        "disease": "Heart Failure",
        "treatment_type": "Medication",
        "hospital_days": 5,
        "icu": 0,
        "hospital_type": "Private",
        "hospital_location": "Dhaka"
    }
])

sample_prediction = pipeline.predict(
    sample
)[0]

print()
print("========================================")
print("SAMPLE PREDICTION")
print("========================================")

print(
    "Estimated treatment cost:",
    round(sample_prediction, 2),
    "BDT"
)

print()
print("Training completed successfully!")