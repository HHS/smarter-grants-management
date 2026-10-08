# Frontend Dependency Management (Node Modules)

For the most part, frontend dependencies on this project are managed in a very routine way using NPM. A few things are worth calling out

## Vulnerabilities and overrides

When high or medium level vulnerabilities appear in our security scans, we are required to either ignore them (if we can attest that they do not pose a risk) or resolve them prior to the next production deploy. Since this creates a good amount of urgency to act, and it is a relatively frequent occurance for a security vulnerability to appear in an npm dependency or subdependency, it is important to follow these guidelines when resolving vulnerabilities.

### When a vulnerability can't be patched

If a fix is not available for a vuilnerability found in our project, this could block deployment until a fix is availble. A couple of options:

- remove the dependency. If there is a workaround for including the dependency that allows us to remove it, we can do that, at least temporarily. If the vulnerable package is not maintained, then this is likely the direction we will want to take.
- ignore the vulnerability. If we can be reasonably assured that the risk of using the vulnerable package is low in the context of our application, we can at least temporarily ignore the vulnerability until it is patched.
- escalate a fix. If it's determined that we can't move forward without a fix, we can raise this situation to HHS leadership, the package maintainers, or anyone that will listen in hope that it leads to a quicker fix.

### Vulnerabilities in top level dependencies

- Top level dependencies should be patched directly
- Overrides should not be used
  - Except in the rare case that the vulnerable package is also included as an unpatched subdependency

### Vulnerabilities in dev dependencies

- If possible, dev dependencies should be patched directly
- If it is not feasible to patch a dev dependency, the vulnerability can be ignored if
  - We can be sure that the package is not and does not need to be included in our final production Dockerfile

### Vulnerabilities in subdependencies

