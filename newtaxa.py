## Python code for finding new species occurrences in Finland and in Finland's biogeographical provinces
## Uses the laji.fi API: https://api.laji.fi
## Gets all the specimens from laji.fi which have location data,
## and compares them to the species distributions which have been saved in Taxon Editor.
## Saves two files, one for potentially new bioprovince records, and one for potentially new species for Finland.
## Before running the code, check that the parameters (e.g. access code) are OK.

## Code CC0 Tapani Hopkins, 18.6.2021


## Import
from subprocess import check_output as call
from io import open
import json
import os


## Parameters

# access token used to get data from the API
access_token = "writeAccessTokenHere"  # access tokens can be got from https://api.laji.fi

# taxa we're interested in (laji.fi identifiers)
taxa = ["MX.44394", "MX.44109"]  # liverworts and bryophytes

# folder in which to save the results (ignored if running from command line)
folderpath = "/Users/tapani/T/Courses/2020/new_mosses"

# texts in Taxon Editor which should be interpreted as representing an occurrence
# There are a bewildering variety of occurrence classifications, see
# http://schema.laji.fi/alt/MX.typeOfOccurrenceEnum
occursStrings = ["MX.typeOfOccurrenceOccurs", "MX.typeOfOccurrenceStablePopulation", "MX.typeOfOccurrenceCommon", "MX.typeOfOccurrenceRare", "MX.typeOfOccurrenceVeryRare", "MX.typeOfOccurrenceImport", "MX.typeOfOccurrenceAnthropogenic", "MX.typeOfOccurrenceAlienOldResident", "MX.typeOfOccurrenceSpontaneousNewEphemeral", "MX.typeOfOccurrenceAlienNewEphemeral", "MX.typeOfOccurrenceAlienNewResident", "MX.typeOfOccurrenceSmallDegreeCultivatedOrigin", "MX.typeOfOccurrenceNotableDegreeCultivatedOrigin", "MX.typeOfOccurrenceCompletelyCultivatedOrigin", "MX.typeOfOccurrenceOnlyCultivated"]


## Helper functions

# get stuff from the API
def get(apiurl):
    res = call(["curl", "-X", "GET", "--header", "Accept: application/json", apiurl])
    return json.loads(res)

# get the order into which a list will be sorted
def order(x, reverse=False):
    o = sorted(range(len(x)), key=x.__getitem__, reverse=reverse)
    return o

# sort a list into a specific order
def sort(x, o):
    # create new empty list
    newToProvinces = []
    
    # add the items in 'x' in the correct order
    for i in o:
        newToProvinces.append(x[i])
    
    # return the new list
    return(newToProvinces)

# check if a specific combination of keys exists in a dictionary
# keys:  the keys in hierarchical order, e.g. ['unit','linkings', 'taxon', 'id']
def exists(x, keys):
    # start from the top level of keys
    level = x
    
    # drill down through the levels of x
    for key in keys:
        # if the key exists, go down one level
        if key in level:
            level = level[key]
            
        # if the key was not found, return False
        else:
            return False
    
    # return True if all the keys were found
    return True

# check if a specific combination of keys exists in a dictionary,
# return its value if it exists, or 'ifnot' if it doesn't.
# keys:  the keys in hierarchical order, e.g. ['unit','linkings', 'taxon', 'id']
def check(x, keys, ifnot=""):
    # start from the top level of keys
    level = x
    
    # drill down through the levels of x
    for key in keys:
        # if the key exists, go down one level
        if key in level:
            level = level[key]
            
        # if the key was not found, return the value in 'ifnot'
        else:
            return ifnot
    
    # return the value if all the keys were found
    return level


## Initialise

# if running from command line, save the occurrences in the folder this script is in
try:
    path = os.path.dirname(__file__)

# if copy-pasting into python, save into the folder given in the parameters
except NameError:
    path = folderpath


## Check for new occurrences in biogeographical provinces

# get the biogeographical provinces from the API
# format: {province id: province name}
print("\nDownloading biogeographical provinces")
url = "https://api.laji.fi/v0/areas?type=biogeographicalProvince&lang=fi&pageSize=50&access_token=" + access_token
js = get(url)
provinces = {}
for area in js['results']:
    provinces[area['id']] = area['name']

# let the user know we will get the currently known distributions (=Taxon Editor data) from the API
print("\nDownloading Taxon Editor data")

# set up two variables with format:  {species: {province: occurrenceCode}}
occurrencesTE = {}  # only those species-province pairs where the species occurs
occurrencesTEall = {}  # all species-province pairs (used to get occurrence codes)

