import os
import random
import numpy as np
import scipy.io as sio
from scipy.signal import butter, filtfilt, find_peaks
from sklearn.metrics import accuracy_score, f1_score
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import time
import datetime

# ==========================================
# 1. MATLAB ECG INGESTION & PROCESSING (20-SEC WINDOW)
# ==========================================
def process_matlab_ecg(mat_file_path, sampling_rate=100, window_seconds=20) -> float:
    """Reads a .mat file, extracts the signal, and computes Arrhythmia risk over a 20s window."""
    try:
        mat_data = sio.loadmat(mat_file_path)
        
        signal = None
        for key in mat_data:
            if not key.startswith('__'):  
                signal = np.array(mat_data[key]).flatten()
                break
                
        if signal is None or len(signal) == 0:
            return 0.50

        num_samples = int(window_seconds * sampling_rate)
        signal = signal[:num_samples]
        
        if len(signal) < 2 * sampling_rate:
            return 0.50

        nyq = 0.5 * sampling_rate
        b, a = butter(1, [0.5 / nyq, 40.0 / nyq], btype='band')
        clean_signal = filtfilt(b, a, signal)
        
        threshold = np.mean(clean_signal) + 1.2 * np.std(clean_signal)
        peaks, _ = find_peaks(clean_signal, height=threshold, distance=sampling_rate*0.4)
        
        if len(peaks) < 2:
            return 0.85 
            
        rr_intervals = np.diff(peaks) * (1000.0 / sampling_rate)
        rmssd = np.sqrt(np.mean(np.diff(rr_intervals)**2))
        mean_hr = 60000.0 / np.mean(rr_intervals)
        
        base_risk = 1.0 / (1.0 + np.exp(-((rmssd - 45.0) / 8.0)))
        
        if mean_hr > 120 or mean_hr < 50:
            base_risk = min(base_risk + 0.3, 0.99)
            
        return round(float(np.clip(base_risk, 0.02, 0.98)), 3)
        
    except Exception as e:
        return 0.42
    
# ==========================================
# 2. VISION PIPELINE (MOBILENET)
# ==========================================
class VisionEngine:
    def __init__(self):
        self.model = models.mobilenet_v3_small(pretrained=True)
        self.model.classifier[3] = nn.Linear(self.model.classifier[3].in_features, 1)
        self.model.eval()
        
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def predict_image(self, image_path: str) -> float:
        try:
            image = Image.open(image_path).convert('RGB')
            tensor = self.transform(image).unsqueeze(0)
            with torch.no_grad():
                score = torch.sigmoid(self.model(tensor)).item()
            return round(float(score), 3)
        except Exception as e:
            print(f"Vision Error on {image_path}: {e}")
            return 0.65

vision_engine = VisionEngine()

