Mahmood Ahmad
Tahir Heart Institute
author@example.com

HTA Artifact Standard: An Open-Source Platform with 41 Analytical Engines for Health Technology Assessment

How can health technology assessment analysts unify economic modeling, evidence synthesis, and uncertainty analysis within one open-source platform? HTA Artifact Standard implements 41 engines spanning Markov simulation, microsimulation, discrete event simulation, partitioned survival, pairwise and network meta-analysis, probabilistic sensitivity analysis, and value-of-information computation. Deterministic reproducibility is enforced through a PCG32 seeded pseudo-random generator, Kahan compensated summation, and IEEE 754 compliance, producing identical outputs from the same seed. The validation suite comprises 3,337 automated tests across unit, integration, property-based, stress, and performance categories, with Markov and OR pooling fixtures matching R outputs to a maximum absolute error within CI bounds of 4.72e-5. Eight meta-analysis benchmarks against R metafor and four publication bias validations passed within specified tolerances. The platform provides a unified, transparent, reproducible HTA workflow accessible to analysts without commercial software licenses. Scope is bounded to the 41 implemented engines; emerging methods such as federated survival analysis and adaptive platform trial simulation are not yet supported.

Outside Notes

Type: methods
Primary estimand: ICER, NMB, and pooled treatment effects
App: HTA Artifact Standard v1.1
Data: 41 analytical engines with PCG32 determinism
Code: https://github.com/mahmood726-cyber/hta-artifact-standard-v2
Version: 1.1
Validation: DRAFT

References

1. Salanti G. Indirect and mixed-treatment comparison, network, or multiple-treatments meta-analysis. Res Synth Methods. 2012;3(2):80-97.
2. Rucker G, Schwarzer G. Ranking treatments in frequentist network meta-analysis. BMC Med Res Methodol. 2015;15:58.
3. Dias S, Welton NJ, Caldwell DM, Ades AE. Checking consistency in mixed treatment comparison meta-analysis. Stat Med. 2010;29(7-8):932-944.

AI Disclosure

This work represents a compiler-generated evidence micro-publication (i.e., a structured, pipeline-based synthesis output). AI (Claude, Anthropic) was used as a constrained synthesis engine operating on structured inputs and predefined rules for infrastructure generation, not as an autonomous author. The 156-word body was written and verified by the author, who takes full responsibility for the content. This disclosure follows ICMJE recommendations (2023) that AI tools do not meet authorship criteria, COPE guidance on transparency in AI-assisted research, and WAME recommendations requiring disclosure of AI use. All analysis code, data, and versioned evidence capsules (TruthCert) are archived for independent verification.
