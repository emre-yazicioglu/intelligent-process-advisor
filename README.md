# Intelligent Process Advisor

From process mining to automation decisions.

Agentic AI-powered system that analyzes object-centric event logs and generates structured automation recommendations across RPA, AI, and human-in-the-loop.

---

## Overview

Process mining provides visibility into processes, but it does not answer a critical question:

**Where and how should automation be applied?**

Intelligent Process Advisor is a system that combines object-centric process intelligence with AI-based decision logic to generate structured and explainable automation recommendations.

The focus is not on dashboards, but on decision-making.

This project is built on the principle that process intelligence should be owned and structured independently, before being operationalized through execution platforms such as RPA or AI tools.

---

## Current Working Prototype

The current implementation provides a lightweight Process Intelligence pipeline:

```
OCEL CSV
→ ingestion
→ activity-object feature extraction
→ activity interaction pattern classification
→ business insight generation
→ JSON export
```

This allows fast discovery of process structure and potential automation signals without requiring heavy enterprise tools.

### What It Does Today

- Loads OCEL-style CSV data  
- Extracts activity → object relationships  
- Identifies interaction patterns (join points, item-level activities, etc.)  
- Generates structured process insights  
- Exports results as machine-readable JSON  

Example output:

```json
{
  "activity": "Match Invoice",
  "pattern": "multi_object_join",
  "risk": "high",
  "insight": "Activity connects multiple business objects and may introduce reconciliation issues",
  "recommendation": "Validate object consistency and consider automation for matching logic"
}
```

---

## Problem

In most organizations:

* Process mining identifies bottlenecks and inefficiencies  
* Automation opportunities are still unclear  
* Decisions are often subjective or tool-driven  
* There is limited transparency behind automation choices  

In addition, many approaches:

* Rely on case-centric assumptions  
* Ignore object interactions  
* Apply AI without a solid process understanding  

---

## Solution

This project builds a system that:

* Ingests Object-Centric Event Logs (OCEL)  
* Performs process analysis using PM4Py  
* Evaluates each activity using a structured decision model  

Classifies automation suitability into:

* Agentic AI  
* RPA  
* Human-in-the-loop  
* Process redesign required  

Produces explainable recommendations.

---

## Architecture

The system is structured into the following layers:

**Ingestion Layer**  
OCEL parsing, validation, and object structure analysis  

**Process Analytics Layer**  
Bottleneck signals, variants, exceptions, and interaction patterns  

**Decision Intelligence Layer**  
Activity-level evaluation based on:

* variability  
* rule-based nature  
* data quality  
* exception rate  
* human judgment requirement  

**Recommendation Layer**  
Automation classification, prioritization, and confidence scoring  

**Explainability Layer**  
Reasoning, assumptions, and data limitations  

### Current Implementation Scope

The current prototype focuses on the early layers of this architecture:

- Feature extraction (activity-object relationships)  
- Interaction pattern classification  
- Initial insight generation  

These form the foundation of the **Process Analytics** and early **Decision Intelligence** layers.

---

## Tech Stack

* Python  
* PM4Py (object-centric process mining)  
* Pandas  
* (Planned) LangChain / LangGraph  
* (Planned) OpenAI / Claude APIs  
* (Planned) Streamlit  

---

## Project Structure

```
intelligent-process-advisor/

data/
  p2p_sample/

outputs/
  activity_insights.json

src/
  ingestion/
  features/        # low-level analytics (foundation layer)
  export/          # output handling
  main.py
  run_feature_extraction.py

requirements.txt
README.md
```

---

## How to Run

Important: ensure you are using Python 3.14

```bash
python --version
/usr/local/bin/python3 --version
```

Run the pipeline:

```bash
/usr/local/bin/python3 src/main.py --data data/p2p_sample
```

Pipeline:

```
Load data
→ Extract features
→ Classify patterns
→ Generate insights
→ Export JSON
```

Output:

```
outputs/activity_insights.json
```

---

## Vision

The goal is to move from tool-based process mining to system-level process intelligence.

This includes:

* Separation of decision logic from execution platforms  
* Integration of process understanding and AI reasoning  
* Structured and explainable decisions  
* Applicability in imperfect or low-data environments  
* Establishing an internal process intelligence layer before committing to execution platforms  

---

## Status

Work in progress.

Current focus:

* OCEL ingestion  
* Core analytics foundation  
* Feature extraction layer  
* Interaction pattern classification  
* Insight generation  

---

## Roadmap

* OCEL ingestion module  
* Core process metrics  
* Bottleneck and anomaly detection  
* Decision scoring framework  
* AI-supported classification  
* Explainable recommendation output  
* Lightweight interface layer  

---

## Author

Emre Yazıcıoğlu  
Building process intelligence systems that connect analysis to automation decisions.