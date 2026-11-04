# Data dictionary and analysis choices

`data/processed/edges_{year}_cleaned.csv` fields:

- `source`: author-provided exporter country/jurisdiction name, normalized for documented spelling/encoding errors.
- `target`: author-provided importer country/jurisdiction name, similarly normalized.
- `weight_usd`: **positive, nominal United States dollars**, stored as numeric. The upstream record is declared to cover crude petroleum (HS 2709).

Each ordered country pair is present once in an annual CSV after summing genuine identical directed pairs, if encountered. A reciprocal pair consists of **two separate directed exports**, retained independently in the directed network. Self loops, nonfinite values and nonpositive weights are excluded. There are no zero-strength isolated nodes in the supplied edge lists. A node being a territory does not imply sovereignty.

For each year the GEXF file has matching directed edges and includes node-level:

- `in_degree` and `out_degree`: counts of distinct directed trade counterparties.
- `in_strength_usd` and `out_strength_usd`: sums of recorded incoming and outgoing trade values.
- `harmonic_out`: normalized directed outward harmonic centrality, \(\sum_{j \ne i, d(i,j) < \infty} 1/d(i,j)/(n-1)\), with unweighted shortest-path length.
- `betweenness`: NetworkX normalized directed unweighted betweenness centrality.
- `hub_score`, `authority_score`: HITS, calculated on the weighted directed graph.
- `community`: label assigned by Louvain using the symmetric projection with reciprocal trade values summed, weights in dollars, resolution 1, seed 46.
- `viz_x`, `viz_y`, and GEXF viz metadata: shared 2D coordinates and color/size suggestions for Gephi.

Clustering coefficients use the symmetric projection. Weighted clustering is normalized as implemented by NetworkX. Global efficiency uses reachable directed paths, and disconnected ordered pairs contribute zero. Strong and weak component counts **must not be conflated**.

Sensitivity definitions:

- Bilateral-dollar threshold filter: USD 0, 1,000, 1,000,000 or 10,000,000. All annual nodes are retained.
- Random deletion: 70 random permutations of vertices, random seed 20261102; 0,10,...,100% removed; LCC divided by remaining vertices.
- Targeted deletion: descending initial total degree, with fixed ranking and 0,10,...,100% removed; LCC divided by remaining vertices.
- Louvain stability: 20 runs with seeds 1000 to 1019.
- Null clustering: 25 undirected degree-preserving double-edge swap realizations with year-specific seeds, not a sanctions/COVID counterfactual.
- Rank stability: Spearman correlations on the intersection of labels observed in each annual pair, not a paired common-country panel estimate.
- Degree distribution: Geometric versus Zipf likelihood fit on positive in-/out-degrees; Akaike information criterion is indicative and subject to finite sample issues.

No causal model, supply-chain simulation, oil quantity, barrels-per-day, carbon emissions, official SDG metric or institutional trade agreement data are measured in this project.