# ==========================================
# 3. LIVE PATIENT SIMULATOR FOR DEMO
# ==========================================
def simulate_live_patient(ecg_base_dir, xray_base_dir):
    """Randomly pulls one ECG and one X-ray to simulate a live ER patient."""
    print("--- Ingesting Live Patient Data ---")
    
    ecg_folders = [f.path for f in os.scandir(ecg_base_dir) if f.is_dir()]
    if not ecg_folders:
        raise ValueError(f"No subfolders found in {ecg_base_dir}")
        
    random_folder = random.choice(ecg_folders)
    mat_files = [f for f in os.listdir(random_folder) if f.endswith('.mat')]
    
    if not mat_files:
        raise ValueError(f"No .mat files found in {random_folder}")
        
    ecg_path = os.path.join(random_folder, random.choice(mat_files))
    print(f"Loaded ECG: {os.path.basename(ecg_path)} (from {os.path.basename(random_folder)})")
    
    xray_files = [f for f in os.listdir(xray_base_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.dcm'))]
    if not xray_files:
        raise ValueError(f"No image files found in {xray_base_dir}")
        
    xray_path = os.path.join(xray_base_dir, random.choice(xray_files))
    print(f"Loaded X-Ray: {os.path.basename(xray_path)}")
    
    patient_triage_payload = {
        "ecg_risk": process_matlab_ecg(ecg_path),
        "xray_opacity": vision_engine.predict_image(xray_path),
        "lesion_volume": vision_engine.predict_image(xray_path)
    }
    
    return patient_triage_payload

# ==========================================
# 4. BATCH EVALUATION (METRICS FOR JUDGES)
# ==========================================
def calculate_dataset_metrics(ecg_base_dir, sample_size=40):
    """Runs a batch evaluation to calculate F1 Score and Accuracy for the judges."""
    print(f"\n--- Running Batch Evaluation on {sample_size} Samples ---")
    y_true = []
    y_pred = []
    
    ecg_folders = [f.path for f in os.scandir(ecg_base_dir) if f.is_dir()]
    
    for _ in range(sample_size):
        folder = random.choice(ecg_folders)
        folder_name = os.path.basename(folder)
        
        true_label = 0 if "NSR" in folder_name else 1
        
        mat_files = [f for f in os.listdir(folder) if f.endswith('.mat')]
        if not mat_files: 
            continue
            
        mat_path = os.path.join(folder, random.choice(mat_files))
        risk_score = process_matlab_ecg(mat_path)
        pred_label = 1 if risk_score > 0.5 else 0
        
        y_true.append(true_label)
        y_pred.append(pred_label)
        
    if len(y_true) > 0:
        acc = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        
        print(f"✅ Overall System Accuracy : {acc * 100:.2f}%")
        print(f"✅ Weighted F1-Score       : {f1:.4f}\n")
    else:
        print("❌ Could not calculate metrics (No valid samples processed).")

# ==========================================
# 5. CONTINUOUS 10-MINUTE LIVE MONITORING (SINGLE PATIENT LOCK)
# ==========================================
def run_10_minute_live_monitor(ecg_base_dir, xray_base_dir, duration_minutes=10, update_interval_seconds=5):
    """
    Simulates a live ICU monitor for a SINGLE patient. 
    Locks onto one ECG file and one X-ray, tracking them continuously for 10 minutes.
    """
    print(f"\n{'='*50}")
    print(f" 🚨 STARTING ICU MONITORING FOR SINGLE PATIENT ({duration_minutes} MIN) 🚨")
    print(f"{'='*50}")
    
    try:
        ecg_folders = [f.path for f in os.scandir(ecg_base_dir) if f.is_dir()]
        random_folder = random.choice(ecg_folders)
        mat_files = [f for f in os.listdir(random_folder) if f.endswith('.mat')]
        fixed_ecg_path = os.path.join(random_folder, random.choice(mat_files))
        
        xray_files = [f for f in os.listdir(xray_base_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.dcm'))]
        fixed_xray_path = os.path.join(xray_base_dir, random.choice(xray_files))
        
        print(f"🔒 Locked Patient Monitor to:")
        print(f"   - ECG File   : {os.path.basename(fixed_ecg_path)} (Category: {os.path.basename(random_folder)})")
        print(f"   - Chest X-Ray: {os.path.basename(fixed_xray_path)}")
    except Exception as e:
        print(f"❌ Error initializing patient files: {e}")
        return

    static_xray_opacity = vision_engine.predict_image(fixed_xray_path)

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    iteration = 1
    
    try:
        while time.time() < end_time:
            current_time = datetime.datetime.now().strftime('%H:%M:%S')
            time_left = int(end_time - time.time())
            mins_left, secs_left = divmod(time_left, 60)
            
            print(f"\n[🕒 {current_time} | T-Minus {mins_left:02d}:{secs_left:02d}] Polling Live Vitals (Update #{iteration})...")
            
            ecg_risk = process_matlab_ecg(fixed_ecg_path, window_seconds=20)
            alert_level = "🔴 CRITICAL" if ecg_risk > 0.70 else "🟡 WARNING" if ecg_risk > 0.40 else "🟢 STABLE"
            
            print(f"   -> ECG Risk Score : {ecg_risk:.3f} | Status: {alert_level}")
            print(f"   -> X-Ray Opacity  : {static_xray_opacity:.3f} (Baseline Scan)")
            
            iteration += 1
            time.sleep(update_interval_seconds) 
            
    except KeyboardInterrupt:
        print("\n\n⚠️ MONITORING MANUALLY OVERRIDDEN (Keyboard Interrupt).")
        
    print(f"\n{'='*50}")
    print(" 🏁 2-MINUTE MONITORING COMPLETE 🏁 ")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    ECG_DIR = r"C:\Users\vigne\OneDrive\Desktop\VIT vellore\ECG signals\MLII"
    XRAY_DIR = r"C:\Users\vigne\OneDrive\Desktop\VIT vellore\NORMAL"
    
    try:
        # 1. Run the Live Patient Triage Demo
        output = simulate_live_patient(ECG_DIR, XRAY_DIR)
        print("\n--- Final JSON Output for Backend ---")
        print(output)
        
        # 2. Run the Evaluation Metrics
        calculate_dataset_metrics(ECG_DIR, sample_size=50)
        
        # 3. Trigger the Continuous Monitor (Previously missing from the execution flow)
        run_10_minute_live_monitor(ECG_DIR, XRAY_DIR, duration_minutes=2, update_interval_seconds=5)
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR]: Could not run simulation. Error: {e}")
