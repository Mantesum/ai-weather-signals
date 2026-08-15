# ProjectEOL integration

The existing Weather project remains unchanged. Its Django `Location` has `geonames_id`, slug, names, coordinates and timezone. This service uses its own stable `city_id` and optional `geonames_id`, so integration does not import Django models or share a database.

Recommended next step: export a versioned GeoNames-compatible JSON/TSV catalogue from Weather (or import the same upstream GeoNames snapshot here), with `geonames_id`, localized names, coordinates and timezone. Expose signals through `/api/v1/events` and `/summary`; Weather should consume this stable API with a short timeout/cache and treat signals as observational context only. It must not numerically correct Zarr forecasts in the MVP.
