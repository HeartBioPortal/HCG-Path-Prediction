Pathway Commons PC2 v14 was downloaded as the default external background regulatory graph (BRG) candidate for this project.

Why this graph:

- It is scientifically close to how BioPathNet uses a BRG in the paper.
- It is an integrated human pathway / interaction graph rather than a direct disease-gene label graph.
- It adds mechanistic message-passing context such as physical interactions, regulation, phosphorylation, pathway links, and related molecular biology edges.

Files in this folder:

- `pc-hgnc.sif.gz`: integrated HGNC-symbol SIF interaction network
- `datasources.txt`: upstream source list and counts
- `metadata.json`: upstream release metadata

Upstream release:

- Pathway Commons PC2 v14
- Download root: `https://download.baderlab.org/PathwayCommons/PC2/v14/`

Important usage note:

- This graph should be treated as BRG / fact-graph input, not as target supervision.
- Before merging it into `train1.txt`, we should map node identifiers cleanly and filter any edges that would leak the target `GENE --ASSOCIATED_WITH_CONDITION--> CONDITION` task.
