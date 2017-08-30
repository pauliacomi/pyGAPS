# %%

import json
import urllib

material = 'CuBTC'

with urllib.request.urlopen("http://adsorbents.nist.gov/api/material-biblio/" + material + ".json") as url:
    data = json.loads(url.read().decode())

# %%
dois = [x['DOI'] for x in data]
dois = [x[:7] + x[8:] for x in dois]
print(len(dois))

# %%
exps = []

total_dois = len(dois)
for index, doi in enumerate(dois):

    if index == 6:
        print("reached max index")
        break

    print("Starting doi number ", index, "out of ", total_dois)

    iso_number = 1
    while True:
        print("    Starting isotherm number ", iso_number)

        title = dois[index] + ".isotherm" + str(iso_number)
        iso_number += 1
        response = urllib.request.urlopen(
            "http://adsorbents.nist.gov/api/isotherm/" + title + ".json")

        iso_data = json.loads(response.read().decode())
        if len(iso_data) > 0:
            exps.append(iso_data)
        else:
            break

# %%
print(len(exps))

isotherms = []
for raw_iso in exps:
    isotherms.append(pygaps.isotherm_from_json(raw_iso))


# %%
with open('result.json', 'w') as fp:
    json.dump(exps, fp, indent=4)
