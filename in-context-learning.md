---
# yaml-language-server: $schema=schemas/concept.schema.json
Object type:
    - Concept
Tag:
    - NoteBook 5 - Dynamic Operations
Backlinks:
    - 4-the-system-architecture-v2-0.md
    - 1-executive-summary-resolving-the-ontology-cri.md
    - the-large-language-model-as-dynamic-transition.md
    - the-recursive-third-intelligence-system-archit.md
Status: Done
Creation date: "2025-11-22T16:54:19Z"
Created by:
    - Roi Ezra
Emoji: "\U0001F4A1"
id: bafyreiarczymkovtjuunvxlyjgb6a3ahy3wzm5q5o5tznvoj7e2pyu4dba
---
# In-Context Learning   
**Definition:** The technical capability of LLMs to adapt to the prompt context.   
Acts as the **Servomechanism** for Adaptive Calibration. It allows the AI to fine-tune the Challenge Gap ($\|D-C\|$) in real-time.   
   
**In-Context Learning (ICL)** is a crucial paradigm and emergent capability observed in Large Language Models (LLMs). It enables an LLM to adapt to new tasks and generalize to new domains by conditioning on demonstrations or examples provided directly within the input prompt, which serves as the context. Critically, this "learning" occurs at inference time without any explicit training, fine-tuning, or gradient updates to the model's parameters. ICL allows the pre-trained model to dynamically adapt to different contexts, utilizing its ability to recognize patterns and apply knowledge learned during its extensive pre-training.   
In practice, this capability is often leveraged using **few-shot prompting**, where a minimal set of task-oriented input-output examples (the task demonstration) is included in the prompt's context before the user's query. Theoretically, while there is no immediate explicit weight update, researchers conjecture that an implicit form of weight updates takes place at inference time when the prompt is consumed. This means the trained LLMs seem to reorganize or reconfigure themselves based on the instruction of the user prompt, exhibiting a dynamic nature equivalent to learning in context. The overall goal is to predict the correct answer to the query, conditioned on the task demonstration provided in the context.   
   