- The first thing to do when a vulnerable subdependency surfaces is to research
  - What is the subdependency's dependency path? Which top level dependency can we trace the subdependency back to?
    - Tools like [npm-dependency-graph](https://github.com/TypeFox/npm-dependency-graph) or [npmgraph](https://npmgraph.js.org/) can help
  - Can we patch the top level dependency in a way that resolves the vulnerability? Does the top level dependency have a patched version that includes a patched version of the subdependency?
    - Sometimes if the subdependency is specified with a caret or tilde range, we can force a resolution by deleting our lockfile and running a fresh install
- Dependencies with vulnerable subdependencies should be patched to a version that do not contain vulnerable subdepencies where possible
- If a patched top level dependency version does not exist, but a patched subdependency version does, the best option is create an override in the package.json for the subdependency
  - This will force the application to use the patched version, while we wait for the top level dependency to implement the patch
  - Whenever this is done
    - This document should be uploaded with information uncovered in the research from step one, as well as what the initial vulnerability forcing the override was
    - A ticket should be created for revisiting the situation at a later date to see if the top level dependency has introduced a patched version

## Keeping dependencies up to date

TBD

### Node

On cadence TBD, check the current node version used by [the 24-bookworm-slim Dockerfile in Dockerhub](https://hub.docker.com/layers/library/node/24-bookworm-slim). This is the image used in our frontend Dockerfile, so this dictates the actual node version that our production build and runtime processes will use. If the version specified by the `NODE_VERSION` env var here is different from the version in the [engines declaration in our package.json](https://github.com/HHS/smarter-grants-management/blob/main/frontend/package.json#L6) and [our .nvmrc](https://github.com/HHS/smarter-grants-management/blob/main/frontend/.nvmrc), the version referenced in those places needs to be updated.

Whenever this version is updated, make sure to run a fresh `npm i` on the project as well, and commit any changes to the lockfile so we avoid lockfile mismatches in CI.

## Testing

When updating a dependency, the application must be tested to ensure that it still works as expected.

Directions TBD

## Current overrides

The list below is meant as a running list of overrides, explaining their current state and path towards resolution.

### ws

WS (websockets) has a vulnerability in 8.20.1 up to 8.21.

It is referenced at ^8.20.0 in puppeteer-core v24.43.1
It is referenced at ^8.18.0 in jsdom v26.1.0
It is referenced at ^8.18.0 in storybook v10.5.3

Tracking this in https://github.com/HHS/smarter-grants-management/issues/279

### sharp

v0.34.5 contains a vuln fixed in v 0.35.0. Latest stable next version (16.2.x) does not contain a patch, but latest canary (16.3.x) does so a fix should be forthcoming shortly.

### undici

Override: `^7.29.1`. Currently resolves to 7.30.0.

undici 7.0.0 to 7.29.0 has a DoS via unrequested WebSocket subprotocol ([GHSA-rfgv-xxqx-mfg5](https://github.com/advisories/GHSA-rfgv-xxqx-mfg5)) and a TLS certificate validation bypass in BalancedPool ([GHSA-w293-vg96-wgc3](https://github.com/advisories/GHSA-w293-vg96-wgc3)). 

All of them are fixed in 7.29.1.

It is referenced at ^7.21.0 in jsdom v28.1.0 (via isomorphic-dompurify; production)
It is referenced at ^7.19.0 in @newrelic/security-agent v3.0.4 (via newrelic; production)
It is referenced at ^6.19.5 in cheerio v1.0.0 (via pa11y-ci; dev only)

No current flags for undici 6.x (cheerio would resolve to 6.29.0 without the override).

Path to resolution: We could remove the override. If we want cheerio to use version 7.x, we could update pa11y-ci v5 for cheerio 1.2.0, which wants undici ^7.19.0. Then all versions would be 7.30.0

### nanoid

Override: `^3.3.17`. Currently resolves to 3.3.18.

nanoid below 3.3.18 can loop forever when a custom generator is called with size zero ([GHSA-2v37-7h3g-55p8](https://github.com/advisories/GHSA-2v37-7h3g-55p8), high).

It is referenced at ^3.3.19 in postcss v8.5.29 (top-level devDependency)
It is referenced at ^3.3.16 in postcss v8.5.23 (pinned by next v16.4.0)

Both ranges already allow a patched version. The override still allows the vulnerable 3.3.17, and the lockfile has 3.3.18.

Path to resolution: Remove the override, should resolve to 3.3.20.

### fast-uri

Override: `^3.1.6`. Currently resolves to `3.1.8`.

fast-uri 3.0.0 up to (but not including) 3.1.6 
Advisories in URI normalization (e.g. [GHSA-f65p-4m7j-42xc](https://github.com/advisories/GHSA-f65p-4m7j-42xc), [GHSA-fph4-wmhf-6fwf](https://github.com/advisories/GHSA-fph4-wmhf-6fwf)). 

Authority injection via unvalidated port, fixed in 3.1.7 ([GHSA-qw65-cvwx-89v3](https://github.com/advisories/GHSA-qw65-cvwx-89v3), high) 
host case normalization, fixed in 3.1.8 ([GHSA-hrr3-gc8f-f4qj](https://github.com/advisories/GHSA-hrr3-gc8f-f4qj), moderate). 

The override as written (`^3.1.6`) would still allow two of the vulnerabilities

The ajv range already allows the patched version.

Path to resolution: Remove the override or increase it to (`3.1.8`). 
I see no change to the lockfile removing this locally.

### dompurify

Override: `^3.4.16`. Currently resolves to 3.4.16 (latest).

DOMPurify has XSS / sanitizer bypass advisories. Affecting everything up to 3.4.15 ([GHSA-p98j-92pf-mc4p](https://github.com/advisories/GHSA-p98j-92pf-mc4p), [GHSA-6688-9rhm-gjv2](https://github.com/advisories/GHSA-6688-9rhm-gjv2)).

It is referenced at ^3.3.1 in isomorphic-dompurify v2.36.0 (direct dependency)

The isomorphic-dompurify range allows 3.4.16.

Path to resolution: I see no change to the lockfile removing the override. However upgrading isomorphic-dompurify to v4.x. v4.5.0 depends on `dompurify ^3.4.16` and `jsdom ^30.1.2`, so the floor would come from upstream. 
This is a major version bump though and may have larger impact. 

It might help with untangling source-map-js, since isomorphic-dompurify is one of the paths that pulls in jsdom/csstree.

### source-map-js

v1.2.1 has a vulnerability that is resolved in 1.2.2. This depends on a number of packages updating including sass, and csstree, which is included indirectly via jsdom, jest-environment-jsdom, isomorphic-dompurify, css-stylie, and specificity. This will be a tough one to untangle, best to check back in later and try to update everything?
