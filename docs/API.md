# hh.ru integration and publication prerequisites

Documentation checked on 2026-10-22 against the official [OpenAPI specification](https://api.hh.ru/openapi/specification/public), [documentation](https://api.hh.ru/openapi/redoc), [application-token guidance](https://github.com/hhru/api/blob/master/docs/authorization_for_application.md) and [API terms](https://dev.hh.ru/admin/developer_agreement). Recheck these before enabling a real deployment: source policy can change.

## Access

Register MlPops at <https://dev.hh.ru/admin>. Obtain an application access token via the documented application authorization flow (`client_credentials`) or retrieve an existing application token in the developer console. Supply it as `HH_TOKEN`; the client sends `Authorization: Bearer …`. `HH_USER_AGENT` must identify the app/version and a real developer email. Requests use `HH-User-Agent`; errors never log raw responses, headers, tokens or CAPTCHA URLs.

The application token guidance describes a reusable application token; generating a replacement revokes the prior token. User OAuth tokens are a different flow: honor their `expires_in`, and rotate the one-use refresh token as documented. MlPops accepts an externally managed access token and does **not** store a refresh token or automatically rotate repository secrets. A revoked/expired/unauthorized token stops collection and needs operator action. No token is placed in a URL or a frontend environment variable.

Current vacancy-search documentation explicitly warns that unauthenticated searches can challenge after the first request. The client therefore refuses anonymous collection. CAPTCHA and 401/403 responses stop the run; there is no bypass or proxy rotation.

## Search contract

`GET /vacancies` supports `text` with the [hh.ru query language](https://hh.ru/article/1175), zero-based `page`, at most 100 items per page and a maximum depth of 2,000 results. `date_from` and `date_to` are rounded to five-minute boundaries by the source. MlPops bisects overflowing publication windows using **inclusive overlapping** five-minute boundaries, then deduplicates IDs. A five-minute partition still above the ceiling is recorded as truncated, making the run partial. Request-budget exhaustion also prevents publication.

`/dictionaries` supplies actual source enum IDs. Configurable dictionary-backed filters are validated before search. `/areas` supplies the location hierarchy; country and region stay unknown if not resolved. Unknown/new API fields are tolerated during normalization, while the public export has a strict versioned schema. Source work-format, experience, employment and salary-range fields are retained without inventing missing values.

Full `/vacancies/{id}` responses are used for extraction and content hashes. Only normalized facts and short evidence snippets are retained. Source HTML, contacts and raw response payloads are not persisted. Details are refreshed after `HH_DETAIL_TTL_HOURS` (24 by default), including previously observed IDs absent from new searches. A 404/410 means inaccessible, not archived. Archival requires an explicit source flag.

Concurrency is one. Defaults: 800 requests/run, 25-second timeout, three retries for network/429/5xx responses, exponential backoff with jitter. `Retry-After` numeric and HTTP dates are respected; waits above 120 seconds defer to a later run. HTTP redirects are not followed with credentials. Authentication failures are not retried.

## Redistribution gate

API terms restrict this architecture's public use: section 3.11 addresses material changes and removing archived vacancies; sections 4.3 and 4.6 restrict redistribution/database access and transfer to third-party services. Short snippets and normalized facts are **not assumed automatically exempt**. Written permission covering public static exports and repository-backed persistence is an external prerequisite. App registration may also require changing how users accept hh.ru agreements; MlPops has no registration flow.

Default delivery publishes only explicitly fictional demo records. Private local collection is supported independently. Public export requires `--public` and `HH_PUBLICATION_PERMISSION`, an operator-supplied permission reference. The flag is an auditable operational gate, not a substitute for permission. Public real exports remove source-confirmed archived and inaccessible vacancy records and their detailed historical snapshots; aggregate daily counts remain. This redaction reduces reconstructable historical cohort coverage and is disclosed in methodology.

Do not run real state on a public `data` branch until written permission covers it. For a private deployment, also check Pages audience: a private source repository does not by itself guarantee a private Pages website. No real collection was exercised during implementation because no valid application credentials or publication permission were supplied.
