---
name: write-report
description: Write or revise an experiment report following the project style guide
---

Write an experiment report for: $ARGUMENTS

## Process

1. Read the style guide at `evidence/experiment_report_style_guide.md`
2. Gather evidence — read eval results, configs, and any prior analysis from the relevant `evidence/<experiment>/` folder
3. Draft the report following the style guide structure: Motivation → Design and Hypothesis → Iterations → Evaluation Setup → Results → Decision and Tradeoffs → Lessons → What's Next → Artifacts
4. Run through the style guide checklist before presenting the draft:
   - Does every design decision name its tradeoff?
   - Does every iteration link back to a specific finding from the prior version?
   - Does every table have a stated takeaway?
   - Are assumption corrections surfaced as findings, not buried?
   - Are lessons stated as transferable principles with evidence?
   - Is impact framed honestly?
   - Would a reader who skips the tables still understand the narrative from the prose?
5. Co-locate all artifacts with the report in `evidence/<experiment>/`