# get the known distributions for the taxa we're interested in (liverworts and bryophytes)
for taxon in taxa:
    # get from api
    url = "https://api.laji.fi/v0/taxa/" + taxon + "/species?lang=fi&langFallback=true&taxonRanks=MX.species&includeHidden=false&includeMedia=false&includeDescriptions=false&includeRedListEvaluations=false&selectedFields=id%2CscientificNameDisplayName%2Coccurrences&onlyFinnish=true&sortOrder=taxonomic&pageSize=1000&access_token=" + access_token
    js = get(url)
    
    # save into the two variables one species at a time
    for sp in js['results']:
        species = sp['id']
        
        # save those species that have occurence data (others are e.g. only presumed present in Finland)
        if ("occurrences" in sp):
            # initialise occurrence variable ("province: occurrenceCode" for provinces were species occurs),
            # and occurrence code variable ("province: occurrenceCode" for all provinces)
            ocs = {}
            ocsAll = {}
            
            # loop through the provinces
            for i in sp['occurrences']:
                # add to 'ocs' if the species occurs here
                if (i['status'] in occursStrings):
                    ocs[i['area']] = i['status']
                
                # add to 'ocsAll' whether or not the species occurs here
                ocsAll[i['area']] = i['status']
                
            # add to the lists
            occurrencesTE[species] = ocs
            occurrencesTEall[species] = ocsAll

# let the user know we will get the specimen data from the API
print("\nDownloading specimen data")

# initialise variables for specimen data download
page = 1
loop = True

# set up variable 'occurrences' with format:
# { species: { province: { occurrenceCode: XXX, speciesName: XXX, specimens : [{specimenID: XXX, modifiedDate: XXX, gatheredDate: XXX, reliability: XXX}] } } }
occurrences = {}

# get data from the API, one page (10000 specimens) at a time
while loop:
    # get from api
    url = "https://api.laji.fi/v0/warehouse/query/unit/list?selected=document.createdDate%2Cdocument.documentId%2Cdocument.modifiedDate%2Cgathering.eventDate.end%2Cgathering.interpretations.biogeographicalProvince%2Cunit.interpretations.reliability%2Cunit.linkings.taxon.id%2Cunit.linkings.taxon.scientificName%2Cunit.unitId&pageSize=10000&page=" + str(page) + "&cache=false&taxonId=" + ",".join(taxa) + "&useIdentificationAnnotations=true&includeSubTaxa=true&includeNonValidTaxa=true&taxonRankId=MX.species&biogeographicalProvinceId=" + "%2C".join(list(provinces.keys())) + "&recordBasis=PRESERVED_SPECIMEN&individualCountMin=1&qualityIssues=NO_ISSUES&access_token=" + access_token
    js = get(url)
    
    # loop through each specimen, add its data to 'occurrences'
    for sp in js["results"]:
        # only add specimens whose species name is typed correctly (by checking if sp is in TE)
        if exists(sp, ['unit', 'linkings', 'taxon', 'id']):
            # extract (and tidy up) the species id and province id of this specimen
            species = sp['unit']['linkings']['taxon']['id'].replace("http://tun.fi/", "")
            area = sp['gathering']['interpretations']['biogeographicalProvince'].replace("http://tun.fi/", "")
            
            # extract the occurrenceCode and species name
            occurrenceCode = check(occurrencesTEall, [species, area])
            speciesName = sp['unit']['linkings']['taxon']['scientificName']
            
            # extract the unit id for multi-species observations
            if ("unitId" in sp['unit']):
                specimenID = sp['unit']['unitId']
            
            # otherwise, extract the specimen id
            else:
                specimenID = sp['document']['documentId']
                
            # extract the date when the data was modified and the specimen gathered
            modifiedDate = check(sp, ['document', 'modifiedDate'])
            gatheredDate = check(sp, ['gathering', 'eventDate', 'end'])
            
            # extract the data on how reliable the observation is
            reliability = sp['unit']['interpretations']['reliability']
            
            # if this species is not yet in occurrences,
            # add a new species then save all the extracted data there
            if (species not in occurrences):
                occurrences[species] = {area: { "occurrenceCode": occurrenceCode, "speciesName": speciesName, "specimens": [{"specimenID": specimenID, "modifiedDate": modifiedDate, "gatheredDate": gatheredDate, "reliability": reliability}] }}
            
            # if the species already exists in occurrences,
            # add the extracted data to it
            else:
                oc = occurrences[species]
                
                # add the province if it does not already exist, then add the data to it
                if (area not in oc):
                    oc[area] = { "occurrenceCode": occurrenceCode, "speciesName": speciesName, "specimens": [{"specimenID": specimenID, "modifiedDate": modifiedDate, "gatheredDate": gatheredDate, "reliability": reliability}] }
                    
                # else if the province already exists, add the data to it
                else:
                    oc[area]['specimens'].append( {"specimenID": specimenID, "modifiedDate": modifiedDate, "gatheredDate": gatheredDate, "reliability": reliability} )
                    
    # end the loop if the last page has been reached
    if ( js['currentPage'] >= js['lastPage'] ):
        loop = False
    
    # go to the next page of specimens
    page += 1

