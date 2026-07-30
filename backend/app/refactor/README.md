# Legacy Refactoring Module (T3)

Turns a screenshot of a legacy enterprise screen into a modern Angular
component — and verifies its own output.

## The loop

    screenshot --(vision)--> UISpec  --(generate)--> Angular component
                                ^                          |
                                |                     (recover spec)
                                |                          v
                          fidelity score <--(compare)-- recovered UISpec
                                |
                    below threshold? feed missing fields back and regenerate

The differentiator is step 3-4: the module re-derives a spec from its own
generated code and scores how faithfully it reproduced the original screen.
If fidelity is below the threshold it refines, up to `max_iterations`. Most
one-shot generators never check their work — this one measures and corrects.

## Why spec comparison, not pixel comparison

Comparing structured specs (field type + fuzzy label match) makes fidelity a
real number that is unit-testable without a browser or a screenshot renderer.
The whole control flow runs offline against FakeProvider in the test suite;
only the initial extraction needs a vision-capable model.

## Usage

    POST /refactor   { "image_b64": "<base64 png>", "threshold": 0.9 }

Returns the extracted spec, the generated component, and the fidelity report
(score, matched/missing/extra fields, iterations, cost).
