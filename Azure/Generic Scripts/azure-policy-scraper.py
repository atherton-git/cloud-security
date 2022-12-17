import re
import ssl
import requests
import pandas as pd
from bs4 import BeautifulSoup

print("Compiling a list of Azure services...")
service_list = [ ]
response = requests.get('https://github.com/Azure/azure-policy/tree/master/built-in-policies/policyDefinitions')    
service_table = BeautifulSoup(response.text, 'html.parser')   
file = service_table.find_all('a',class_="js-navigation-open Link--primary")
for i in file:
    service_list.append(i.extract().get_text().replace(" ","%20"))

service_list.remove("Regulatory%20Compliance")

print("Compiling a list of policy files for processing...")
href_list = [ ]
for i in service_list:
    github_policies = f'https://github.com/Azure/azure-policy/tree/master/built-in-policies/policyDefinitions/{i}'
    policy_response = requests.get(github_policies)
    gitlab_table = BeautifulSoup(policy_response.text, 'html.parser')
    try:
        jsonfiles = gitlab_table.find_all('a', {'href': re.compile("\.json$")})
        for i in jsonfiles:
            href_list.append(i['href'])
    except Exception:
        pass

# Remove prefix from existing list
policy_list = [str(i).removeprefix('/Azure/azure-policy/blob/master/built-in-policies/policyDefinitions/') for i in href_list]

print("Looping through the policies and parsing the raw json (this may take some time)...")
policy_objects = pd.DataFrame()
for policy in policy_list:
    ssl._create_default_https_context = ssl._create_unverified_context
    data = pd.read_json(f'https://raw.githubusercontent.com/Azure/azure-policy/master/built-in-policies/policyDefinitions/{policy}', typ='series')
    policy_objects=policy_objects.append(data,ignore_index=True)

print("Normalising the 'properties' column, and concatenating the output with 'id' and 'name'...")
policy_objects = pd.concat([policy_objects[["id","name"]],pd.json_normalize(policy_objects['properties'],max_level=2)],axis=1)

# Removing "depracated" policies
policy_objects = policy_objects[~policy_objects['metadata.version'].str.endswith('-deprecated')]

# Removing prefixes from columns
policy_objects.columns = [re.sub('^parameters.|^metadata.',"", i) for i in policy_objects.columns]

print("Writing the dataframe to csv...")
policy_objects.to_csv(f'output.csv', 
columns=["category","policyType","name","id","displayName","description","mode","effect.allowedValues","effect.defaultValue","version"],
index=False)

print("Complete!")