# start comparing the specimen data to the known occurrences (Taxon editor data)
# initialise variable for the new occurrences (new species-province pairs), format:
# [ [species, speciesName, province, occurrenceCode, [specimens], [modifiedDates], [gatheredDates], [reliabilities]] ]
notinTE = []

# check each species to see if there are specimens outside the known distribution
for sp in occurrences.keys():
    # only check species that are in TE (others are probably mistypes)
    if (sp in occurrencesTE.keys()):
        # loop through each province for this species
        for area in occurrences[sp].keys():
            # if the occurrence is new, extract the data and save in 'notinTE'
            if (area not in occurrencesTE[sp]):
                # extract the occurrence code and species name
                occurrenceCode = occurrences[sp][area]['occurrenceCode']
                speciesName = occurrences[sp][area]['speciesName']
                
                # extract the specimens found here
                sps = occurrences[sp][area]['specimens']
                
                # extract the data for the specimens
                specimens = []
                modifiedDates = []
                gatheredDates = []
                reliabilities = []
                for specimen in sps:
                    specimens.append(specimen['specimenID'])
                    modifiedDates.append(specimen['modifiedDate'])
                    gatheredDates.append(specimen['gatheredDate'])
                    reliabilities.append(specimen['reliability'])
                    
                # save into 'notinTE'
                notinTE.append([sp, speciesName, area, occurrenceCode, specimens, modifiedDates, gatheredDates, reliabilities])

# initialise a variable for the new occurrences
# the data in 'notinTE' will be filtered, sorted, converted into human-readable format, then saved here
newToProvinces = []

# filter out e.g. old distribution records
for i in notinTE:
    # get the data of this species
    line = list(i)
    
    # initialise boolean showing whether this data should be included or not
    include = True
    
    # filter 1: ignore old distribution records if all the specimens are from before 1940
    if ( (line[3] == 'MX.typeOfOccurrenceOldRecords') or (line[3] == 'MX.typeOfOccurrenceExtirpated') ):
        # initialise whether there are specimens from 1940 or later
        recentYear = False
        
        # check if any of the specimens are recent
        for gatheredDate in line[6]:
            # only check specimens with a date
            if (not gatheredDate==""):
                if (int(gatheredDate[0:4]) >= 1940):
                    recentYear = True
        
        # filter out this species if no specimens were recent (and its occurrence data is old)
        if (not recentYear):
            include = False
            
    # after the filters, save the species if not filtered away
    # also take the opportunity to sort the specimens by date
    if (include):
        # sort the specimens by modifiedDate
        o = order(line[5], reverse=True)
        line[4] = sort(line[4], o)
        line[5] = sort(line[5], o)
        line[6] = sort(line[6], o)
        line[7] = sort(line[7], o)
        
        # save into 'newToProvinces' in human-readable format
        line[0] = "http://tun.fi/" + line[0]
        line[2] = provinces[line[2]]
        line[4] = " ".join(line[4])
        line[5] = " ".join(line[5])
        line[6] = " ".join(line[6])
        line[7] = " ".join(line[7])
        newToProvinces.append(line)

# get the most recent dates when specimens were modified for each species
# these will be used to sort the data
modifiedDate = []
for i in newToProvinces:
    modifiedDate.append(i[5])

# sort the new occurrences by the most recent date when a specimen was modified
o = order(modifiedDate, reverse=True)
newToProvinces = sort(newToProvinces, o)

# get the occurrence codes of each species
# these will be used to sort the data
occurrenceCode = []
for i in newToProvinces:
    occurrenceCode.append(i[3])

# sort the new occurrences by occurrence code
o = order(occurrenceCode)
newToProvinces = sort(newToProvinces, o)

# open a file in which the new occurrences will be saved
filepath = os.path.join(path, "new_to_bioprovinces.csv")
f = open(filepath, "w", encoding="utf-8")

