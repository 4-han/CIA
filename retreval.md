### Retrieval Evaluation

This notebook/script ([`scripts/evaluation_retrival.ipynb`](./notebooks/)) is used to evaluate and compare the performance of different retrieval methods. The goal is to determine which search index (Minsearch or Elasticsearch) is more effective at retrieving relevant documents for a given user query. The evaluation uses a pre-generated ground truth dataset containing questions and the URLs of the documents that should contain the answer.

#### Evaluation Metrics

The evaluation focuses on two key metrics:

-   **Hit Rate:** The proportion of queries for which the correct document (as identified in the ground truth) is found among the top `N` search results (where `N` is the number of results requested from the search function, typically 5). A higher hit rate indicates that the correct document is frequently included in the search results.
-   **Mean Reciprocal Rank (MRR):** Measures the ranking of the first correct document in the search results. If the correct document is ranked first, the reciprocal rank is 1. If it's ranked second, it's 1/2, third is 1/3, and so on. The MRR is the average of these reciprocal ranks across all queries. A higher MRR indicates that when the correct document is found, it tends to be ranked higher in the results.

#### Evaluation Process

1.  The ground truth dataset (`ground-truth-data.csv`), containing generated questions and their corresponding correct document URLs, is loaded.
2.  The Elasticsearch client is initialized, and data is indexed into an Elasticsearch index (`course-questions`).
3.  A function (`elastic_search`) is defined to perform searches against the Elasticsearch index using a `multi_match` query on the 'title' and 'info' fields.
4.  The Minsearch index is initialized and fitted with the document data.
5.  A function (`search`) is defined to perform searches against the Minsearch index.
6.  For each query in the ground truth dataset:
    -   Both the `elastic_search` and `search` (Minsearch) functions are executed with the query.
    -   The URLs of the search results are compared against the correct document URL from the ground truth.
    -   A list of booleans (`relevance`) is created, indicating whether the document at each rank in the search results is the correct one.
7.  The `hit_rate` and `mrr` functions are used to calculate the final metrics based on the accumulated `relevance` lists for all queries.

#### Results

The script/notebook compares the `hit_rate` and `mrr` for both retrieval methods:

-   **Elasticsearch Results:** `{'hit_rate': 0.701..., 'mrr': 0.828...}`
-   **Minsearch Results:** `{'hit_rate': 0.593..., 'mrr': 0.470...}`

#### Conclusion

Based on this evaluation, the Elasticsearch retrieval method achieved a higher Hit Rate (correct document found more often in the top 5 results) and a significantly higher Mean Reciprocal Rank (when found, the correct document was ranked higher) compared to the Minsearch index using the current configuration and dataset. This suggests that Elasticsearch, with its more advanced indexing and querying capabilities (even with a simple `multi_match`), is more effective for retrieving relevant documents in this context.