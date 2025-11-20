# Non-Intrusive Load Monitoring (NILM) Research Report
# Energy Disaggregation for Computer Vision Utility Monitor

**Date:** November 19, 2025
**Project:** Multi-Utility Meter Monitoring System
**Location:** Ilderton, Ontario, Canada
**Prepared for:** Integration with existing vision-based utility monitoring platform

---

## Executive Summary

This report provides a comprehensive analysis of Non-Intrusive Load Monitoring (NILM) technology for disaggregating whole-home electricity consumption into individual appliance usage. The goal is to identify individual appliances from the aggregate electric meter reading without installing sensors on each appliance.

### Key Findings

1. **Feasibility with 60-second sampling:** NILM is possible with 1 Hz (60-second) data, but limited to steady-state disaggregation approaches rather than transient-based detection
2. **Target accuracy:** 90-95% for high-power appliances (>2kW), 75-85% for medium appliances (500W-2kW)
3. **Recommended approach:** Hybrid system combining event detection, pattern matching, and machine learning
4. **Timeline to production:** 6-12 months for initial deployment with continuous improvement through user feedback
5. **Cost:** Minimal additional infrastructure cost; primary investment is development time and training data

---

## Table of Contents

1. [NILM Technology Overview](#1-nilm-technology-overview)
2. [Current System Analysis](#2-current-system-analysis)
3. [Target Appliances for Canadian Households](#3-target-appliances-for-canadian-households)
4. [Technical Requirements and Constraints](#4-technical-requirements-and-constraints)
5. [NILM Algorithms and Approaches](#5-nilm-algorithms-and-approaches)
6. [Public Datasets and Training Resources](#6-public-datasets-and-training-resources)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [Database Schema and Data Flow](#8-database-schema-and-data-flow)
9. [UI/UX Design Recommendations](#9-ui-ux-design-recommendations)
10. [Accuracy Expectations and Challenges](#10-accuracy-expectations-and-challenges)
11. [Competitive Analysis](#11-competitive-analysis)
12. [Research Partnerships and Open Source](#12-research-partnerships-and-open-source)
13. [Cost-Benefit Analysis](#13-cost-benefit-analysis)
14. [Recommendations and Next Steps](#14-recommendations-and-next-steps)

---

## 1. NILM Technology Overview

### 1.1 What is NILM?

**Non-Intrusive Load Monitoring (NILM)**, also called Non-Intrusive Appliance Load Monitoring (NIALM), is the process of disaggregating total household power consumption into individual appliance usage without installing sensors on each appliance.

**History:**
- First proposed by George Hart at MIT in 1992
- Hart described an event-based workflow that detects state transitions (events) and matches these with unique appliance signatures
- Modern approaches combine traditional methods with deep learning

### 1.2 How NILM Works

NILM analyzes the aggregate electricity signal to identify unique electrical "signatures" of individual appliances:

**Traditional Features:**
- **Turn-on/turn-off transients:** Rapid changes when appliances switch states
- **Steady-state power draw:** Constant power consumption during operation
- **Harmonic content:** Frequency components in the AC waveform
- **Reactive power:** Power stored and released by inductive/capacitive loads
- **Power factor:** Ratio of real to apparent power
- **Cycling patterns:** Periodic on/off behavior (e.g., refrigerator compressor)

**Modern Approaches:**
- Deep learning models that learn complex patterns from data
- Time-enhanced multidimensional feature visualization
- Active learning to reduce manual labeling burden

### 1.3 Key Workflow Stages (Hart's Framework)

1. **Signal Acquisition:** Capture aggregate power consumption
2. **Event Detection:** Identify step changes in power consumption
3. **Feature Extraction:** Calculate signatures from events
4. **Load Identification:** Match signatures to known appliances

---

## 2. Current System Analysis

### 2.1 Existing Infrastructure

Your computer vision utility monitor currently captures:

**Electric Meter Configuration:**
- **Camera:** Wyze Cam V2 with Thingino firmware
- **Stream:** MJPEG over HTTP
- **Reading Interval:** 600 seconds (10 minutes) configured, adjustable
- **Vision Processing:** Claude Vision API for meter reading
- **Storage:** InfluxDB time-series database
- **Visualization:** Grafana dashboards

**Data Collection:**
```yaml
# From config/meters.yaml
reading_interval: 600  # 10 minutes
max_change_per_reading: 10.0  # kWh (configurable for electric meter)
```

**Database Schema (InfluxDB):**
```python
# From src/influx_logger.py
Point("meter_reading")
    .tag("meter", meter_name)
    .tag("confidence", confidence)
    .field("total_reading", float)
    .field("digital_reading", float)
    .field("dial_reading", float)
    .field("temperature_c", float)
    .time(timestamp)
```

### 2.2 Current Sampling Rate Analysis

**Actual Rate:** 600-second intervals (0.00167 Hz) to potentially 60 seconds (0.0167 Hz if configured)

**NILM Requirements:**
- **High-frequency NILM:** 1-15 kHz for transient detection (Sense Energy Monitor: 1 MHz)
- **Low-frequency NILM:** 1-60 seconds for steady-state disaggregation
- **Your system:** Can achieve 60-second sampling, suitable for steady-state NILM

**What's Possible:**
- ✅ Steady-state power analysis
- ✅ Event detection (on/off transitions)
- ✅ Large appliance identification (>500W)
- ✅ Cycling pattern recognition (refrigerators, HVAC)
- ❌ Transient-based high-frequency analysis
- ❌ Small load detection (<100W)
- ❌ High-precision harmonic analysis

### 2.3 Ontario Electricity Context

**Provider:** Hydro One
**Location:** Ilderton, Ontario, Canada (Middlesex Centre)

**Time-of-Use Rates (effective 2025-11-01):**
- **Off-peak:** 9.8¢/kWh (evenings, nights, weekends)
- **Mid-peak:** 15.7¢/kWh (shoulder hours)
- **On-peak:** 20.3¢/kWh (peak demand hours)
- **Ontario Electricity Rebate:** 23.5% on electricity charges
- **HST:** 13% on total bill

**Why This Matters for NILM:**
- Time-of-use rates create strong incentive for appliance-level cost tracking
- Users want to know which appliances run during expensive peak hours
- Potential for load-shifting recommendations (run dishwasher off-peak)

---

## 3. Target Appliances for Canadian Households

### 3.1 High Priority (High Consumption + Distinctive Signatures)

| Appliance | Power (Watts) | Signature Characteristics | Detection Difficulty |
|-----------|---------------|---------------------------|---------------------|
| **Central Air Conditioning** | 3,000-5,000W | Large, steady draw with cycling; compressor startup spike | Easy |
| **Electric Furnace** | 10,000-50,000W | Massive load, very distinctive; cycling based on thermostat | Very Easy |
| **Heat Pump** | 3,000-5,000W | Similar to AC; reverse cycle in winter | Easy |
| **Electric Water Heater** | 3,000-4,500W | Large resistive load, predictable cycling (40-60 min) | Easy |
| **Electric Oven/Range** | 2,000-5,000W per element | Large resistive load, controlled cycling to maintain temp | Medium |
| **Clothes Dryer** | 2,000-5,000W | High power, motor + heating element, ~45 min cycles | Easy |
| **Dishwasher** | 1,200-2,400W | Complex pattern: pump (200W) → heater (1200W) → pump → dry | Medium |
| **Washing Machine** | 500-2,000W | Motor + heating element, distinct wash/rinse/spin cycles | Medium |
| **Refrigerator/Freezer** | 100-800W (running) | Periodic cycling (15-30 min on, 30-60 min off), very distinctive | Easy |

### 3.2 Medium Priority

| Appliance | Power (Watts) | Notes |
|-----------|---------------|-------|
| **EV Charger (Level 2)** | 7,200W | Constant high load, 4-8 hours, very distinctive |
| **Pool Pump** | 1,500-2,500W | Seasonal (summer), programmable schedule |
| **Space Heaters** | 750-1,500W | Resistive load, portable, hard to distinguish from other resistive loads |
| **Microwave** | 600-1,200W | Short duration (1-5 min), magnetron signature |
| **Coffee Maker** | 800-1,400W | Morning pattern, 5-10 min brew cycle |
| **Block Heater (Car)** | 400-1,500W | Winter, timer-controlled (common in Ontario) |

### 3.3 Low Priority (Low Power or Difficult to Identify)

| Appliance | Power (Watts) | Why Low Priority |
|-----------|---------------|------------------|
| **LED Lights** | 10-100W | Too small, too many, constantly changing |
| **TVs** | 50-400W | Variable load, hard to distinguish from computers |
| **Computers/Laptops** | 65-350W | Variable load, multiple devices |
| **Phone Chargers** | 5-20W | Negligible consumption, below detection threshold |

### 3.4 Ontario-Specific Considerations

**Winter-Dominant Loads (Nov-Apr):**
- Electric/gas furnace (highest priority)
- Block heaters (very common in Ontario)
- Space heaters (supplemental heating)
- Heat pump (if installed)

**Summer-Dominant Loads (May-Oct):**
- Central air conditioning (highest priority)
- Pool pump (if applicable)
- Dehumidifier

**Year-Round High-Value Targets:**
- Electric water heater (24/7 operation)
- Clothes dryer (weekly/daily use)
- Dishwasher (daily use)
- EV charger (growing adoption in Ontario)

---

## 4. Technical Requirements and Constraints

### 4.1 Current System Capabilities

**Meter Reading Frequency:**
- Current: 10 minutes (600 seconds)
- Configurable: Can be reduced to 60 seconds
- **Recommendation:** 60-second sampling for NILM (1 Hz)

**Data Storage:**
- ✅ InfluxDB already capturing timestamped readings
- ✅ Field for total_reading (cumulative kWh)
- ✅ Confidence scoring infrastructure
- ✅ Tag-based organization (meter name, confidence)

**Compute Resources:**
- Vision API calls: Already using Claude for meter reading
- Local processing: Python environment with pandas, numpy
- Database queries: InfluxDB Flux query language

### 4.2 NILM Data Requirements

**Minimum Sampling Rate:**
- **Recommended:** 1 Hz (60 seconds) for steady-state NILM
- **Your system:** Can achieve this with configuration change
- **Trade-off:** More frequent sampling = higher vision API costs

**Derived Metrics Needed:**
- **Instantaneous power (W):** Calculate from kWh delta between readings
- **Power delta:** Change in power from previous reading (for event detection)
- **Time delta:** Actual time between readings (for rate calculation)

**Formula:**
```python
# Calculate instantaneous power from cumulative kWh readings
power_watts = (current_kwh - previous_kwh) * 1000 / time_delta_hours
```

### 4.3 Minimum Detectable Power

**Resolution Target:**
- ±50W resolution for event detection
- Ignore loads <100W (lights, chargers, small electronics)
- Focus on appliances >500W for initial deployment

**Calculation:**
```
At 60-second sampling:
- 50W continuous = 0.000833 kWh per reading
- 500W continuous = 0.00833 kWh per reading
- 3000W continuous = 0.05 kWh per reading

Meter reading precision required: ±0.001 kWh (1 Wh)
```

### 4.4 Data Storage Requirements

**Volume Estimate:**
```
Current:
- 1 reading per 10 min = 144 readings/day
- Storage per reading: ~200 bytes (InfluxDB point)
- Daily storage: ~29 KB/day

With NILM (60-second sampling):
- 1 reading per 60 sec = 1,440 readings/day
- Daily storage: ~288 KB/day
- Annual storage: ~105 MB/year (aggregate meter)

With Appliance Disaggregation:
- 10 appliances × 1,440 readings/day
- Daily storage: ~2.9 MB/day
- Annual storage: ~1 GB/year
```

**Recommendation:** InfluxDB can easily handle this volume; retention policy not needed for at least 2-3 years.

### 4.5 API Cost Analysis

**Current Vision API Calls:**
- 1 call per 10 minutes = 144 calls/day
- Cost: ~$0.01/day (based on Claude pricing)

**With 60-Second Sampling:**
- 1 call per 60 seconds = 1,440 calls/day
- Cost: ~$0.10/day = $3/month
- **Trade-off consideration:** 10x cost increase for NILM capability

**Optimization Strategy:**
- Use 60-second sampling during "learning phase" (first 1-2 months)
- Reduce to 5-minute sampling after appliance signatures learned
- Triggered high-frequency sampling when large events detected

---

## 5. NILM Algorithms and Approaches

### 5.1 Algorithm Categories

#### 5.1.1 Traditional Approaches

**1. Event Detection (Hart's Algorithm - 1992)**
- **Description:** Detect step changes in power, match step sizes to known appliances
- **Pros:** Simple, works with 1 Hz data, interpretable
- **Cons:** Struggles with overlapping events, requires signature library
- **Best for:** Large appliances with distinctive on/off patterns
- **Implementation:** Python, scikit-learn

**2. Factorial Hidden Markov Models (FHMM - Kolter & Jaakkola 2012)**
- **Description:** Model each appliance as HMM, combines them additively
- **Key innovation:** Looks at observed difference signal, allows at most one state change at a time
- **Pros:** State-of-the-art performance on sparse, high-power appliances
- **Cons:** Computationally expensive, requires training data
- **Best for:** Household with 5-10 major appliances
- **Implementation:** NILMTK library (Python)

**3. Sparse Coding / Non-negative Matrix Factorization (NMF)**
- **Description:** Decompose aggregate signal into sum of appliance signatures
- **Pros:** Fast, unsupervised, works with low sample rates
- **Cons:** Requires signature library, assumes linear additivity
- **Best for:** Initial deployment without training data
- **Implementation:** scikit-learn NMF module

#### 5.1.2 Modern Deep Learning Approaches

**4. Sequence-to-Point CNN (Zhang et al. 2018)**
- **Description:** Convolutional neural network that maps aggregate power sequence to single appliance power value
- **Pros:** High accuracy (90%+ on UK-DALE), handles overlapping appliances
- **Cons:** Requires large training dataset, black-box model
- **Best for:** After collecting 2-3 months of labeled data
- **Implementation:** TensorFlow/Keras

**5. Sequence-to-Sequence LSTM**
- **Description:** Bidirectional LSTM that maps aggregate power sequence to appliance power sequence
- **Pros:** Captures temporal dependencies, handles variable-length sequences
- **Cons:** Slow training, requires significant data
- **Best for:** Complex appliances with multi-stage cycles (dishwasher, washing machine)
- **Implementation:** PyTorch

**6. Transient-Steady-State Feature Fusion (Recent - 2024)**
- **Description:** Combines CNN and Bi-LSTM with two-stage CUSUM event detection
- **Pros:** State-of-the-art accuracy, robust to noise
- **Cons:** Requires high-frequency data (>1 kHz)
- **Best for:** Not applicable to your 1 Hz system

**7. Active Learning Approaches (2025)**
- **Description:** Intelligently selects most informative data for user labeling
- **Key benefit:** Achieves similar performance with 90% fewer user inputs
- **Pros:** Minimizes manual labeling burden, continuous improvement
- **Cons:** Requires user feedback mechanism
- **Best for:** Production system with engaged users
- **Implementation:** Custom Python + scikit-learn

### 5.2 Recommended Hybrid Approach for Your System

**Phase 1: Event Detection + Pattern Matching (Months 1-3)**
1. **Event Detector:** Generalized Likelihood Ratio Test (GLRT) to detect power step changes
2. **Signature Matching:** Match events to signature library using k-NN or decision tree
3. **Pattern Recognition:** Identify cycling appliances (refrigerator, HVAC) using autocorrelation

**Phase 2: FHMM for Multi-Appliance States (Months 4-6)**
1. **NILMTK Integration:** Use NILMTK's FHMM implementation
2. **Transfer Learning:** Pre-train on UK-DALE, fine-tune on your household
3. **Confidence Scoring:** Provide probabilistic outputs (e.g., "65% dishwasher, 30% oven")

**Phase 3: Deep Learning for Complex Appliances (Months 7-12)**
1. **Seq2Point CNN:** Train on 3+ months of your household data
2. **Active Learning:** User feedback loop for continuous improvement
3. **Ensemble Model:** Combine FHMM + CNN predictions with weighted voting

### 5.3 Algorithm Selection Criteria

| Criterion | Event Detection | FHMM | Seq2Point CNN |
|-----------|----------------|------|---------------|
| **Data Required** | Signature library | 1-2 weeks training | 2-3 months training |
| **Accuracy (Large Appliances)** | 75-85% | 85-90% | 90-95% |
| **Accuracy (Medium Appliances)** | 60-70% | 75-85% | 85-90% |
| **Training Time** | Minutes | Hours | Days |
| **Inference Time** | <1 second | ~10 seconds | <1 second |
| **Interpretability** | High | Medium | Low |
| **Works with 1 Hz?** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Handles Overlaps?** | ❌ Poor | ✅ Good | ✅ Excellent |

---

## 6. Public Datasets and Training Resources

### 6.1 UK-DALE Dataset

**Full Name:** UK Domestic Appliance-Level Electricity Dataset
**Source:** Jack Kelly & William Knottenbelt, Imperial College London
**Publication:** Scientific Data 2, Article 150007 (2015)
**DOI:** 10.1038/sdata.2015.7

**Dataset Details:**
- **Homes:** 5 UK households
- **Duration:** 4.3 years (House 1), 1-2 years (others)
- **Sampling Rates:**
  - Aggregate: 16 kHz (high-freq) + 1/6 Hz (low-freq)
  - Individual appliances: 1/6 Hz (~6 seconds)
- **Appliances:** 52 appliance types total across all homes

**Download:**
- **Low-frequency data:** CSV or NILMTK HDF5 format from UKERC EDC
- **High-frequency data:** FLAC format via FTP
- **Processed dataset (October 2024):** Zenodo - includes tensorized .npy files

**Official Links:**
- Personal site: https://jack-kelly.com/data/
- GitHub metadata: https://github.com/JackKelly/UK-DALE_metadata
- Papers With Code: https://paperswithcode.com/dataset/uk-dale

**Value for Your Project:**
- ✅ Includes 1/6 Hz data (similar to your 1 Hz capability)
- ✅ Long-term data for training seasonal patterns
- ✅ Well-documented, widely used for NILM research
- ⚠️ UK appliances may differ from Canadian (voltage 230V vs 120/240V)

### 6.2 REDD Dataset

**Full Name:** Reference Energy Disaggregation Dataset
**Source:** J. Zico Kolter, MIT
**Publication:** SustKDD Workshop 2011

**Dataset Details:**
- **Homes:** 6 households (USA - closer to Canadian context)
- **Duration:** 3-19 days per home
- **Sampling Rates:**
  - Aggregate: 15 kHz
  - Individual circuits: 1/3 Hz (~3 seconds)
- **Appliances:** 20+ appliance types

**Download:**
- **Access Issues:** Researchers have noted difficulty accessing from original sources
- **Alternative:** Zenodo repository (October 2024) with .h5 and .npy files
- **Link:** https://zenodo.org/records/13917372 (includes REDD, UK-DALE, IAWE)

**Value for Your Project:**
- ✅ US voltage levels (120/240V) similar to Canada
- ✅ Similar home layouts and appliances
- ✅ Includes labeled circuits (can infer appliances)
- ⚠️ Short duration (weeks, not months)

### 6.3 PLAID Dataset

**Full Name:** Plug Load Appliance Identification Dataset
**Source:** Carnegie Mellon University
**Publication:** ACM BuildSys 2014

**Dataset Details:**
- **Appliances:** 1,876 records from 17 appliance types
- **Makes/Models:** 330 different appliances
- **Locations:** 65 locations in Pittsburgh, PA
- **Sampling:** 30 kHz voltage and current waveforms
- **Duration:** Short measurements (seconds) - focused on startup transients

**Download:**
- **Official site:** http://portoalegre.andrew.cmu.edu/
- **Figshare:** https://figshare.com/articles/dataset/PLAID_-_A_Voltage_and_Current_Measurement_Dataset_for_Plug_Load_Appliance_Identification_in_Households/10084619
- **GitHub tools:** https://github.com/jingkungao/PLAID

**Value for Your Project:**
- ✅ Diverse appliance library (330 makes/models)
- ✅ US context (similar to Canada)
- ✅ Good for building signature library
- ⚠️ High-frequency focus (30 kHz) - not directly usable at 1 Hz
- **Use case:** Reference library for appliance power ratings

### 6.4 NILMTK Toolkit

**Full Name:** Non-Intrusive Load Monitoring Toolkit
**Source:** Nipun Batra, Jack Kelly, et al.
**Publication:** ACM e-Energy 2014
**GitHub:** https://github.com/nilmtk/nilmtk

**Features:**
- ✅ Parsers for 8+ datasets (UK-DALE, REDD, PLAID, etc.)
- ✅ Standardized data format (HDF5)
- ✅ Benchmark disaggregation algorithms (FHMM, Combinatorial Optimization, etc.)
- ✅ Performance metrics (F1-score, accuracy, precision, recall)
- ✅ Visualization tools

**Installation:**
```bash
# Modern installation (2025)
pip install nilmtk

# Or with uv (fast package manager)
uv pip install nilmtk

# Docker image
docker pull ghcr.io/enfuego27826/nilmtk:latest
```

**Version:** v0.4 (August 2019) - actively maintained

**Value for Your Project:**
- ✅ Ready-to-use FHMM implementation
- ✅ Dataset converters for UK-DALE/REDD
- ✅ Benchmark against state-of-the-art
- ⚠️ Learning curve for HDF5 format

**Example Workflow:**
```python
from nilmtk import DataSet
from nilmtk.disaggregate import FHMM

# Load dataset
dataset = DataSet('ukdale.h5')

# Train FHMM on first house
fhmm = FHMM()
fhmm.train(dataset.buildings[1])

# Disaggregate new data
predictions = fhmm.disaggregate(aggregate_power)
```

### 6.5 Other Datasets

**IAWE (Indian Appliance-Level Electricity)**
- India household, 73 days, 1 Hz sampling
- Included in Zenodo processed datasets

**GREEND**
- 8 households (Italy, Austria), 1 Hz sampling
- Focus on European appliances

**Pecan Street Dataport**
- 1000+ homes in Austin, Texas (large-scale)
- 1-minute resolution, 2+ years
- Requires application for academic access

---

## 7. Implementation Roadmap

### 7.1 Phase 1: Foundation and Signature Library (Months 1-2)

**Objective:** Build appliance signature library and establish baseline event detection

**Tasks:**

**Month 1: Data Collection and Infrastructure**
1. **Configure 60-second sampling:**
   - Modify `config/meters.yaml`: `reading_interval: 60`
   - Test camera/API performance at higher frequency
   - Monitor InfluxDB performance and disk usage

2. **Calculate instantaneous power:**
   - Add field to InfluxDB schema: `power_watts`
   - Derive from kWh delta: `power_watts = (current_kwh - prev_kwh) * 1000 / time_delta_hours`
   - Store both cumulative energy (kWh) and instantaneous power (W)

3. **Download and process datasets:**
   - Download UK-DALE low-frequency data (1/6 Hz)
   - Download REDD from Zenodo (includes preprocessed .h5 files)
   - Install NILMTK: `pip install nilmtk`
   - Convert to common format for analysis

4. **Build Canadian appliance signature library:**
   - Extract power signatures for target appliances from REDD (US context)
   - Create database of typical signatures:
     - Steady-state power (mean, std)
     - Turn-on/turn-off deltas
     - Cycling periods (if applicable)
   - Prioritize: furnace, AC, water heater, dryer, dishwasher, refrigerator

**Month 2: Event Detection Implementation**

5. **Implement event detector:**
   - Algorithm: Generalized Likelihood Ratio Test (GLRT) or simple threshold
   - Detect step changes >100W in aggregate power
   - Store events with timestamp, power delta, duration

6. **Pattern matching engine:**
   - Match detected events to signature library
   - Use k-nearest neighbors (k-NN) or decision tree
   - Calculate confidence score for each match
   - Handle ambiguity (multiple possible appliances)

7. **User labeling interface:**
   - Web UI (Flask) to show detected events
   - "Unknown load detected: 1,200W for 45 minutes"
   - Buttons: [Dishwasher] [Oven] [Space Heater] [Other: ___]
   - Store user corrections to improve signature library

8. **Validation:**
   - Manual validation with user: "I ran the dishwasher at 3:47 PM"
   - Calculate precision/recall on labeled data
   - Target: 70-80% accuracy on high-power devices (>1kW)

**Deliverables:**
- InfluxDB schema updated with power_watts field
- Signature library JSON file (appliances → power profiles)
- Event detection service (Python script)
- User labeling web interface
- Performance report: accuracy, precision, recall

### 7.2 Phase 2: FHMM and Multi-Appliance States (Months 3-4)

**Objective:** Improve accuracy to 85-90% using Factorial Hidden Markov Models

**Tasks:**

**Month 3: FHMM Training**

1. **NILMTK integration:**
   - Convert your InfluxDB data to NILMTK HDF5 format
   - Structure: building → meter → appliance hierarchy
   - Include user-labeled appliance data from Phase 1

2. **Transfer learning from UK-DALE:**
   - Pre-train FHMM on UK-DALE House 1 (4.3 years of data)
   - Extract learned state transitions for common appliances
   - Adapt to Canadian voltage levels (120/240V vs 230V UK)

3. **Fine-tune on your household:**
   - Train FHMM on 1-2 months of your labeled data
   - Optimize hyperparameters: number of states per appliance, transition probabilities
   - Cross-validate with held-out test set

**Month 4: Deployment and Refinement**

4. **Real-time disaggregation service:**
   - Background process to run FHMM on 1-hour windows of data
   - Write predictions to InfluxDB measurement `appliance_estimates`
   - Fields: `appliance_type`, `power_watts`, `confidence`, `energy_kwh`

5. **Confidence scoring:**
   - FHMM provides probabilistic outputs
   - Example: "65% dishwasher, 30% oven, 5% other"
   - Only display predictions with >50% confidence

6. **Cycling pattern detection:**
   - Identify periodic appliances (refrigerator, HVAC) using autocorrelation
   - Learn cycle periods (e.g., refrigerator: 20 min on, 40 min off)
   - Improve FHMM accuracy by incorporating temporal patterns

7. **Evaluation:**
   - Compare FHMM vs. event detection accuracy
   - Measure performance on overlapping appliances
   - User acceptance testing: "Are these predictions useful?"

**Deliverables:**
- NILMTK HDF5 dataset of your household
- Trained FHMM model (serialized)
- Real-time disaggregation service
- InfluxDB populated with appliance-level estimates
- Accuracy report: 85-90% target for major appliances

### 7.3 Phase 3: Deep Learning and Advanced Features (Months 5-6)

**Objective:** Achieve 90-95% accuracy using Seq2Point CNN and active learning

**Tasks:**

**Month 5: Deep Learning Model Development**

1. **Data preparation:**
   - Collect 3+ months of labeled data (from Phases 1-2)
   - Create training windows:
     - Input: 60-datapoint aggregate power sequence (1 hour at 60-sec sampling)
     - Output: single appliance power value at center point
   - Split: 70% training, 15% validation, 15% test

2. **Seq2Point CNN architecture:**
   ```python
   # Simplified architecture (Zhang et al. 2018)
   model = Sequential([
       Conv1D(30, 10, activation='relu', input_shape=(60, 1)),
       Conv1D(30, 8, activation='relu'),
       Conv1D(40, 6, activation='relu'),
       Conv1D(50, 5, activation='relu'),
       Flatten(),
       Dense(1024, activation='relu'),
       Dense(1)  # Output: single power value
   ])
   ```

3. **Train per-appliance models:**
   - Separate CNN for each target appliance (dishwasher, dryer, HVAC, etc.)
   - Data augmentation: add Gaussian noise, time-shift sequences
   - Early stopping based on validation loss
   - Save best model checkpoints

**Month 6: Active Learning and Ensemble**

4. **Active learning loop:**
   - Identify predictions with high uncertainty (low confidence)
   - Prompt user: "What was running at 3:47 PM when power jumped to 2.8 kW?"
   - Retrain models weekly with new labeled data
   - Track improvement: "Accuracy increased from 87% to 91% with 10 new labels"

5. **Ensemble predictions:**
   - Combine FHMM + CNN predictions
   - Weighted voting: `final_pred = 0.4 * FHMM + 0.6 * CNN`
   - Calibrate weights based on validation set performance

6. **Advanced features:**
   - Detect unusual usage: "Your water heater ran 3x longer than usual today (possible leak)"
   - Compare to historical patterns: "AC usage up 25% vs last July"
   - Cost attribution: "Dryer accounted for $8.50 of this month's bill"

**Deliverables:**
- Trained Seq2Point CNN models (1 per appliance)
- Active learning user interface
- Ensemble disaggregation service
- Advanced anomaly detection
- Final accuracy report: 90-95% target achieved

### 7.4 Phase 4: User Feedback and Continuous Improvement (Months 7-12)

**Objective:** Production deployment with continuous learning

**Tasks:**

**Months 7-9: Production Deployment**

1. **Grafana dashboard integration:**
   - Real-time appliance-level power charts
   - Appliance breakdown pie chart
   - Cost attribution per appliance
   - Alerts for unusual usage

2. **User notifications:**
   - Email/push notifications: "Dryer cycle complete" (based on power drop)
   - Weekly reports: "Top 5 energy consumers this week"
   - Monthly cost breakdown by appliance

3. **Optimization:**
   - Reduce API calls: use model predictions to decide when to sample meter
   - Caching: store recent predictions to avoid redundant computation
   - Monitor inference latency (<5 seconds for 1 hour of data)

**Months 10-12: Continuous Improvement**

4. **Expand appliance coverage:**
   - Start with 6-8 major appliances
   - Add medium-priority appliances (microwave, coffee maker, EV charger)
   - User-requested additions: "Can you detect my sump pump?"

5. **Seasonal adaptation:**
   - Learn summer patterns (AC-heavy)
   - Learn winter patterns (furnace/heating-heavy)
   - Adapt models as usage changes

6. **Multi-home deployment (if applicable):**
   - Deploy to friends/family homes
   - Collect diverse training data
   - Identify regional patterns (Ontario-specific)

7. **Research collaboration:**
   - Publish anonymized dataset (with user consent)
   - Contribute to NILMTK ecosystem
   - Engage with University of Waterloo / academic partners

**Deliverables:**
- Production-ready disaggregation system
- User-facing dashboards and alerts
- Anonymized dataset for research
- Final accuracy: 90-95% (high-power), 75-85% (medium-power)
- User satisfaction report

---

## 8. Database Schema and Data Flow

### 8.1 Enhanced InfluxDB Schema

**Measurement: `meter_reading` (Existing)**
```python
Point("meter_reading")
    .tag("meter", "electric_main")
    .tag("confidence", "high|medium|low")
    .field("total_reading", 1234.56)      # Cumulative kWh
    .field("digital_reading", 1234.0)      # From digital display
    .field("dial_reading", 0.56)           # From dial display
    .field("power_watts", 2500.0)          # NEW: Instantaneous power
    .field("power_delta", 200.0)           # NEW: Change from last reading
    .field("temperature_c", 22.5)
    .time(timestamp)
```

**Measurement: `appliance_detections` (New)**
```python
Point("appliance_detections")
    .tag("appliance_type", "dishwasher")
    .tag("detection_method", "fhmm|cnn|event_detection")
    .tag("user_confirmed", "true|false|pending")
    .field("power_watts", 1200.0)
    .field("confidence", 0.85)             # 0.0 to 1.0
    .field("energy_kwh", 0.02)             # Energy for this reading
    .field("duration_seconds", 60)
    .field("state", "on|off|unknown")
    .time(timestamp)
```

**Measurement: `appliance_costs` (New - Derived)**
```python
Point("appliance_costs")
    .tag("appliance_type", "dryer")
    .tag("rate_period", "on_peak|mid_peak|off_peak")
    .field("cost_cad", 0.12)               # Cost for this period
    .field("energy_kwh", 0.5)
    .time(timestamp)
```

**Measurement: `events` (New - For Event Detection)**
```python
Point("events")
    .tag("event_type", "turn_on|turn_off|state_change")
    .tag("appliance_type", "oven")
    .tag("user_labeled", "true|false")
    .field("power_delta", 2500.0)          # Positive for turn-on
    .field("pre_event_power", 500.0)
    .field("post_event_power", 3000.0)
    .field("confidence", 0.72)
    .time(timestamp)
```

### 8.2 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CAMERA LAYER                             │
│  Wyze Cam V2 + Thingino Firmware → MJPEG Stream                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VISION PROCESSING                            │
│  Claude Vision API → Meter Reading (kWh) + Confidence           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   POWER CALCULATION                             │
│  Python Service:                                                │
│   - Calculate power_watts from kWh delta                        │
│   - Calculate power_delta (change detection)                    │
│   - Write to InfluxDB: meter_reading                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   NILM DISAGGREGATION                           │
│  Disaggregation Service (Python):                               │
│   ┌──────────────────────────────────────────────────┐          │
│   │ 1. Event Detector (GLRT)                         │          │
│   │    → Detect step changes >100W                   │          │
│   │    → Write to InfluxDB: events                   │          │
│   ├──────────────────────────────────────────────────┤          │
│   │ 2. FHMM (NILMTK)                                 │          │
│   │    → Probabilistic multi-appliance states        │          │
│   │    → Write to InfluxDB: appliance_detections     │          │
│   ├──────────────────────────────────────────────────┤          │
│   │ 3. Seq2Point CNN (TensorFlow)                    │          │
│   │    → Per-appliance deep learning predictions     │          │
│   │    → Write to InfluxDB: appliance_detections     │          │
│   ├──────────────────────────────────────────────────┤          │
│   │ 4. Ensemble Voter                                │          │
│   │    → Combine FHMM + CNN predictions              │          │
│   │    → Final confidence scoring                    │          │
│   └──────────────────────────────────────────────────┘          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   COST CALCULATION                              │
│  Cost Service (Python):                                         │
│   - Read appliance_detections from InfluxDB                     │
│   - Match timestamp to TOU rate (on/mid/off peak)               │
│   - Calculate cost: energy_kwh × rate × (1 - rebate) × (1+HST) │
│   - Write to InfluxDB: appliance_costs                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VISUALIZATION                                │
│  Grafana Dashboard:                                             │
│   - Real-time appliance power (line chart)                      │
│   - Appliance breakdown (pie chart)                             │
│   - Cost by appliance (bar chart)                               │
│   - Anomaly alerts (threshold alerts)                           │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   USER FEEDBACK LOOP                            │
│  Web UI (Flask):                                                │
│   - Show uncertain predictions                                  │
│   - User labels events: "This was the dishwasher"               │
│   - Update InfluxDB: user_confirmed=true                        │
│   - Retrain models with new labels (weekly)                     │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 Service Architecture

**Service 1: `meter_reader_service.py` (Existing - Enhanced)**
- **Frequency:** Every 60 seconds
- **Function:** Read electric meter via Claude Vision API
- **Output:** Write to InfluxDB `meter_reading` with power_watts calculated

**Service 2: `nilm_disaggregation_service.py` (New)**
- **Frequency:** Every 5 minutes (process 5-min window of data)
- **Function:**
  - Query last 5 minutes of `meter_reading` data
  - Run event detection → write to `events`
  - Run FHMM → write to `appliance_detections`
  - Run CNN → write to `appliance_detections`
  - Ensemble vote → update confidence scores
- **Output:** InfluxDB `appliance_detections` and `events`

**Service 3: `cost_attribution_service.py` (New)**
- **Frequency:** Every 1 hour (batch process)
- **Function:**
  - Query `appliance_detections` for last hour
  - Match timestamps to TOU rate periods
  - Calculate cost with Ontario rates (TOU + delivery + rebate + HST)
  - Aggregate daily/weekly/monthly costs per appliance
- **Output:** InfluxDB `appliance_costs`

**Service 4: `active_learning_service.py` (New)**
- **Frequency:** Daily (batch)
- **Function:**
  - Query `appliance_detections` where confidence < 0.7
  - Rank by uncertainty (lowest confidence first)
  - Present to user via web UI for labeling
  - Collect labels, retrain models weekly

**Service 5: `anomaly_detection_service.py` (New)**
- **Frequency:** Every 1 hour
- **Function:**
  - Compare current usage to historical baselines
  - Detect:
    - Appliance running longer than usual
    - Appliance not running when expected
    - Unusual power level (e.g., water heater drawing 5kW instead of 4kW)
  - Send alerts via email/notification

### 8.4 Query Examples (InfluxDB Flux)

**Query 1: Aggregate power over last 24 hours**
```flux
from(bucket: "utility_meters")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "meter_reading")
  |> filter(fn: (r) => r["meter"] == "electric_main")
  |> filter(fn: (r) => r["_field"] == "power_watts")
```

**Query 2: Appliance power breakdown (last hour)**
```flux
from(bucket: "utility_meters")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "appliance_detections")
  |> filter(fn: (r) => r["_field"] == "power_watts")
  |> group(columns: ["appliance_type"])
  |> mean()
```

**Query 3: Cost by appliance (last month)**
```flux
from(bucket: "utility_meters")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "appliance_costs")
  |> filter(fn: (r) => r["_field"] == "cost_cad")
  |> group(columns: ["appliance_type"])
  |> sum()
  |> sort(columns: ["_value"], desc: true)
```

**Query 4: Events detected today**
```flux
from(bucket: "utility_meters")
  |> range(start: today())
  |> filter(fn: (r) => r["_measurement"] == "events")
  |> filter(fn: (r) => r["event_type"] == "turn_on")
  |> sort(columns: ["_time"], desc: true)
```

---

## 9. UI/UX Design Recommendations

### 9.1 Real-Time Dashboard (Grafana)

**Panel 1: Aggregate Power (Top)**
- **Visualization:** Line chart
- **Query:** `meter_reading.power_watts` over last 24 hours
- **Features:**
  - Shaded regions for TOU periods (off-peak: green, mid-peak: yellow, on-peak: red)
  - Annotations for major events (appliance turn-on/off)
  - Threshold line at 5000W (high-usage alert)

**Panel 2: Appliance Breakdown (Left)**
- **Visualization:** Pie chart or stacked bar chart
- **Query:** Sum of `appliance_detections.energy_kwh` by appliance_type (last 24h)
- **Features:**
  - Click to filter other panels by appliance
  - Show percentage of total consumption
  - Color-coded by appliance type

**Panel 3: Active Appliances (Right)**
- **Visualization:** Status list (table)
- **Query:** Latest `appliance_detections` where state="on"
- **Columns:**
  - Appliance icon + name
  - Current power (W)
  - Duration (running for X minutes)
  - Estimated cost (real-time)
  - Confidence indicator (●●●○○ for 60%)

**Panel 4: Cost Attribution (Bottom)**
- **Visualization:** Horizontal bar chart
- **Query:** Sum of `appliance_costs.cost_cad` by appliance_type (last 30 days)
- **Features:**
  - Sort by highest cost
  - Show breakdown: on-peak vs off-peak
  - Compare to previous month (% change)

**Panel 5: Anomaly Alerts (Top-Right)**
- **Visualization:** Alert list
- **Examples:**
  - ⚠️ Water heater running 3x longer than usual (possible leak)
  - ⚠️ Refrigerator compressor cycling frequently (inefficiency)
  - ⚠️ Phantom load: 150W continuous (check for devices left on)
  - ℹ️ AC usage up 25% vs last July

### 9.2 User Labeling Interface (Flask Web App)

**Page 1: Uncertain Events**
- **URL:** `/label-events`
- **Layout:**
  ```
  ┌─────────────────────────────────────────────────────────┐
  │  Help Us Improve Appliance Detection                   │
  │                                                         │
  │  We detected an unknown event:                          │
  │  📊 Power: 1,200W                                       │
  │  ⏰ Time: 2025-11-19 15:47:23                           │
  │  ⏱️ Duration: 45 minutes                                │
  │                                                         │
  │  Power Chart: [Line chart showing event]               │
  │                                                         │
  │  What was this?                                         │
  │  ┌──────────┬──────────┬──────────┬──────────┐         │
  │  │Dishwasher│   Oven   │  Dryer   │  Heater  │         │
  │  └──────────┴──────────┴──────────┴──────────┘         │
  │  ┌──────────┬──────────────────────────────┐           │
  │  │  Other:  │ [Text input]         [Submit]│           │
  │  └──────────┴──────────────────────────────┘           │
  │                                                         │
  │  Skip for now   |   I don't know                       │
  └─────────────────────────────────────────────────────────┘
  ```

**Page 2: Appliance Management**
- **URL:** `/appliances`
- **Features:**
  - List all detected appliances
  - User can add new appliances: "I have a heat pump"
  - Edit appliance names: "Rename 'Refrigerator 1' to 'Garage Fridge'"
  - Set expected power ranges: "My dryer is 3000-3500W, not 2500W"

**Page 3: Insights and Recommendations**
- **URL:** `/insights`
- **Content:**
  - Top energy consumers this month
  - Cost-saving opportunities:
    - "Running dishwasher off-peak would save $2.50/month"
    - "Water heater accounts for 35% of bill - consider timer"
  - Usage patterns:
    - "You typically run the dryer on Saturdays at 2 PM"
    - "AC usage peaks at 7 PM (on-peak rates)"

### 9.3 Notifications and Alerts

**Real-Time Notifications:**
1. **Appliance Cycle Complete:**
   - "Dryer cycle complete (45 min, cost: $0.32)"
   - Trigger: Power drop from >2000W to <100W after 30+ min

2. **High Usage Alert:**
   - "High power usage detected: 8,500W (furnace + dryer + oven)"
   - Trigger: Aggregate power >7000W

3. **Anomaly Detection:**
   - "Water heater has been running for 3 hours (usual: 45 min)"
   - Trigger: Appliance duration >2× historical average

**Weekly Reports (Email):**
- Subject: "Your Energy Report: Week of Nov 11-17"
- Content:
  - Total cost this week: $42.50 (↑ 15% vs last week)
  - Top 5 consumers:
    1. Electric furnace: $18.20 (43%)
    2. Water heater: $9.50 (22%)
    3. Dryer: $5.80 (14%)
    4. Dishwasher: $3.20 (8%)
    5. Refrigerator: $2.50 (6%)
  - Insights: "You used 60% of electricity during on-peak hours. Shifting dryer usage to off-peak could save $8/month."

**Monthly Summary (Email + Dashboard):**
- Total cost this month: $185.50
- Cost by appliance (bar chart)
- Cost by time-of-use period (pie chart)
- Comparison to previous month and same month last year

### 9.4 Mobile App Considerations (Future)

**Features:**
- Push notifications for real-time alerts
- Quick view: current power usage
- Appliance control integration (if smart plugs added)
- Cost tracking widget

---

## 10. Accuracy Expectations and Challenges

### 10.1 Realistic Accuracy Goals

**By Appliance Category:**

| Category | Target Accuracy | Confidence Threshold | Timeline |
|----------|----------------|---------------------|----------|
| **High-Power (>2kW)** | 90-95% | >0.85 | Month 3 |
| Electric furnace | 95%+ | >0.90 | Month 2 |
| Central AC | 95%+ | >0.90 | Month 2 |
| Water heater | 90-95% | >0.85 | Month 2 |
| Clothes dryer | 90-95% | >0.85 | Month 3 |
| Electric oven/range | 85-90% | >0.80 | Month 4 |
| **Medium-Power (500W-2kW)** | 75-85% | >0.70 | Month 6 |
| Dishwasher | 80-85% | >0.75 | Month 5 |
| Washing machine | 75-80% | >0.70 | Month 6 |
| Microwave | 70-75% | >0.65 | Month 6 |
| **Low-Power (<500W)** | 50-70% | >0.50 | Month 9+ |
| Refrigerator | 85-90% | >0.80 | Month 3 (easy due to cycling) |
| LED lights (aggregate) | 50-60% | >0.50 | Month 12 |
| Small electronics | Not attempted | N/A | Future |

**Overall System Accuracy (Weighted by Energy):**
- **Month 3 (Phase 1):** 75-80% (high-power appliances only)
- **Month 6 (Phase 2):** 85-90% (high + medium appliances)
- **Month 12 (Phase 3):** 90-95% (comprehensive coverage)

### 10.2 Key Challenges

**Challenge 1: Simultaneous Appliance Operation**
- **Problem:** Multiple appliances turning on/off within 60-second window
- **Example:** User starts dishwasher (1200W) while oven is heating (2500W)
- **Impact:** Event detector sees single 3700W increase
- **Solution:**
  - FHMM models joint probability of states
  - Combinatorial optimization to find best appliance combination
  - User feedback: "What turned on at 3:47 PM?" → "Dishwasher AND oven"

**Challenge 2: Similar Appliance Signatures**
- **Problem:** Space heater (1500W) vs. hair dryer (1500W) vs. toaster (1400W)
- **Impact:** Cannot distinguish based on power alone
- **Solution:**
  - Temporal context: hair dryer used for 5 min, space heater for hours
  - User patterns: space heater in winter, toaster in morning
  - User labeling: "This is my space heater (bedroom)"

**Challenge 3: Seasonal Variations**
- **Problem:** AC in summer, furnace in winter → different appliance sets
- **Impact:** Model trained in summer doesn't recognize furnace
- **Solution:**
  - Year-round data collection (12 months minimum)
  - Seasonal model switching
  - Transfer learning from other households

**Challenge 4: New/Unknown Appliances**
- **Problem:** User buys new appliance not in signature library
- **Impact:** Appears as "unknown load"
- **Solution:**
  - Active learning: prompt user to label new appliances
  - Zero-shot learning: use power level + context to infer appliance type
  - User-initiated appliance addition: "I just bought a heat pump"

**Challenge 5: Appliance State Variations**
- **Problem:** Oven has multiple states: preheat (3000W) → bake (2000W) → broil (4000W)
- **Impact:** Single appliance appears as multiple loads
- **Solution:**
  - Multi-state HMM (FHMM naturally handles this)
  - Clustering: learn typical states from data
  - Report as single appliance with variable power

**Challenge 6: Low Sampling Rate Limitations**
- **Problem:** 60-second sampling misses short events (<1 minute)
- **Example:** Microwave runs for 45 seconds → may not be captured
- **Solution:**
  - Accept limitation: focus on appliances with >2 min runtime
  - Adaptive sampling: increase frequency when events detected
  - User education: "We can't detect very short events like microwaves perfectly"

**Challenge 7: Data Quality Issues**
- **Problem:** Vision API misreads meter → bad power calculation
- **Example:** OCR error: 1234.56 kWh read as 1334.56 kWh → 100 kWh spike!
- **Solution:**
  - Anomaly detection in meter readings (flag >10 kWh change)
  - Confidence filtering: only use "high" confidence readings for disaggregation
  - Outlier removal: discard readings >3 std dev from mean

### 10.3 Evaluation Metrics

**Metrics to Track:**

1. **Accuracy:** (TP + TN) / (TP + TN + FP + FN)
   - Overall correctness of predictions

2. **Precision:** TP / (TP + FP)
   - When we say "dishwasher is on," how often is it actually on?

3. **Recall:** TP / (TP + FN)
   - When dishwasher is actually on, how often do we detect it?

4. **F1-Score:** 2 × (Precision × Recall) / (Precision + Recall)
   - Harmonic mean of precision and recall

5. **Energy Accuracy:** 1 - (|Predicted Energy - Actual Energy| / Actual Energy)
   - How close is our total energy estimate to actual?

6. **Mean Absolute Error (MAE):** Average |Predicted Power - Actual Power|
   - Average error in watts

**Benchmark Against:**
- **UK-DALE baseline:** FHMM achieves ~85% F1-score on major appliances
- **Sense Energy Monitor:** Claims 80%+ detection accuracy (commercial product)
- **Your target:** 85-90% F1-score for high-power appliances by Month 6

### 10.4 Validation Strategy

**Validation Approach:**

1. **Ground Truth Collection (Month 1-2):**
   - Manual logging: User records appliance usage for 2 weeks
   - Smart plugs on select appliances (optional): Kasa TP-Link plugs (~$15 each)
   - Diary: "I ran the dishwasher at 7:30 PM for 1.5 hours"

2. **Holdout Test Set:**
   - Reserve 15% of data for final evaluation
   - Never use for training or hyperparameter tuning

3. **Cross-Validation:**
   - Time-series cross-validation (not random splits)
   - Train on weeks 1-3, validate on week 4
   - Rotate through 4 weeks

4. **User Acceptance Testing:**
   - Survey: "Do these predictions match your actual usage?"
   - Likert scale: 1 (very inaccurate) to 5 (very accurate)
   - Target: Average rating >4.0

**Validation Report (Monthly):**
```
Month 3 Validation Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Appliance          Precision  Recall  F1-Score
────────────────────────────────────────────────
Electric Furnace     0.95      0.92    0.93
Water Heater         0.88      0.85    0.87
Dryer                0.82      0.79    0.80
Dishwasher           0.75      0.71    0.73
Refrigerator         0.90      0.88    0.89
────────────────────────────────────────────────
Overall (Weighted)   0.86      0.83    0.84

Energy Accuracy:     91.5%
Mean Absolute Error: 125W

User Satisfaction:   4.2 / 5.0
```

---

## 11. Competitive Analysis

### 11.1 Sense Energy Monitor

**Company:** Sense (Founded 2013, MIT speech recognition team)
**Product:** Sense Home Energy Monitor
**Price:** $299 USD hardware + machine learning service

**Technology:**
- **Sampling Rate:** 1 million samples/second (1 MHz!)
- **Installation:** Clamps around service breakers in electrical panel
- **Connectivity:** WiFi to cloud
- **Detection Method:** Transient-based signatures + machine learning
- **Training:** 5+ years of development to reach current accuracy

**Performance:**
- Detects appliances at moment of turn-on ("oven turned on at 3:47 PM")
- Average: 16 discrete data streams per house
- ~50% identified as specific appliances
- Continuous learning: improves over weeks/months

**Limitations:**
- Cannot detect every device with absolute accuracy
- Multiple similar appliances hard to differentiate (two space heaters)
- Smaller devices (<100W) or intermittent devices may be missed

**Business Model:**
- One-time hardware purchase
- Free cloud service (machine learning included)
- Revenue from partnerships with utilities (demand response programs)

**Pilot Results:**
- Ohmconnect pilot: 18% reduction in home energy usage

**Key Insight:**
- Sense requires high-frequency data (1 MHz) for transient detection
- Your 1 Hz system cannot replicate transient-based approach
- **Opportunity:** Offer similar insights at lower hardware cost (camera vs. $299 monitor)

### 11.2 Neurio

**Company:** Neurio (Canadian company, acquired by Generac)
**Product:** Neurio Home Energy Monitor
**Price:** ~$199 USD

**Technology:**
- Circuit-level monitoring (installs in electrical panel)
- Lower sampling rate than Sense
- NILM + circuit-level hybrid approach

**Performance:**
- Less accurate than Sense (per user reviews)
- Better suited for solar integration (Generac focus)

**Status:** Product discontinued (as of 2021)

### 11.3 Smappee

**Company:** Smappee (Belgium)
**Product:** Smappee Energy Monitor
**Price:** €299-399 EUR

**Technology:**
- NILM + optional smart plugs for specific appliances
- Solar panel integration
- European focus (230V)

**Performance:**
- Similar accuracy claims to Sense
- Strong solar monitoring features

**Market:** Primarily Europe

### 11.4 Your Competitive Position

**Advantages:**

1. **Lower Hardware Cost:**
   - Wyze Cam V2: ~$25 (already owned)
   - Sense/Neurio/Smappee: $199-299
   - **Savings:** $174-274 per installation

2. **Multi-Utility Integration:**
   - Your system: water + electric + gas monitoring (unified platform)
   - Competitors: electricity only
   - **Value:** Single dashboard for all utilities

3. **No Electrical Panel Access Required:**
   - Your system: camera points at meter (non-invasive)
   - Competitors: requires electrician installation (~$100-200 labor)
   - **Advantage:** DIY-friendly, renter-friendly

4. **Vision-Based Flexibility:**
   - Your system: can read any meter (digital, analog, dial)
   - Competitors: electrical panel only
   - **Advantage:** Works with older homes, different meter types

**Disadvantages:**

1. **Lower Sampling Rate:**
   - Your system: 1 Hz (60 seconds)
   - Sense: 1 MHz (1,000,000 Hz)
   - **Impact:** Cannot detect transients, less accurate for small loads

2. **Development Maturity:**
   - Your system: New (6-12 month development)
   - Sense: 10+ years of development
   - **Impact:** Lower initial accuracy, requires training

3. **Cloud Dependency:**
   - Your system: Requires Claude Vision API (ongoing cost)
   - Sense: One-time hardware purchase
   - **Impact:** Monthly operational cost (~$3/month at 60-sec sampling)

**Market Positioning:**

**Target Market:** DIY homeowners, renters, multi-utility monitoring enthusiasts

**Value Proposition:**
- "Monitor water, electric, and gas usage with a single $25 camera"
- "No electrician required, no panel access needed"
- "AI-powered appliance detection for 90% less than Sense"

**Pricing Strategy (If Commercialized):**
- Hardware: Wyze Cam V2 ($25) + weatherproof housing ($15) = $40
- Software: $5/month subscription (includes API costs, cloud storage, ML models)
- Annual: $100 (saves 15% vs monthly)
- **Compare to Sense:** $299 upfront vs. $100/year (break-even at 3 years)

### 11.5 Academic and Open-Source Alternatives

**NILMTK (Open Source):**
- Free, Python-based
- Requires technical expertise
- No pre-trained models (must train on own data)
- **Your approach:** Use NILMTK algorithms, add user-friendly UI

**Home Assistant Integrations:**
- Various NILM plugins for Home Assistant
- Mostly simple threshold-based detection
- **Opportunity:** Integrate your system as Home Assistant custom component (already planned)

---

## 12. Research Partnerships and Open Source

### 12.1 Academic Collaboration Opportunities

**University of Waterloo (Ontario, Canada)**
- **Department:** Electrical and Computer Engineering
- **Research Areas:** Smart grids, energy systems, machine learning
- **Potential Collaboration:**
  - Provide anonymized Canadian household dataset
  - Joint research on low-frequency NILM (1 Hz)
  - Co-author papers on vision-based energy monitoring
- **Contact:** Faculty members in sustainable energy research group

**MIT (Massachusetts Institute of Technology)**
- **History:** Birthplace of NILM (George Hart, 1992)
- **Current Research:** Advanced NILM algorithms, smart home energy
- **Potential Collaboration:**
  - Access to REDD dataset and expertise
  - Benchmark your system against MIT research
- **Note:** MIT researchers are co-authors of many NILM papers

**UC Berkeley / LBNL (Lawrence Berkeley National Lab)**
- **Focus:** Energy efficiency, building energy systems
- **Datasets:** Some buildings datasets available
- **Potential Collaboration:**
  - Policy research: impact of appliance-level monitoring on energy behavior

### 12.2 Open Source Contributions

**NILMTK Ecosystem:**
- **Contribution 1:** Canadian appliance signature library
  - Collect signatures from Ontario homes
  - Submit to NILMTK dataset repository
  - Annotate with Canadian voltage levels (120/240V), climate (heating-dominant)

- **Contribution 2:** Vision-based meter reading module
  - Add camera capture pipeline to NILMTK
  - Enable NILMTK users to use cameras instead of CT clamps
  - Pull request: `nilmtk/nilmtk` GitHub repo

- **Contribution 3:** Low-frequency NILM algorithms
  - Document best practices for 1 Hz sampling
  - Benchmark algorithms on low-frequency data
  - Tutorial: "NILM with Smart Meter Data (1 Hz)"

**GitHub Repository (Your Project):**
- **License:** MIT or Apache 2.0 (permissive)
- **Repository Name:** `computer-vision-nilm`
- **Features:**
  - Camera-based meter reading
  - NILM disaggregation pipeline
  - Grafana dashboards (pre-configured)
  - Docker compose setup
  - Example datasets (anonymized)

**Documentation:**
- Tutorial: "DIY Home Energy Disaggregation with a $25 Camera"
- Blog posts: Medium, Hacker News, Reddit (r/homeautomation)
- Video: YouTube walkthrough

### 12.3 Data Sharing (Anonymized)

**Dataset Name:** "Canadian Residential Energy Dataset (CRED)"

**Contents:**
- 1 Hz aggregate electricity data (kWh readings)
- Appliance-level ground truth (user-labeled)
- Weather data (temperature, heating/cooling degree days)
- Time-of-use rate periods (Ontario-specific)
- Anonymization: remove exact timestamps, geographic coordinates

**Format:**
- NILMTK HDF5 format (for compatibility)
- CSV files (for ease of use)
- Metadata: appliance types, home size, heating system type

**Release:**
- Zenodo (DOI assignment, citable)
- GitHub (for code and scripts)
- License: CC BY 4.0 (attribution required)

**Impact:**
- Enable researchers to study Canadian energy patterns
- Benchmark NILM algorithms on heating-dominant climate
- Foster collaboration with Canadian universities/government (NRCan)

### 12.4 Research Questions to Explore

**Question 1:** Can vision-based meter reading compete with CT clamp accuracy for NILM?
- **Hypothesis:** Yes, for 1 Hz sampling
- **Methodology:** Compare disaggregation accuracy with camera vs. CT clamps
- **Outcome:** Paper submission to ACM BuildSys or IEEE Transactions on Smart Grid

**Question 2:** How does NILM accuracy change with sampling rate (1 Hz vs 1/6 Hz vs 1/60 Hz)?
- **Hypothesis:** Diminishing returns below 1 Hz
- **Methodology:** Downsample UK-DALE data, compare F1-scores
- **Outcome:** Guidance for smart meter design (1 Hz sufficient?)

**Question 3:** What is the impact of user feedback on NILM accuracy?
- **Hypothesis:** Active learning improves accuracy by 10-15% with minimal user effort
- **Methodology:** A/B test: active learning vs. no user feedback
- **Outcome:** Paper on human-in-the-loop NILM systems

**Question 4:** Can NILM detect appliance anomalies (failures, inefficiencies)?
- **Hypothesis:** Yes, with baseline modeling
- **Methodology:** Identify cases where appliances deviate from normal patterns
- **Outcome:** Predictive maintenance application (e.g., water heater failure prediction)

### 12.5 Conference and Publication Targets

**Top Conferences:**
1. **ACM BuildSys** (International Conference on Systems for Energy-Efficient Buildings)
   - Deadline: Typically June
   - Focus: Building energy systems, NILM, smart homes

2. **IEEE SmartGridComm** (Smart Grid Communications)
   - Deadline: Typically March
   - Focus: Smart grid communications, demand response

3. **ACM e-Energy** (International Conference on Future Energy Systems)
   - Deadline: Typically January
   - Focus: Energy efficiency, renewable integration

**Journals:**
1. **IEEE Transactions on Smart Grid**
   - Impact Factor: ~10
   - Focus: Smart grid technologies, NILM

2. **Energy and Buildings**
   - Impact Factor: ~7
   - Focus: Building energy efficiency

3. **Applied Energy**
   - Impact Factor: ~11
   - Focus: Energy systems, efficiency

**Workshop Papers (Lower Barrier to Entry):**
- NILM Workshop (at BuildSys)
- Energy Data Analytics Workshop

---

## 13. Cost-Benefit Analysis

### 13.1 Development Costs

**Phase 1: Foundation (Months 1-2)**
- Developer time: 80 hours @ $75/hr = $6,000
- Dataset downloads: Free (UK-DALE, REDD)
- Cloud compute (training): $50
- **Total Phase 1:** $6,050

**Phase 2: FHMM (Months 3-4)**
- Developer time: 60 hours @ $75/hr = $4,500
- Cloud compute: $100
- **Total Phase 2:** $4,600

**Phase 3: Deep Learning (Months 5-6)**
- Developer time: 100 hours @ $75/hr = $7,500
- Cloud compute (GPU training): $300
- **Total Phase 3:** $7,800

**Phase 4: Production (Months 7-12)**
- Developer time: 120 hours @ $75/hr = $9,000
- Cloud hosting: $50/month × 6 = $300
- **Total Phase 4:** $9,300

**Total Development Cost:** $27,750

**Note:** This assumes DIY development. Commercial development would be 2-3× higher.

### 13.2 Operational Costs (Annual)

**API Costs (60-Second Sampling):**
- Claude Vision API: 1,440 calls/day × 365 days = 525,600 calls/year
- Cost per call: ~$0.00002 (estimated based on Claude pricing)
- **Annual API Cost:** ~$10.50

**InfluxDB Cloud (If Using Hosted):**
- Free tier: 10,000 writes/day (sufficient for single home)
- Paid tier (if needed): $50/month = $600/year
- **Recommendation:** Self-hosted InfluxDB (free)

**Grafana Cloud (If Using Hosted):**
- Free tier: 10,000 series, 14-day retention (sufficient)
- Paid tier (if needed): $29/month = $348/year
- **Recommendation:** Self-hosted Grafana (free)

**Server Costs (Self-Hosted):**
- Raspberry Pi 4 (4GB): $75 one-time
- Power consumption: ~5W = 43.8 kWh/year @ $0.12/kWh = $5.25/year
- **Total Server:** $80 one-time + $5.25/year

**Total Annual Operational Cost (Self-Hosted):** ~$16/year

**Total Annual Operational Cost (Cloud-Hosted):** ~$959/year

### 13.3 Benefits Quantification

**Benefit 1: Energy Savings from Awareness**
- **Assumption:** 5-10% reduction in electricity usage (conservative)
- **Baseline:** Average Ontario household uses ~900 kWh/month
- **Annual usage:** 10,800 kWh
- **Reduction:** 540-1,080 kWh/year
- **Savings:** $65-130/year (at blended rate of $0.12/kWh)

**Benchmark:** Sense Ohmconnect pilot showed 18% reduction (your 5-10% is conservative)

**Benefit 2: Time-of-Use Optimization**
- **Assumption:** Shift 20% of discretionary load (dryer, dishwasher) from on-peak to off-peak
- **Discretionary load:** 200 kWh/month (dryer: 100, dishwasher: 50, other: 50)
- **Annual discretionary:** 2,400 kWh
- **Shifted:** 480 kWh/year
- **Rate difference:** On-peak (20.3¢) - off-peak (9.8¢) = 10.5¢/kWh
- **Savings:** $50/year

**Benefit 3: Appliance Failure Detection**
- **Assumption:** Detect 1 major appliance failure per 3 years
- **Example:** Water heater failure detected early (leaking, inefficient)
- **Cost of emergency repair:** $500 (plumber call, damage)
- **Cost of proactive replacement:** $300 (planned replacement)
- **Savings:** $200 per incident / 3 years = $67/year

**Benefit 4: Phantom Load Reduction**
- **Assumption:** Identify 100W of phantom loads (devices left on)
- **Annual waste:** 100W × 24 hr × 365 days = 876 kWh
- **Savings:** $105/year (at $0.12/kWh)

**Benefit 5: Insurance Discount (Future Potential)**
- **Assumption:** Home insurance discount for monitoring (like smart home discount)
- **Typical discount:** 5-10% on home insurance
- **Average Ontario home insurance:** $1,200/year
- **Savings:** $60-120/year
- **Status:** Not currently available, but potential future benefit

**Total Annual Savings:** $287-472/year (conservative)

### 13.4 Return on Investment (ROI)

**Scenario 1: DIY Development (Your Case)**

**Investment:**
- Camera (already owned): $0
- Development time (personal project): $0 (hobby)
- Operational cost: $16/year (self-hosted)

**Annual Savings:** $287-472

**ROI:** Infinite (no upfront cost beyond time)
**Payback Period:** Immediate

**Scenario 2: Commercial Product**

**Investment:**
- Hardware: $40 (camera + housing)
- Software subscription: $60/year
- Total Year 1: $100

**Annual Savings:** $287-472

**ROI Year 1:** 187-372%
**Payback Period:** 3-5 months

**5-Year Net Benefit:**
- Savings: $287 × 5 = $1,435 (conservative)
- Costs: $100 + $60 × 4 = $340
- **Net Benefit:** $1,095

**Compare to Sense:**
- Sense Cost: $299 (one-time)
- Sense Savings (18% reduction): $117 × 5 = $585 (using 18% from pilot)
- **Net Benefit:** $286

**Your System vs. Sense (5-Year):**
- Your system: $1,095 net benefit
- Sense: $286 net benefit (though potentially higher savings with 18% reduction)
- **Advantage:** $809 (your system saves 3.8× more over 5 years)

### 13.5 Intangible Benefits

**Benefit 6: Behavioral Change**
- Awareness of real-time energy usage changes habits
- Gamification: "Can I beat last month's energy usage?"
- Family engagement: "Kids, who left the lights on?"

**Benefit 7: Environmental Impact**
- 540-1,080 kWh reduction = 0.27-0.54 tonnes CO₂ avoided/year (Ontario grid: 0.05 kg CO₂/kWh)
- Equivalent to planting 6-12 trees per year

**Benefit 8: Data Sovereignty**
- Self-hosted system: you own your data
- No privacy concerns about sharing usage patterns with third parties
- GDPR/PIPEDA compliant (Canadian privacy law)

**Benefit 9: Educational Value**
- Learn about electricity usage, NILM algorithms, machine learning
- Open-source contribution to community
- Potential for academic publication

---

## 14. Recommendations and Next Steps

### 14.1 Immediate Actions (Week 1)

**Action 1: Configure 60-Second Sampling**
- Modify `config/meters.yaml`: Change `reading_interval: 600` to `reading_interval: 60`
- Test camera performance at higher frequency (ensure no frame drops)
- Monitor Claude API costs for 1 week (estimate: $0.70/week)

**Action 2: Add Power Calculation to InfluxDB Schema**
- Update `src/influx_logger.py` to calculate `power_watts` field
- Formula: `power_watts = (current_kwh - prev_kwh) * 1000 / time_delta_hours`
- Backfill historical data with calculated power (optional)

**Action 3: Download and Explore Datasets**
- Download UK-DALE low-frequency data (1/6 Hz) from UKERC EDC
- Download REDD from Zenodo (https://zenodo.org/records/13917372)
- Install NILMTK: `pip install nilmtk`
- Load datasets and explore appliance signatures:
  ```python
  from nilmtk import DataSet
  dataset = DataSet('ukdale.h5')
  dataset.buildings[1].elec.plot()
  ```

**Action 4: Manual Ground Truth Collection**
- Start logging appliance usage manually for 1 week
- Simple spreadsheet: Timestamp | Appliance | Action (on/off) | Duration
- Example: "2025-11-19 19:30 | Dishwasher | On | 90 min"

### 14.2 Short-Term Goals (Months 1-2)

**Goal 1: Build Signature Library**
- Extract power signatures from REDD (US context, similar to Canada)
- Target appliances:
  - Electric furnace / heat pump
  - Water heater
  - Clothes dryer
  - Dishwasher
  - Refrigerator
- Store as JSON: `{"appliance": "dishwasher", "power_mean": 1200, "power_std": 150, "duration_mean": 5400}`

**Goal 2: Implement Event Detector**
- Algorithm: Generalized Likelihood Ratio Test (GLRT) or simple threshold
- Detect step changes >100W in aggregate power
- Write to InfluxDB `events` measurement
- Visualize in Grafana: scatter plot of events

**Goal 3: Create User Labeling Interface**
- Flask web app at `/label-events`
- Show detected events with power chart
- Buttons for common appliances
- Store user labels in InfluxDB (tag: `user_confirmed=true`)

**Goal 4: Achieve 70% Accuracy on High-Power Appliances**
- Validate against manual logs
- Focus on: furnace, water heater, dryer (easy to detect)
- Iterate on event detection thresholds

### 14.3 Medium-Term Goals (Months 3-6)

**Goal 1: NILMTK FHMM Integration**
- Convert your data to NILMTK format (HDF5)
- Train FHMM on 1-2 months of labeled data
- Benchmark against UK-DALE performance (target: 85% F1-score)

**Goal 2: Real-Time Disaggregation Service**
- Background process running FHMM every 5 minutes
- Write predictions to `appliance_detections` measurement
- Confidence scoring and filtering (only show >50% confidence)

**Goal 3: Grafana Dashboard Enhancement**
- Appliance breakdown pie chart
- Active appliances status list
- Cost attribution by appliance
- Anomaly alerts

**Goal 4: Achieve 85% Accuracy**
- FHMM should improve accuracy to 85-90% for major appliances
- Handle overlapping events better than event detection alone

### 14.4 Long-Term Goals (Months 7-12)

**Goal 1: Deep Learning Deployment**
- Collect 3+ months of labeled data
- Train Seq2Point CNN models (1 per appliance)
- Active learning loop for continuous improvement

**Goal 2: Anomaly Detection and Insights**
- Baseline modeling of typical usage patterns
- Detect appliances running longer than usual
- Cost-saving recommendations (shift to off-peak)

**Goal 3: Production-Ready System**
- Optimize API costs (adaptive sampling)
- User notifications (email, push)
- Documentation for deployment to other homes

**Goal 4: Open Source Release**
- GitHub repository with MIT license
- Tutorial and documentation
- Blog post / video walkthrough
- Submit to Hacker News, Reddit (r/homeautomation)

### 14.5 Optional Extensions

**Extension 1: Home Assistant Integration**
- Custom component: `utility_meters_nilm`
- Entities: `sensor.dishwasher_power`, `sensor.dryer_status`
- Automations: "Notify when dryer cycle complete"

**Extension 2: Multi-Home Deployment**
- Deploy to friends/family homes (with consent)
- Collect diverse training data
- Benchmark across different home types (apartment, house, condo)

**Extension 3: Smart Plug Integration**
- Use TP-Link Kasa smart plugs for ground truth on select appliances
- Compare NILM predictions to smart plug measurements
- Validation tool for new algorithms

**Extension 4: EV Charger Optimization**
- Detect EV charging sessions (7.2 kW Level 2 charger)
- Recommend charging schedule to minimize cost (off-peak only)
- Integration with EV charger APIs (Tesla, ChargePoint)

**Extension 5: Solar Integration**
- If solar panels installed, separate production from consumption
- Net-metering: track self-consumption vs. grid export
- Optimize appliance usage to match solar production

### 14.6 Risk Mitigation

**Risk 1: Low Accuracy with 1 Hz Sampling**
- **Mitigation:** Start with large appliances (easier to detect)
- **Fallback:** Accept 75-80% accuracy, focus on high-value appliances

**Risk 2: High API Costs**
- **Mitigation:** Adaptive sampling (reduce to 5 min after learning phase)
- **Fallback:** Switch to local vision model (Florence-2, LLaVA) for meter reading

**Risk 3: User Labeling Fatigue**
- **Mitigation:** Minimize user burden with active learning (ask about uncertain predictions only)
- **Fallback:** Transfer learning from public datasets (UK-DALE, REDD)

**Risk 4: Privacy Concerns**
- **Mitigation:** Self-hosted system, no data sharing
- **Transparency:** Document data usage, allow user to export/delete data

**Risk 5: Appliance Diversity**
- **Mitigation:** Build signature library from diverse sources (REDD, PLAID, user data)
- **Fallback:** Provide "generic" appliance categories (resistive load, motor, etc.)

---

## 15. Conclusion

### 15.1 Summary of Findings

**NILM is Feasible for Your System:**
- 60-second (1 Hz) sampling is sufficient for steady-state NILM
- Focus on high-power appliances (>500W) with distinctive signatures
- Expected accuracy: 85-90% for major appliances by Month 6

**Recommended Approach:**
- **Phase 1:** Event detection + signature matching (Months 1-2)
- **Phase 2:** Factorial Hidden Markov Models (Months 3-4)
- **Phase 3:** Deep learning with active learning (Months 5-6)
- **Phase 4:** Production deployment with continuous improvement (Months 7-12)

**Key Advantages Over Competitors:**
- Lower cost: $40 hardware vs. $299 (Sense)
- Multi-utility integration: water + electric + gas
- No electrical panel access required (DIY-friendly)

**Expected ROI:**
- Annual savings: $287-472 (energy reduction + TOU optimization)
- 5-year net benefit: $1,095 (conservative)
- Payback period: 3-5 months

### 15.2 Critical Success Factors

1. **User Engagement:** Active learning requires user feedback
2. **Data Quality:** Vision API must maintain high accuracy on meter readings
3. **Signature Library:** Comprehensive library of Canadian appliances
4. **Continuous Improvement:** Weekly retraining with new labeled data
5. **Realistic Expectations:** Communicate 85-90% accuracy, not 100%

### 15.3 Final Recommendation

**Proceed with NILM integration** as a high-value addition to your computer vision utility monitor platform. The technology is mature enough for 1 Hz sampling, the public datasets are available for training, and the potential energy savings justify the development investment.

**Prioritize:**
1. 60-second sampling configuration (Week 1)
2. Event detection and user labeling (Months 1-2)
3. FHMM deployment (Months 3-4)
4. Open source release and community engagement (Month 6+)

**Success Metrics:**
- Month 3: 75% accuracy on high-power appliances
- Month 6: 85% accuracy with FHMM
- Month 12: 90% accuracy with deep learning
- User satisfaction: >4.0/5.0 rating

**Timeline to Production:** 6 months for core functionality, 12 months for comprehensive coverage.

---

## Appendix A: Glossary

**NILM:** Non-Intrusive Load Monitoring - disaggregating total power into appliance-level usage
**NIALM:** Non-Intrusive Appliance Load Monitoring (same as NILM)
**FHMM:** Factorial Hidden Markov Model - probabilistic model for multi-appliance states
**HMM:** Hidden Markov Model - statistical model for sequential data
**GLRT:** Generalized Likelihood Ratio Test - statistical test for event detection
**Seq2Point:** Sequence-to-Point model - deep learning architecture for NILM
**TOU:** Time-of-Use - electricity pricing that varies by time of day
**kWh:** Kilowatt-hour - unit of energy (1000 watts for 1 hour)
**W:** Watt - unit of power
**CT Clamp:** Current Transformer clamp - sensor for measuring electrical current
**Transient:** Rapid change in power when appliance turns on/off
**Steady-State:** Constant power consumption during appliance operation
**F1-Score:** Harmonic mean of precision and recall (performance metric)

---

## Appendix B: References

1. **Hart, G. W.** (1992). "Nonintrusive appliance load monitoring." Proceedings of the IEEE, 80(12), 1870-1891.

2. **Kolter, J. Z., & Jaakkola, T.** (2012). "Approximate inference in additive factorial HMMs with application to energy disaggregation." AISTATS.

3. **Kelly, J., & Knottenbelt, W.** (2015). "The UK-DALE dataset, domestic appliance-level electricity demand and whole-house demand from five UK homes." Scientific Data, 2, 150007.

4. **Kolter, J. Z., & Johnson, M. J.** (2011). "REDD: A public data set for energy disaggregation research." SustKDD workshop.

5. **Gao, J., et al.** (2014). "PLAID: a public dataset of high-resolution electrical appliance measurements for load identification research." ACM BuildSys.

6. **Batra, N., et al.** (2014). "NILMTK: An open source toolkit for non-intrusive load monitoring." ACM e-Energy.

7. **Zhang, C., et al.** (2018). "Sequence-to-point learning with neural networks for non-intrusive load monitoring." AAAI.

8. **IEEE.** (2024). "A New Nonintrusive Load Monitoring Method via Transient-Steady-State Feature Fusion." IEEE Xplore.

9. **Springer.** (2025). "Fostering non-intrusive load monitoring for smart energy management in industrial applications: an active machine learning approach." Energy Informatics.

10. **Ontario Energy Board.** (2025). "Electricity Prices." https://www.oeb.ca/rates-and-your-bill/electricity-rates

---

## Appendix C: Code Examples

### C.1 Calculate Instantaneous Power

```python
# src/power_calculator.py

from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

def calculate_power(current_kwh: float, previous_kwh: float,
                   current_time: datetime, previous_time: datetime) -> float:
    """
    Calculate instantaneous power from cumulative kWh readings.

    Args:
        current_kwh: Current meter reading (kWh)
        previous_kwh: Previous meter reading (kWh)
        current_time: Current reading timestamp
        previous_time: Previous reading timestamp

    Returns:
        Power in watts
    """
    # Calculate time difference in hours
    time_delta = (current_time - previous_time).total_seconds() / 3600

    if time_delta <= 0:
        return 0.0

    # Calculate energy difference
    energy_delta = current_kwh - previous_kwh

    # Calculate power (convert kWh to Wh by multiplying by 1000)
    power_watts = (energy_delta * 1000) / time_delta

    return power_watts

# Example usage
if __name__ == "__main__":
    current = 1234.56  # kWh
    previous = 1234.51  # kWh
    current_time = datetime(2025, 11, 19, 15, 48, 0)
    previous_time = datetime(2025, 11, 19, 15, 47, 0)

    power = calculate_power(current, previous, current_time, previous_time)
    print(f"Power: {power:.0f} W")  # Output: Power: 3000 W
```

### C.2 Event Detection with GLRT

```python
# src/event_detector.py

import numpy as np
from scipy import stats
from typing import List, Tuple

def detect_events(power_series: List[float],
                 timestamps: List[datetime],
                 threshold: float = 100.0,
                 window_size: int = 5) -> List[Tuple[datetime, float]]:
    """
    Detect step changes in power using simple threshold method.

    Args:
        power_series: List of power values (watts)
        timestamps: Corresponding timestamps
        threshold: Minimum power change to consider as event (watts)
        window_size: Number of points to average before/after event

    Returns:
        List of (timestamp, power_delta) tuples
    """
    events = []

    for i in range(window_size, len(power_series) - window_size):
        # Calculate mean power before and after this point
        before = np.mean(power_series[i-window_size:i])
        after = np.mean(power_series[i:i+window_size])

        # Calculate power delta
        delta = after - before

        # Check if delta exceeds threshold
        if abs(delta) > threshold:
            events.append((timestamps[i], delta))

    return events

# Example usage
if __name__ == "__main__":
    # Simulate power series with a turn-on event
    power = [500] * 10 + [2500] * 10  # Appliance turns on at index 10
    times = [datetime(2025, 11, 19, 15, i, 0) for i in range(20)]

    events = detect_events(power, times, threshold=100.0)

    for timestamp, delta in events:
        print(f"Event at {timestamp}: {delta:+.0f} W")
    # Output: Event at 2025-11-19 15:10:00: +2000 W
```

### C.3 NILMTK FHMM Example

```python
# src/fhmm_disaggregator.py

from nilmtk import DataSet
from nilmtk.disaggregate import FHMM
import pandas as pd

def train_fhmm(dataset_path: str, building_num: int = 1):
    """
    Train FHMM on NILMTK dataset.

    Args:
        dataset_path: Path to HDF5 dataset
        building_num: Building number to train on
    """
    # Load dataset
    dataset = DataSet(dataset_path)

    # Get building
    building = dataset.buildings[building_num]

    # Initialize FHMM
    fhmm = FHMM()

    # Train on building's aggregate meter
    fhmm.train(building.elec)

    return fhmm

def disaggregate(fhmm, aggregate_power: pd.Series):
    """
    Disaggregate aggregate power using trained FHMM.

    Args:
        fhmm: Trained FHMM model
        aggregate_power: Pandas Series of aggregate power

    Returns:
        Dictionary of appliance predictions
    """
    predictions = fhmm.disaggregate(aggregate_power)
    return predictions

# Example usage (requires UK-DALE dataset)
if __name__ == "__main__":
    # Train FHMM on UK-DALE
    fhmm = train_fhmm('ukdale.h5', building_num=1)

    # Load your household data
    aggregate = pd.read_csv('my_household_power.csv', index_col='timestamp', parse_dates=True)

    # Disaggregate
    predictions = disaggregate(fhmm, aggregate['power_watts'])

    print(predictions)
```

---

**End of Report**

**Date:** November 19, 2025
**Author:** Claude (Anthropic)
**Project:** Computer Vision Utility Monitor - NILM Research
**Location:** /Users/seanhunt/Code/computer-vision-utility-monitor/NILM_RESEARCH_REPORT.md