# write the header to the file
tmp = f.write(u"species,speciesName,province,occurrenceCode,specimens,modifiedDate,collectedDate,reliability" + "\n")

# write the data of each species with new occurrences to the file
for line in newToProvinces:
    tmp = f.write(u",".join(line) + "\n")

# close the file
f.close()


## Check for new species to Finland

# let the user know we will get specimens which are new to Finland from the API
print("\nDownloading data on specimens new to Finland")

# set up variable for the species not known to be in Finland with format:
# { species: [ species, speciesName, [specimenIDs], [modifiedDates], [gatheredDates], [reliabilities] ] }
notinFI = {}

# get Finnish specimens of species not known to occur in Finland from the API
url = "https://api.laji.fi/v0/warehouse/query/unit/list?selected=document.createdDate%2Cdocument.documentId%2Cdocument.modifiedDate%2Cgathering.eventDate.end%2Cgathering.interpretations.biogeographicalProvince%2Cunit.interpretations.reliability%2Cunit.linkings.taxon.id%2Cunit.linkings.taxon.scientificName%2Cunit.unitId&pageSize=100&page=1&cache=false&taxonId=" + ",".join(taxa) + "&useIdentificationAnnotations=true&includeSubTaxa=true&includeNonValidTaxa=true&finnish=false&taxonRankId=MX.species&countryId=ML.206&recordBasis=PRESERVED_SPECIMEN&individualCountMin=1&qualityIssues=NO_ISSUES&access_token=" + access_token
js = get(url)

# loop through each specimen, add its data to 'notinFI'
for sp in js["results"]:
    # # only add specimens whose species name is typed correctly (by checking if sp is in TE)
    if exists(sp, ['unit', 'linkings', 'taxon', 'id']):
        # extract (and tidy up) the species id for this specimen
        species = sp['unit']['linkings']['taxon']['id'].replace("http://tun.fi/", "")
        
        # extract the species name
        speciesName = sp['unit']['linkings']['taxon']['scientificName']
        
        # extract the unit id for multi-species observations
        if ("unitId" in sp['unit']['linkings']):
            specimenID = sp['unit']['linkings']['unitId']
            
        # otherwise, extract the specimen id
        else:
            specimenID = sp['document']['documentId']
            
        # extract the date when the data was modified and the specimen gathered
        modifiedDate = check(sp, ['document', 'modifiedDate'])
        gatheredDate = check(sp, ['gathering', 'eventDate', 'end'])
        
        # extract the data on how reliable the observation is
        reliability = sp['unit']['interpretations']['reliability']
        
        # if this specimen's species is not already in 'notinFI', add the species then the extracted data
        if (species not in notinFI):
            notinFI[species] = [ species, speciesName, [specimenID], [modifiedDate], [gatheredDate], [reliability] ]
            
        # if the species already exists, add the extracted data to it
        else:
            # add the data to a species already in 'notinFI'
            notinFI[species][2].append(specimenID)
            notinFI[species][3].append(modifiedDate)
            notinFI[species][4].append(gatheredDate)
            notinFI[species][5].append(reliability)

# initialise a variable for the new occurrences
# the data in notinFI will be sorted and converted into human-readable format, then saved here
newToFI = []

#  sort the specimens of each species by the date when their data was modified, and save in human-readable format
for i in notinFI:
    # get the data of this species
    line = list(notinFI[i])
    
    # sort the specimens by date modified
    o = order(line[3], reverse=True)
    line[2] = sort(line[2], o)
    line[3] = sort(line[3], o)
    line[4] = sort(line[4], o)
    line[5] = sort(line[5], o)
    
    # add this species to 'newToFI' in human-readable format
    line[0] = "http://tun.fi/" + line[0]
    line[2] = " ".join(line[2])
    line[3] = " ".join(line[3])
    line[4] = " ".join(line[4])
    line[5] = " ".join(line[5])
    newToFI.append(line)

# get the most recent dates when specimens were modified for each species
# these will be used to sort the data
modifiedDate = []
for i in newToFI:
    modifiedDate.append(i[3])

# sort the new occurrences by the most recent date when a specimen was modified
o = order(modifiedDate, reverse=True)
newToFI = sort(newToFI, o)

# open a file in which the new occurrences will be saved
filepath = os.path.join(path, "new_to_fi.csv")
f = open(filepath, "w", encoding="utf-8")

# write the header to the file
tmp = f.write(u"species,speciesName,specimens,modifiedDate,collectedDate,reliability" + "\n")

# write the data of each species with new occurrences to the file
for line in newToFI:
    tmp = f.write(u",".join(line) + "\n")

# close the file
f.close()
