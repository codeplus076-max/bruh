# AI Target Model Retraining Guide

This guide ensures safe, reproducible, and effective model retraining whenever new symptoms or disease datasets are available without compromising the production application.

## 1. Directory Requirements
Ensure you have the following new CSV datasets ready inside the `data/` or root project path (ensure filenames match the `prepare_dataset.py` variables):
- `Final_Augmented_dataset_Diseases_and_Symptoms.csv` (The mapping of boolean symptoms)
- `Symptom-severity.csv` (Used for mapping gravity metrics)

## 2. Generate the Supervised Dataset
The application relies heavily on risk stratification and dynamic demographic inferences. Run the data preparation script to synthesize these missing elements.
```bash
python scripts/prepare_dataset.py
```
This generates `data/new_training_dataset.csv`.

## 3. Retrain the XGBoost and Support Classifiers
The training script will load the clean CSV, filter out untrainable rare anomalies (fewer than 5 instances), and initiate a grid comparison across:
- **Logistic Regression**
- **Random Forest**
- **XGBoost (Primary Choice)**

```bash
python scripts/train_disease_model.py
```
*Wait approximately 5 to 10 minutes depending on thread availability.*

The script will:
1. Print detailed `F1`, `Recall`, `Precision`, and `Accuracy` matrices.
2. Automatically save the preferred classifier to `backend/app/ml/triage_model_v2.joblib`.
3. Save feature lists and categories to `backend/app/ml/model_meta_v2.joblib`.

## 4. Test Model Schema Inference 
Do **NOT** push to production without verifying the strict feature parity expected by the FastAPI ML Predictor singleton:
```bash
python scripts/test_inference.py
```
This will launch a full local load of the new `.joblib` payload into RAM and generate test diagnostic outputs ranging from minor illness to emergency anomalies. Ensure `risk_score` and `important_features` conform strictly to numerical parameters and lists.

## 5. Deployment
Upon a successful test inference, simply commit the two `_v2.joblib` payload updates and trigger a deploy on your Host provider. The model will automatically hook into the newly configured predictor endpoint.
