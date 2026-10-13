# Northstowe responsibility map

A resident-facing map of Northstowe civil parish, with separate problem and organisation filters, overlapping contact scopes, individual county asset records, dated evidence and explicit information gaps.

The checked-in data combines public research with summaries of organisation replies received on 15–17 September, reviewed on 13 October 2026. County assets were refreshed on 13 October; OSM footprints remain the 11 September snapshot. It is not a certified register of legal ownership or current handover boundaries. The official ONS parish boundary is complete; responsibility evidence is incomplete. Read `public/data/research-notes.md` for sources, methods, contacts and outstanding information holders.

## Local development

For a locally hosted production app with an external demonstration link, see [LOCAL-HOSTING.md](LOCAL-HOSTING.md). Start with `Start-Northstowe.ps1 -Share`; stop with `Stop-Northstowe.ps1`. The reviewed local app uses the same map component and data as the Sites app. Email drafts are private local files under `email-drafts/`, excluded from the public build and source upload.

Requires Node 22.13+ and pnpm. Run `pnpm install` and `pnpm dev`. The application uses Leaflet and OpenStreetMap tiles. Contact and responsibility data is local to the site; no report submission or location storage is implemented.

## Data maintenance

Migration audit, 13 October 2026: compared project source, data, research and documents with the original folder on E:. Restored 64 omitted files, including raw research, boundary datasets and the two later helper scripts. Restored the original runtime/test files while retaining the additional correspondence privacy check. Private email drafts, received correspondence and research downloads remain local and are excluded from Git. Generated caches, old process state and dependency folders are recreated for this computer rather than copied from the old profile.

Canonical client files are `public/data/responsibilities.json` and `public/data/parish.geojson`. Each area carries a geometry note, evidence status, source IDs and one or more category-specific responsibility records. An enquiry area must not be promoted to confirmed maintenance merely because a development has been built or a transfer was expected.

Rebuild data in this order: `scripts/build-map-data.py`, `scripts/extend-map-data.py`, `scripts/finalise-map-data.py`, `scripts/review-map-data.py`, then `scripts/apply-response-updates.py`. The last step requires the privately held bin document and research files. Before refreshing county data, run `scripts/fetch-county.py` and `scripts/convert-county.py`; a partial fetch must not be published as a complete new snapshot. Response updates reconcile road/light row IDs against the unchanged named inventory and stop for a changed inventory that needs review. Generate the original private review pack with `scripts/prepare-email-drafts.py`; new targeted drafts are in `email-drafts/follow-ups/`. Original research, local GIS dependencies and received correspondence are retained privately, excluded from Git and both web builds.

The October update separates Western Park playing surfaces, pitch bases, routine car-park care, surface repairs and EV points. Ownership and operator roles do not imply every service contract. Homes England's broad land overlays exclude indicative Inholm, Stirling Fields and Education Campus footprints; these are orientation shapes awaiting approved GIS boundaries. Pending Faith/Community, Eastern Sports Hub and Town Hub transfers retain their dated contacts. The 48 supplied bin records are searchable separately: 46 Wednesday, two Thursday, two supplied bin numbers, no confirmed coordinates or contractor. Duplicate descriptions remain separate records. The restricted supplied title-plan image and traced boundary are not published. Suggested review dates and a proposed register owner are clearly labelled as proposals.

The county query uses a bounded public WFS request, then tests exact intersection against the parish in British National Grid before converting to longitude/latitude. It retains complete edge features. County centreline geometry does not represent the legal highway width. Four returned district residential holdings are excluded from public-realm scope.

The recovered research scripts use Python GIS packages from `research-boundaries/_deps`. Recreate them on a new computer with `python -m pip install --target research-boundaries/_deps shapely==2.1.2 pyproj==3.8.0 certifi==2026.7.22` (NumPy is also required and is installed as a Shapely dependency). This directory is ignored; retain the original research files and provenance separately from the Git source backup.

Validation: `pnpm exec tsc --noEmit`; `node --experimental-strip-types --test tests/map-spatial.test.mjs`; Sites build helper. Spatial checks cover lake contacts, overlapping H4 scopes, sports exceptions, prospective adoption, county asset IDs, source integrity and parish coverage.

The review adds filtered organisation/task summaries for hover and tap, separate road rendering panes, a collapsible legend, and a distinct public-bin-emptying category with historical versus enquiry evidence. Sixteen map checks cover these distinctions, including October task splits, exception masks, bin transcription and private-source summaries. After `pnpm run local:build` and starting the local app, `node --test tests/local-server.test.mjs` checks the production page/assets, updated data and exclusion of private files. Set `NORTHSTOWE_TEST_URL` to verify the external link too.

## Verification limits

October update validation: TypeScript, 16 map/data checks plus an initial-render regression check, all 316 nonempty valid geometries, repeatable response generation and both production builds passed. Three HTTP checks passed against the local server and external tunnel. Browser access to localhost was blocked by an administrator policy; no visual browser validation was completed for this update. The received emails, raw restricted title-plan and 14 private unsent follow-up drafts are excluded from the builds and source repository. Keepmoat's draft is held without a verified email recipient.

Review validation on 12 September 2026: TypeScript and both production builds passed; all ten map tests passed; the three HTTP checks passed against both the local server and the external tunnel. The 19 `.eml` files were parsed and checked for unsent status, recipients and signature placeholders. The start script was checked to reuse the existing tunnel after fixing PowerShell's JSON date conversion. Lint still reports typing, hook/ref and accessibility issues in the existing map component; these are separate from the passing build and data/HTTP checks.

The optional feature-detected WebMCP read-only contact lookup has not been exercised in a supported browser tool context; ordinary map controls do not depend on it. Spatial data is checked independently. See the research register for remaining data uncertainties.

## Rights

Preserve ONS/Ordnance Survey, county mapping, OpenStreetMap and source-plan attribution. Each source retains its own terms; the dataset is a compilation and no blanket licence over third-party material is asserted.
