# FinBif-scripts
Scripts for getting and using data in the [Finnish Biodiversity Information Facility](https://laji.fi/en). They use the [public API](https://api.laji.fi) to search the database.

## Access token
Using the [API]((https://api.laji.fi)) requires an access token. This is used to identify the user. To get one, send a POST request with your email address. Easiest is to skim down the page to [APIUser > Post api-users](https://api.laji.fi/explorer/#!/APIUser/APIUser_create_post_api_users), put  your email into the form, then click "Try it out!".
When you have received an access token to your email, paste it into the parameters at the start of the script.

## Files

### newtaxa.py
Finds species that are new to Finland or to a Finnish biogeographical province. Gets the currently accepted distributions of each species, and data on the specimens. Then compares the two. Any specimens found outside their species' accepted distribution are saved to a csv file, for further examination by a human.

Although this script saves time in finding new species occurrences, the results should not be taken at face value. A taxonomist should check the specimens flagged by the script.

The default parameters search for new mosses or liverworts. This can easily be changed in the parameters.
Currently (2021) the code is all in one oversize file. In the future, it will be tidied up by moving sections of it to separate files and classes.

### invalid_speciesnames.py
Finds species names that appear to be invalid. Gets the species ID of every specimen in the database which has been identified to species. If the ID does not exist, saves the specimen to a csv file for closer examination by a human. 

Most of the time, the invalid species names (names not found in the accepted list of species in Taxon Editor, i.e. they get no ID) will be mistypes. They can then be corrected by whoever is responsible for the specimen data.

The default parameters check mosses and liverworts. This can easily be changed in the parameters.
Currently (2021) the code is all in one file. In the future, it will be tidied up by moving sections of it to separate files and classes.
