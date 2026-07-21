# visual.md - Mina Park

> Face refs, body/style rules, banned drift, and generation method.

## Face lock - method
- **Current method:** Codex built-in image generation for first reference face
- **Reference face:** `assets/faces/mina_park/face_reference.png`
- **Future lock:** if long-run continuity is required, train a dedicated LoRA or equivalent identity model from curated references
- **Acceptance target:** image 1 and image 847 should read as the same person before this persona is scaled

## Fixed descriptors
1. Korean-American woman, age 31
2. Fair neutral-olive skin tone, natural texture
3. Straight black chin-length bob, slightly tucked behind one ear
4. Dark brown almond-shaped eyes, softly defined brows
5. Oval face, straight nose, subtle natural lips
6. Minimal makeup; clean skin, no heavy glam
7. Slim build, practical posture, calm presence
8. Tiny pale solder-burn mark on side of right index finger when hands are visible

## Body / style rules
- Wardrobe: practical minimalist citywear - black, graphite, olive, cream, denim, weatherproof layers
- Common pieces: boxy overshirts, cropped technical jackets, straight-leg trousers, simple tees, soft knits, clean sneakers, crossbody tech bag
- Accessories: thin silver rings, small hoops, watch, glasses sometimes
- Visual world: rain, desk light, hardware benches, cafes, trains, labs, rooftops, bookstores, city streets
- Lighting: cool window light, rainy reflections, desk lamp glow, clean practical interiors

## Banned drift
- Blonde hair, blue/green eyes, heavy glam makeup
- Luxury yacht / beach-club aesthetic; that belongs to Sofia
- Party-girl styling or adult/suggestive framing
- Overly corporate stock-photo office scenes
- Plastic AI skin, warped devices, melted fingers, fake unreadable brand logos as the focus
- Turning her into a teen, anime character, or generic beauty influencer

## Continuity review
Every generated asset should be checked against the fixed descriptors and banned-drift list.
Log:
- asset path
- pass/fail
- reason if fail
- whether the right-index solder mark appears correctly when hands are visible
