## Python code for finding specimens in FinBif which do not have valid species names
## Uses the laji.fi API: https://api.laji.fi
## Gets all the specimens with potentially mistyped species names,
## and saves them into a csv file
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

# whether to get only specimens which can be placed in a Finnish biogeographical province, or all specimens
onlyFIprovinces = True


## Helper functions

# function for getting stuff from the API
def get(apiurl):
    res = call(["curl", "-X", "GET", "--header", "Accept: application/json", apiurl])
    return json.loads(res)

# function for checking if a specific combination of keys exists in a dictionary
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


## Initialise

# if running from command line, save the occurrences in the folder this script is in
try:
    path = os.path.dirname(__file__)

# if copy-pasting into python, save into the folder given in the parameters
except NameError:
    path = folderpath
    
    
## Check if specimens have valid species names

# get the biogeographical provinces from the API
# format: {province id: province name}
print("\nDownloading biogeographical provinces")
url = "https://api.laji.fi/v0/areas?type=biogeographicalProvince&lang=fi&pageSize=50&access_token=" + access_token
js = get(url)
provinces = {}
for area in js['results']:
    provinces[area['id']] = area['name']

# if asked to only include specimens placed in a biogeographical province,
# add the relevant string to the API url
if (onlyFIprovinces):
    getProvince = "&biogeographicalProvinceId=" + "%2C".join(list(provinces.keys()))
    
# otherwise, get all specimens
else:
    getProvince = ""

# initialise variables for specimen data download
page = 1
loop = True

# initialise list into which the specimen ids of specimens without a valid species ID will be saved
noTaxon = []

# get specimens from the API, one page (10000 specimens) at a time
while loop:
    # get from API
    url = "https://api.laji.fi/v0/warehouse/query/unit/list?selected=document.documentId%2Cunit.linkings.taxon.id%2Cunit.unitId&pageSize=10000&page=" + str(page) + "&cache=false&taxonId=" + ",".join(taxa) + "&useIdentificationAnnotations=true&includeSubTaxa=true&includeNonValidTaxa=true&taxonRankId=MX.species" + getProvince + "&recordBasis=PRESERVED_SPECIMEN&individualCountMin=1&qualityIssues=NO_ISSUES&access_token=" + access_token
    js = get(url)
    
    # stop when the last page is done
    if ( js['currentPage'] >= js['lastPage'] ):
        loop = False
        
    # go to next page
    page += 1
    
    # loop through the specimens, check if they have a valid species ID
    for sp in js['results']:
        # save specimens that do not have a species ID to 'noTaxon'
        if not exists(sp, ['unit', 'linkings','taxon','id']):
            # save the unit ID if the specimen is a multi-species observation
            if exists(sp, ['unit','unitId']):
                id = sp['unit']['unitId']
                
            # otherwise, save the specimen ID
            else:
                id = sp['document']['documentId']
                
            # add the specimen to 'noTaxon'
            noTaxon.append(id)

# open a file in which the specimens without a valid species ID will be saved
filepath = os.path.join(path, "mistyped_speciesnames.csv")
f = open(filepath, "w", encoding="utf-8")

# write the header to the file
tmp = f.write(u"species" + "\n")

# write the specimens to the file
for line in sorted(noTaxon):
    tmp = f.write(line + u"\n")

# close the file
f.close()

