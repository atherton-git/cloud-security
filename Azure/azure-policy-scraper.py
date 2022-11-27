import re
import ssl
import requests
import pandas as pd
from bs4 import BeautifulSoup

print("https://github.com/Azure/azure-policy/tree/master/built-in-policies/policyDefinitions")
service = (input("Specify the service type from the URL above:"))
service = service.replace(" ","%20")

# Scraping azure git for policies
github_url = f'https://github.com/Azure/azure-policy/tree/master/built-in-policies/policyDefinitions/{service}'
response = requests.get(github_url)
gitlab_table = BeautifulSoup(response.text, 'html.parser')
jsonfiles = gitlab_table.find_all(title=re.compile("\.json$"))

filename = [ ]
for i in jsonfiles:
        filename.append(i.extract().get_text())

# Loop through the policies and parse the raw data
policy_objects = pd.DataFrame()
for i in filename:
    ssl._create_default_https_context = ssl._create_unverified_context
    data = pd.read_json(f'https://raw.githubusercontent.com/Azure/azure-policy/master/built-in-policies/policyDefinitions/{service}/{i}', typ='series')
    policy_objects=policy_objects.append(data,ignore_index=True)

# Normalising the "properties" column, concatenating the output with "id" and "name"
policy_objects = pd.concat([policy_objects[["id","name"]],pd.json_normalize(policy_objects['properties'],max_level=1)],axis=1)

# Removing "depracated" policies
policy_objects = policy_objects[~policy_objects['metadata.version'].str.endswith('-deprecated')]

# Writing dataframe to csv
policy_objects.to_csv(f'output_{service}.csv', columns=["metadata.category","name","id","displayName","description","metadata.version"], index=False)