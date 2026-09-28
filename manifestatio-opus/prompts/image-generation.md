# Image generation prompts

Use Cursor `GenerateImage`, aspect `3:4`, then crop to 1080x1350.

Always attach Michelin references:

- `manifestatio-opus/week-2026-09-28/01-michelin/slides/01.jpg`
- `manifestatio-opus/week-2026-09-28/01-michelin/slides/04.jpg`
- `manifestatio-opus/week-2026-09-28/01-michelin/slides/08.jpg`

Shared prefix for every prompt:

```
Photographed real sheet of cream grid paper on a dark walnut desk, identical to the reference images. Soft window light from the top left, gentle shadows, slightly curled corners, paperclip or a single strip of masking tape. Classic typewriter serif body text, messy black ballpoint for notes and @Manifestatio.Opus at the bottom. Slide number N/8 at the top right. A glossy photo print with a white border is taped onto the paper at a slight angle with a soft shadow. No faces. No extra text. Handmade, not a digital template.
```

Then append the slide-specific text and marks from that day's `brief.md`.

Cover slides: the taped photo is ~40% of the sheet. Other slides: smaller print is fine, still clearly a photograph of the real product.
