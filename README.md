#  Diagnosing the Rare: AI-Based Early Detection of Tumoral Calcinosis

> Leveraging Advanced Data Augmentation and Synthetic Lesion Simulation to Overcome Extreme Data Scarcity

**Made by:** Eng. Hadeer Mohamed  
**Supervised by:** Dr. Elhoseeny  
**Internship:** Huawei ETA & National Telecommunication Institute (NTI)

---

##  Overview

Tumoral Calcinosis (TC) is an ultra-rare condition characterized by progressive calcium phosphate deposits around large joints (hips, elbows, shoulders). Its rarity means:

- Many radiologists may never see a case → frequent misdiagnosis as arthritis, gout, or sarcomas
- No large public datasets exist for deep learning
- Zero early-stage TC images exist in any public dataset

This project tackles all three problems through a novel full-stack AI pipeline.

---

##  Project Pipeline

```
Raw Data → Data Augmentation → Lesion Simulation → Model Training (ResNet50) → Model Evaluation
```

---

##  Dataset

The entire dataset was **built from scratch** by manually collecting TC X-ray images from:
- [Radiopaedia](https://radiopaedia.org)
- [LearningRadiology](https://www.learningradiology.com)
- [RadiologyKey](https://radiologykey.com)
- Reddit and other medical sources

Normal X-ray images were sourced from the **MURA dataset**.

```
dataset/
├── raw/
│   └── normal/          # Normal X-ray images (from MURA)
├── augmented/           # Augmented TC images (labeled as 'late' stage)
└── lesion_simulated/
    └── early/           # Synthetically generated early-stage TC images
```

**Class distribution:** Severe imbalance — TC cases are a small minority vs. normal images.

---

##  Strategies to Overcome Data Scarcity

### Strategy 1: Intensity-Preserving Data Augmentation

Standard augmentation breaks the radiological semantics of calcium deposits. Instead, a targeted pipeline using **Albumentations** was developed:

| Technique | Purpose |
|---|---|
| Elastic Transform & Grid Distortion | Simulate soft tissue deformation & patient positioning variation |
| Contrast / Limited CLAHE | Simulate different imaging protocols, keeping calcifications hyperdense |
| Blur & Noise | Mimic different scanner qualities, reduce overfitting to artifact-free edges |

Post-augmentation intensity distributions were rigorously analyzed to ensure clinical validity.

### Strategy 2: Synthetic Early-Stage Lesion Simulation

Since **zero early-stage TC images exist**, a heuristic-based simulation algorithm was developed to generate progressive stages of TC from normal X-rays:

1. **Joint Localization** — Detected periarticular regions using BiomedParse segmentation masks
2. **Synthetic Calcification Generation** — Programmatically generated small, bright, irregularly shaped calcified regions
3. **Overlay Masks** — Semi-transparent masks highlight detected regions and simulated lesions
4. **Progressive Realism** — Parameters (size, density, texture, margin blurriness) simulate different disease stages, starting with faint punctate calcifications for early-stage representation

---

##  Models

### Model 1 — Normal vs. TC Classifier

Detects whether an X-ray shows Tumoral Calcinosis or is normal.

```python
resnet_model = Sequential([
    ResNet50(weights="imagenet", include_top=False, input_shape=(224, 224, 3)),
    GlobalAveragePooling2D(),
    Dense(256, activation='relu'),
    BatchNormalization(),
    Dropout(0.6),
    Dense(128, activation='relu'),
    BatchNormalization(),
    Dropout(0.6),
    Dense(1, activation='sigmoid')
])
```

- **Optimizer:** Adam (lr=0.0001)
- **Loss:** Binary Crossentropy
- **Class weights:** `{0: 1.0, 1: 5}` to handle class imbalance
- **Callbacks:** EarlyStopping (patience=15) + ModelCheckpoint

### Model 2 — Early vs. Late Stage Classifier

For images already classified as TC, this model determines the disease stage.

- Same ResNet50 architecture
- Trained only on TC images (simulated early + augmented late)
- Binary classification: `early (0)` vs. `late (1)`

---

##  Results

### Model 1 — Normal vs. TC

| Metric | Normal | TC |
|---|---|---|
| Precision | 0.96 | 0.90 |
| Recall | 0.97 | 0.87 |
| F1-Score | 0.96 | 0.88 |
| **Overall Accuracy** | **0.94** | |

### Model 2 — Early vs. Late TC

| Metric | Late | Early |
|---|---|---|
| Precision | 1.00 | 0.94 |
| Recall | 0.98 | 1.00 |
| F1-Score | 0.99 | 0.97 |
| **Overall Accuracy** | **0.99** | |

**Key finding:** The model correctly identified all early-stage TC cases (0 false negatives for early), proving it learned the concept of TC even from synthetically generated data.

---

##  Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Hadeer-Mohamed-Eldesokeyy/TC_Project_New
```

### 2. Install dependencies

```bash
pip install tensorflow torch torchvision albumentations opencv-python scikit-learn pydicom seaborn matplotlib tqdm
```

### 3. Mount Google Drive (if using Colab)

```python
from google.colab import drive
drive.mount('/content/drive')
```

### 4. Set dataset paths

```python
tc_augmented = '/content/TC_Project_New/dataset/augmented'
tc_simulated = '/content/TC_Project_New/dataset/lesion_simulated/early'
normal       = '/content/TC_Project_New/dataset/raw/normal'
```

### 5. Run the notebooks

| Notebook | Description |
|---|---|
| `Preprocessing_model1.ipynb` | Data loading, preprocessing & Normal vs. TC classifier |
| `Preprocessing_model2.ipynb` | Early vs. Late TC stage classifier |

---

##  Technical Stack

| Component | Technology |
|---|---|
| Deep Learning Framework | TensorFlow / Keras |
| Base Architecture | ResNet50 (ImageNet pretrained) |
| Data Augmentation | Albumentations |
| Image Processing | OpenCV, PIL |
| Medical Imaging | PyDICOM |
| Segmentation (Simulation) | BiomedParse |
| Evaluation | scikit-learn, seaborn |

---

##  Future Work

- **Grad-CAM / Explainability** — Visualize what the model focuses on for clinical trust
- **Multi-Modal Learning** — Incorporate patient biochemical data (e.g., phosphate levels)
- **Clinical Deployment** — Prospective validation in real hospital workflows
- **Comparison with other rare disease AI pipelines**

---

##  References

- Cossio, M. (2023). Augmenting Medical Imaging: A Comprehensive Catalogue of 65 Techniques. arXiv:2303.01178
- Radiopaedia: [Tumoural Calcinosis](https://radiopaedia.org/articles/tumoural-calcinosis-1)
- LearningRadiology: [Tumoral Calcinosis](https://www.learningradiology.com/notes/bonenotes/tumoralcalcinosispage.htm)
- Alam, A., et al. (2011). Tumoral Calcinosis. PMC4925452

---

##  Author

**Hadeer Mohamed**  
Computer Engineering Student | AI & Data Science  
📧 hadeer.mohamed.eldesokey@gmail.com  
🔗 [LinkedIn](www.linkedin.com/in/hadeer-mohamed-eldesokey) | [GitHub](https://github.com/Hadeer-Mohamed-Eldesokeyy)
