# Data and third-party notices

This is an academic research project. Public visibility is not an open-data
license. No project-wide reuse license has been selected by the contributors;
this notice does not grant rights to code, research artifacts, or third-party data.
A future code license must explicitly exclude third-party data and content.

## Yelp

The January 2022 Yelp archive supplied historical business and review inputs.
Obtain source data directly from [Yelp](https://www.yelp.com/dataset) under the
applicable agreement. Do not commit raw archives, original review/user/business
identifiers, or local review-labeling datasets.

The repository currently also contains short source-review excerpts, hashed
review keys, business-level coordinates and review counts, as well as aggregate
research outputs. The owner confirmed permission on 2026-10-02 to publicly release these
excerpts and business-level records. This confirmation is recorded in the audit;
the underlying agreement has not been independently inspected. Removing names
or hashing IDs alone does not establish redistribution permission. See the [release audit](docs/publication-audit.md) for affected files.

The official [July 7, 2023 dataset agreement](https://s3-media0.fl.yelpcdn.com/assets/srv0/engineering_pages/f64cb2d3efcc/assets/vendor/Dataset_User_Agreement.pdf)
limits use to academic purposes, restricts sharing source data, and includes a
review/approval provision before public presentation or publication. It also
addresses academic disclosures of summaries. The agreement actually accepted for
this archive, and any separate permission, were confirmed by the owner for this release;
this later document alone does not establish the archive's governing terms.
Yelp does not endorse this project or its conclusions.

## Geography, population, and project records

Census/ACS estimates and ZCTA boundaries supply historical context. Year, scope,
and source lineage are recorded in the notebook and data manifests. Census ZCTAs
are statistical areas and are not identical to postal delivery boundaries.

OpenStreetMap supplies street tiles and some map context. Preserve visible
[OpenStreetMap attribution](https://www.openstreetmap.org/copyright) and check
source-specific obligations before republishing extracted geography. Online tiles
send ordinary map-tile requests to the provider; offline mode uses bundled ZIP
boundaries. No claim of ownership is made over third-party geography.

Project costs, dates, footprints, and source links are documented in
[the project source audit](docs/project-source-audit.md). Linked public records
and ArcGIS layers retain their own terms. A source being publicly accessible does
not establish that every associated asset is freely redistributable.

## Software dependencies

Python dependencies are listed in `requirements*.txt`; JavaScript dependencies
are recorded in `package-lock.json`. Their upstream licenses remain applicable.
The prepared browser bundle includes third-party JavaScript; preserve the license
comments retained by the bundler. Do not apply a future repository license to
these dependencies or the datasets by implication.
