def get_darwin_core_terms():
    # Example hardcoded list of Darwin Core terms
    DARWIN_CORE_TERMS = [
    "basisOfRecord", "modified", "datasetName", "type", "language", "institutionID", 
    "institutionCode", "collectionCode", "license", "references", "rightsHolder", 
    "dynamicProperties", "occurrenceID", "catalogNumber", "otherCatalogNumbers", 
    "recordedBy", "recordNumber", "individualCount", "organismQuantity", 
    "organismQuantityType", "establishmentMeans", "georeferenceVerificationStatus", 
    "sex", "lifeStage", "reproductiveCondition", "preparations", "disposition", 
    "associatedTaxa", "associatedReferences", "associatedMedia", "associatedSequences", 
    "occurrenceRemarks", "organismID", "eventDate", "eventTime", "endDayOfYear", 
    "year", "month", "day", "verbatimEventDate", "habitat", "samplingProtocol", 
    "samplingEffort", "eventRemarks", "higherGeography", "continent", "country", 
    "countryCode", "stateProvince", "county", "municipality", "island", "islandGroup", 
    "waterBody", "locality", "verbatimLocality", "locationAccordingTo", "locationRemarks", 
    "minimumElevationInMeters", "maximumElevationInMeters", "minimumDepthInMeters", 
    "maximumDepthInMeters", "verbatimLatitude", "verbatimLongitude", "decimalLatitude", 
    "decimalLongitude", "coordinateUncertaintyInMeters", "verbatimCoordinates", 
    "verbatimCoordinateSystem", "geodeticDatum", "georeferenceProtocol", 
    "georeferenceSources", "georeferencedBy", "georeferencedDate", "georeferenceRemarks", 
    "kingdom", "phylum", "class", "order", "family", "genus", "specificEpithet", 
    "infraspecificEpithet", "scientificName", "scientificNameAuthorship", "taxonRank", 
    "vernacularName", "taxonRemarks", "identificationQualifier", "typeStatus", 
    "identifiedBy", "dateIdentified", "identificationRemarks"]
    DARWIN_CORE_TERMS.sort()

    return DARWIN_CORE_TERMS
