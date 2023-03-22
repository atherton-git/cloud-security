import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

def main():
    print("Compiling a list of Azure services...")
    service_list = get_service_list()

    print("Compiling a list of policy files for processing...")
    policy_list = get_policy_list(service_list)

    print("Looping through the policies and parsing the raw json (this may take some time)...")
    policy_objects = fetch_policy_objects(policy_list)

    print("Normalising the 'properties' column, and concatenating the output with 'id' and 'name'...")
    policy_objects = normalize_policy_objects(policy_objects)

    print("Writing the dataframe to csv...")
    policy_objects.to_csv('output.csv', 
                          columns=["category","policyType","name","id","displayName","description","mode",
                                   "effect.allowedValues","effect.defaultValue","version"],
                          index=False)

    print("Complete!")

def get_service_list():
    url = 'https://github.com/Azure/azure-policy/tree/master/built-in-policies/policyDefinitions'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    file = soup.find_all('a', class_="js-navigation-open Link--primary")
    service_list = [i.extract().get_text().replace(" ", "%20") for i in file]
    service_list.remove("Regulatory%20Compliance")
    return service_list

def get_policy_list(service_list):
    policy_list = []
    for service in service_list:
        url = f'https://github.com/Azure/azure-policy/tree/master/built-in-policies/policyDefinitions/{service}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        jsonfiles = soup.find_all('a', {'href': re.compile("\.json$")})
        for i in jsonfiles:
            policy_list.append(i['href'])
    return [str(i).removeprefix('/Azure/azure-policy/blob/master/built-in-policies/policyDefinitions/') for i in policy_list]

def fetch_policy_objects(policy_list):
    policy_dataframes = []
    for policy in policy_list:
        data = pd.read_json(f'https://raw.githubusercontent.com/Azure/azure-policy/master/built-in-policies/policyDefinitions/{policy}', typ='series')
        policy_dataframes.append(data)
    policy_objects = pd.concat(policy_dataframes, axis=1).transpose().reset_index(drop=True)
    return policy_objects

def normalize_policy_objects(policy_objects):
    normalized_objects = pd.concat([policy_objects[["id", "name"]], pd.json_normalize(policy_objects['properties'], max_level=2)], axis=1)
    normalized_objects = normalized_objects[~normalized_objects['metadata.version'].str.endswith('-deprecated')]
    normalized_objects.columns = [re.sub('^parameters.|^metadata.', "", i) for i in normalized_objects.columns]
    return normalized_objects

if __name__ == '__main__':
    main()
