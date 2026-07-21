# visual.md — Sofia Reyes

> Face refs, body/style rules, banned drift, seed / LoRA / reference method.
> **Acceptance test (from spec): post 1 and post 847 must be the same person.**
> The LoRA is what locks this — gpt-image-1 and browser-driven ChatGPT cannot, and are NOT the method here.

## Face lock — method
- **Engine:** Flux 2 + character LoRA (the face-lock mechanism)
- **Training set:** ~47 reference images of one consistent face (front, 3/4, profile, varied light/expression)
- **Train:** RunPod A100 ~6h (≈$80) or Kohya / Colab
- **Seed:** lock a base seed per shot type for reproducibility — record final seed here once trained
- **LoRA file:** `assets/lora/sofia_reyes/sofia_reyes.safetensors` *(output of training)*
- **Trigger word:** `sofiareyes_face` *(set at train time; used in every prompt)*

## Reference images
- **Current refs:** `assets/faces/face1.jpeg` (seed face), `assets/faces/Sofia/` (variant set — to be regenerated/curated for LoRA, not final)
- **Target:** curate/produce ~47 clean, consistent refs of ONE face before training. Existing Sofia/ variants are inconsistent (different faces) and must NOT be used as-is for the LoRA.

## 6–8 fixed descriptors (never change these — the face is these words)
1. Warm light-olive / sun-kissed Latina complexion
2. Dark brown hair, long, soft natural waves, center part
3. Dark almond-shaped brown eyes, defined brows
4. Straight nose, full natural lips, soft jawline
5. Small crescent-moon scar inside left wrist (signature — see [[persona]])
6. Natural, minimal makeup look; glowy not matte
7. Slim-athletic build, ~5'7"
8. Understated jewelry: thin gold, never loud

## Body / style rules
- Wardrobe: elevated minimalist — linen, silk, neutral tones, one statement piece max
- Brands on-body should match [[persona]] list (Celine, Bottega, The Row, etc.)
- Always looks like she *just arrived somewhere* — lived-in, not posed-stiff
- Lighting: warm golden tones, cinematic, natural; editorial not flash

## Banned drift (auto-reject if any appear)
- Different face shape, lighter/European complexion, blue/green eyes, blonde hair
- Missing or wrong-wrist scar
- Over-smoothed "AI plastic" skin, doll/CGI look
- Extra/melted fingers, warped jewelry, garbled text
- Heavy glam makeup, club/party aesthetic (off-brand for Line N)
- 6th finger / asymmetric eyes / mismatched earrings

## Continuity review (evidence rule)
Every generated asset gets a pass/fail against the 8 descriptors + banned-drift list.
Keep **rejected-drift examples** as evidence (spec §7). Log:
- asset path → review result (pass/fail) → reason if fail
- Record in [[content_backlog]] per post

## Post-processing (carry over from existing pipeline)
ffmpeg grain(40) + sharpness(20) + brightness(-7) + vignette(12); strip AI metadata (exiftool).
