import os
import requests
import sys
import platform

apiKey = the-HKBU-api-key
basicUrl = "https://genai.hkbu.edu.hk/general/rest"
# modelName = "gpt-35-turbo-16k"
modelName = "gpt-4-o-mini"
apiVersion = "2024-05-01-preview"


# requests
headers = {'Content-Type': 'application/json', 'api-key': apiKey}

conversation = [
    {"role": "user", "content": "Hi, how are you?"}
]
body = {'messages': conversation}

# get response
url = basicUrl + "/deployments/" + modelName + "/chat/completions/?api-version=" + apiVersion
response = requests.post(url, json=body, headers=headers)


def submit(message):
    conversation = [{"role": "user", "content": message}]
    url = basicUrl + "/deployments/" + modelName + "/chat/completions/?api-version=" + apiVersion
    headers = { 'Content-Type': 'application/json', 'api-key': apiKey }
    payload = { 'messages': conversation }
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content']
    else:
        return 'Error:', response
    

def hkproperty_legalasst(user_input):
    # Define the conversation
    conversation = [
        {'role': 'system', 'content': 'You are a chatbot in a chat group, familiar with Hong Kong Regulations and Property Laws.\n You act as a legal consultant to answer property buy/sell or lease questions professionally.\n You always answer questions based on Hong Kong Regulation only in legal context.\n To be accurate, include by not limited to Hong Kong Cap. 511 Estate Agents Ordinance.\n Introduce yourself as ‘Dr Law’ and always use happy emojis to answer the user in the first question.\n You must always answer correctly based on actual Hong Kong Regulations and best practices, if you are not absolutely sure, please state your educated answer as ‘suggestion’.\n As a consultant, you need to link up users with similar interests in buy/sell/lease in the same district, start to encourage the user to join district group after answering 3 questions from the user. \n The user that is interested to join the district group, ask them to click abc.com. \n If the user asks in Chinese, always answer in Traditional Chinese. '},
        {'role': 'user', 'content': user_input},
    ]

    # Generate a response from the assistant
    def submit_conversation(conversation):
        url = basicUrl + "/deployments/" + modelName + "/chat/completions/?api-version=" + apiVersion
        headers = { 'Content-Type': 'application/json', 'api-key': apiKey }
        payload = { 'messages': conversation }
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            return 'Error:', response

    # Extract the generated reply from the response
    assistant_reply = submit_conversation(conversation=conversation)

    # Print the assistant's reply
    print(assistant_reply)
