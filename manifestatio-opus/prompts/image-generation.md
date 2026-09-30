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

From story 4 onward, slide 1 is a quiz cover. Overlay typewriter questions after generating a blank-lower-half base (see `04-samwer/quiz-cover-example/`). Handwritten lock-in: `If you can't answer this, you have to read this.` Proofread names. No question may leak another question's answer.

When overlaying marks, use `manifestatio-opus/compose/overlay.py`. Highlight the paper, then draw ink. Letters must stay full black. Do not fade text through a yellow overlay. Reference: `identity/highlight-reference.jpg`.
