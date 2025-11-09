# Prompts For PCR_Calculator

* AI tool: ChatGPT 5
* Purpose of script: calculate PCR master mix components amounts easily by only specifying amount of overall samples and mix concentration.
* Used [Markdown Crash Course](https://blog.webdevsimplified.com/2023-06/markdown-crash-course/) to help with markdowns.

## Prompts and Outputs

1. I want an easy GUI calculator for genotyping that calculates the
amounts I need to prepare (of DDW, mix, and primers) according to
amount of samples. take into account the "per sample": DDW 4 microliters,
mix solution 6 microliters and two primers (forward and reverse) each one 0.5 microliters.
I want the user's input to be just the amount of PCR samples overall.
      * **Output**: created a Single user input: number of PCR samples - Calculates totals for DDW, mix, primer F, primer R, and per-sample volume (11 µL). It also has an optional excess % (default 0%) for pipetting loss (toggle or CLI flag).
      * **Issue with output**: contained a "quick" button that set a default number, and the ammounts where not whole numbers which will make it harder to add percise ammounts in microliters.

2. I want the default excess to appear without the "quick" button, and I want that
the default will be giving whole numbers or 0.5 numbers.
      * **Output**: removed the “Quick: 10%” button, set a default excess of 10%, and made all reported volumes snap to 0.5 µL increments (whole or .5), switched the Excess field to a Spinbox with 0.5% steps.
      * **Issue with output**: remembered that the mix solution comes in two differennt concentrations - 2X and 5X.

4. the mixes are of two kinds - one with a 2X concentration and another of 5X, so include that.
