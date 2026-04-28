# Intelligent Process Advisor

From process mining to automation decisions.

An AI-augmented Process Intelligence system that analyzes object-centric event logs, provides advanced process analytics and interactive insights, and enables intelligent automation decision support across RPA, AI, and human-in-the-loop.

---

## Overview

Process mining provides powerful visibility into processes.

However, there is still a critical gap:

**How do we move from understanding processes to making structured, confident automation decisions?**

Intelligent Process Advisor extends process mining with a new layer of decision intelligence.

It combines:

- object-centric process understanding  
- structured analytical signals  
- AI-assisted reasoning  

to transform process data into clear, explainable recommendations.

The goal is not only to understand processes, but to guide what should happen next.

---

## What This System Does

The system is designed to:

- analyze object-centric process data (OCEL)  
- understand how activities interact with business objects  
- detect structural complexity and interaction patterns  
- identify potential weaknesses in the process  
- generate structured insights  
- support automation decisions across:
  - Agentic AI  
  - RPA  
  - Human-in-the-loop  
  - Process redesign  

The output is not just analysis, but **decision-oriented intelligence**.

---

## Current Implementation

The current prototype focuses on building the analytical foundation of the system.

Implemented so far:

- OCEL-style data ingestion from CSV  
- activity → object relationship extraction  
- interaction pattern classification  
- basic insight generation  
- structured JSON output  

Current pipeline:

```
OCEL CSV
→ ingestion
→ activity-object feature extraction
→ interaction pattern classification
→ insight generation
→ structured output
```

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

## Target Product Experience

The intended system is not a command-line tool, but an interactive intelligence layer.

Target user flow:

```
Upload process data (OCEL / CSV)
→ automatically analyze process structure
→ view insights in a dashboard
→ interact with AI (ask questions)
→ receive automation recommendations
```

Example questions:

- Where are the main weaknesses in this process?  
- Which activities are most complex or risky?  
- What should be automated first?  
- Should this activity be handled by RPA, AI, or human intervention?  

---

## Architecture

The system is structured into layered intelligence:

### Ingestion Layer
Parses and validates object-centric process data.

### Process Analytics Layer
Extracts structural signals such as:

- activity-object relationships  
- interaction patterns  
- complexity indicators  

### Decision Intelligence Layer
Evaluates activities based on:

- variability  
- rule-based behavior  
- object dependencies  
- process complexity  

### Recommendation Layer
Classifies automation opportunities:

- Agentic AI  
- RPA  
- Human-in-the-loop  
- Process redesign  

### Interface Layer (Planned)
Provides:

- dashboard visualization  
- AI interaction  
- explainable outputs  

---

## Why This Project

Many organizations can analyze processes, but struggle to translate that analysis into action.

This project explores how to:

- connect process understanding to automation decisions  
- structure decision logic explicitly  
- integrate AI as a reasoning layer, not just a tool  
- enable faster discovery before committing to large-scale platforms  

The aim is to build a **flexible process intelligence layer** that complements existing tools rather than replacing them.

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
  features/
  export/
  main.py
  run_feature_extraction.py

requirements.txt
README.md
```

---

## Status

Work in progress.

Current focus:

- building the analytics foundation  
- structuring process signals  
- generating initial insights  

Next steps:

- dashboard prototype  
- real OCEL dataset integration  
- AI-assisted reasoning layer  
- automation decision classification  

---

## Author

Emre Yazıcıoğlu  
Building process intelligence systems that connect analysis to automation decisions.