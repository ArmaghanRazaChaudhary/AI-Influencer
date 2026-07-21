# visual.md — {{NAME}}

> Face refs, body/style rules, banned drift, seed / LoRA / reference method.
> **Acceptance test: post 1 and post 847 must be the same person.** LoRA is the lock.

## Face lock — method
- **Engine:** Flux 2 + character LoRA
- **Training set:** ~47 consistent reference images (front, 3/4, profile, varied light/expression)
- **Train:** RunPod A100 ~6h (≈$80) or Kohya / Colab
- **Seed:** {{record locked seed after training}}
- **LoRA file:** `assets/lora/{{persona_id}}/{{persona_id}}.safetensors`
- **Trigger word:** `{{trigger}}`

## Reference images
- **Refs dir:** `assets/faces/{{Name}}/`
- Curate ~47 clean refs of ONE consistent face BEFORE training.

## 6–8 fixed descriptors (the face IS these words — never change)
1. {{complexion}}
2. {{hair}}
3. {{eyes / brows}}
4. {{nose / lips / jaw}}
5. {{signature mark from persona.md}}
6. {{makeup look}}
7. {{build / height}}
8. {{jewelry / signature accessory}}

## Body / style rules
- {{wardrobe}}
- {{lighting}}

## Banned drift (auto-reject)
- {{wrong face shape / complexion / hair / eyes}}
- Missing signature mark
- AI-plastic skin, doll/CGI, extra fingers, warped jewelry, garbled text
- {{off-brand aesthetic for the line}}

## Continuity review (evidence rule §7)
Every asset: pass/fail vs 8 descriptors + banned-drift. Keep rejected-drift examples. Log result per post in [[content_backlog]].

## Post-processing
ffmpeg grain(40)+sharpness(20)+brightness(-7)+vignette(12); strip metadata (exiftool).
