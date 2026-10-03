# Project source audit — September 25, 2026

This audit records targeted changes to the active evidence registry. Earlier coursework tables remain historical artifacts; they are not silently rewritten to appear to have used the corrected design.

## Gateway Arch Park

The National Park Service identifies July 3, 2018 as completion of the $380 million renovation covering the national park, St. Louis Riverfront and Kiener Plaza. The earlier training row combined that total cost with a 2015 milestone and 2016–2017 outcomes. The active registry now uses the full-project opening and 2019–2020 post window. This window includes the pandemic, and the remaining center-point geometry does not represent the full cost footprint; both limitations remain explicit. [NPS completion announcement](https://home.nps.gov/jeff/learn/news/grand-opening-events-for-new-gateway-arch-national-park-experience.htm).

## Crescent Park

The City of New Orleans describes the $31.2 million, 1.4-mile park as opening in July 2015. The designer gives July 2, 2015. Some older planning material refers to 2014, consistent with an ambiguous earlier phase; the active full-project record uses July 2015 and 2016–2017 outcomes. The reported cost is not an audited expenditure ledger. [City announcement](https://content.govdelivery.com/accounts/LANOLA/bulletins/1c0763a), [designer opening record](https://www.hargreaves.com/newsitem/crescent-park-opens-in-new-orleans/).

## Rail Park, phase one

The operator's published project description identifies October 31, 2016 construction and June 14, 2018 opening. The 2015–2016 baseline includes a small portion of construction, and the 2019–2020 outcome includes the pandemic. These are sensitivity flags rather than grounds to select a more favorable period. The operator page was present in search results but redirects to the broader site when opened, so its historical URL is retained as provenance. [CCD project description](https://www.centercityphila.org/ccd-services/streetscape/rail-park).

The active footprint now uses the public Rail Park polygon published by the `jbrain_ccdphila` ArcGIS account. The layer distinguishes `Rail Park` (OBJECTID 11) from `Rail Park - Phase 2` (13). Only 11 is included. This replaces a point approximation, but is still current mapped geometry, not an independently surveyed 2018 boundary. The downloaded geometry, exact query, hash and provenance are in `data/geometry/`; `src/fetch_project_geometry.py` reproduces the download. [GIS layer](https://services1.arcgis.com/TNz8x5gA9YhXLeFQ/arcgis/rest/services/Rail_Park/FeatureServer/0), [item metadata](https://www.arcgis.com/home/item.html?id=ca95766207934d409c481634b26fcd79).

## Indianapolis Cultural Trail

The operator reports $63 million total cost: $27.5 million private and $35.5 million federal funding. Groundbreaking was in spring 2007. Consequently, the existing 2010–2011 baseline is before completion but overlaps construction; it must not be described as pre-intervention evidence. [Operator FAQ](https://indyculturaltrail.org/about/faq/).

An official current trail GIS layer was examined, but it contains segments added or edited after the historical project. GIS creation dates do not prove construction dates, and selecting only old records would under-cover the route. The center proxy therefore remains visibly provisional until an original-phase route can be reconciled. A similarly named public `CulturalTrail` layer was rejected because its coordinates were outside Indianapolis. [Official current trails layer](https://gis.indy.gov/server/rest/services/OpenData/OpenData_Transportation/MapServer/9).

## Tampa Riverwalk and Schuylkill Boardwalk

Tampa distinguishes the Kennedy Boulevard Plaza completion in 2015 from Doyle Carlton in 2016. A whole-route reported cost and a single segment milestone remain different scopes. [City timeline](https://www.tampa.gov/planning-division/programs/invision-tampa).

The Schuylkill operator confirms the October 2, 2014 opening and describes the approximately 2,000-foot boardwalk and its connecting ramp. This validates the milestone and physical project description, but does not turn the current center proxy into a verified alignment or independently audit its cost. [Opening announcement](https://www.schuylkillbanks.org/blog/schuylkill-banks-boardwalk-now-open), [project description](https://www.schuylkillbanks.org/projects/boardwalk).

## Cost and geographic limits retained

Five expansion projects still use center proxies. Original mapped geometries may also be current rather than historical surveys. Cost year and public/private scope are incomplete for several projects. The application therefore reports nominal stated project costs and does not invent inflation adjustments or public-only denominators. Cross-project CE is an exploratory comparison of online activity, not an audited public return.
