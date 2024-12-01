from datetime import datetime
import time
import requests
import json


# Define the Django API endpoint
end_point='http://127.0.0.1:8000/'

create_trad_url =end_point+ "api/create-trade/"  # Replace with the actual endpoint
update_trad_url =end_point+ "api/update-trade/"  # Replace with the actual endpoint

get_trad_url =end_point+ "api/list-trade/?is_open=true"  # Replace with the actual endpoint
get_symbol_url =end_point+ "api/get-top/?ordering=-win_rate/"  # Replace with the actual endpoint


# JSON payload to send
# payload = {
#     "symbol": "BTCUSDT",
#     "quantity": 0.01,
#     "initial_price": 58000,
#     "target_price": 59000,
#     "stop_price": 57000,
#     "start_time":str( datetime.fromtimestamp( time.time())),
#     "timeout": 120,
#     "investment": 1000
# }

# print(payload)
# Headers for the request
headers = {
    "Content-Type": "application/json"
}

# # Send POST request and process response
# try:
#     # response = requests.post(create_trad_url, data=json.dumps(payload), headers=headers)
#     # response.raise_for_status()  # Raise an error for HTTP codes >= 400

#     # # Process response
#     # data = response.json()
#     # print("Trade created successfully:")
#     # print(json.dumps(data, indent=4))

#     response = requests.get(get_trad_url, headers=headers)
#     # response.raise_for_status()  # Raise an error for HTTP codes >= 400

#     # Process response
#     data = response.json()
#     print("Trade created successfully:")
#     print(json.dumps(data, indent=4))

# except requests.exceptions.RequestException as e:
#     print(f"Error occurred: {e}")





def get_top_symbols(limit=100):
    
    response = requests.get(get_trad_url, headers=headers)
    data = response.json()
    top_symbols=[]
    for symbol in data:
        if len(top_symbols) >= limit:
            break
        top_symbols.append(symbol)


def get_open_trad():
    
    response = requests.get(get_trad_url, headers=headers)
    data = response.json()
    open_trad={}
    for trad in data:
        open_trad[trad['symbol']] = trad

    return open_trad


# print(get_open_trad())


def create_trad(data):
    response = requests.post(create_trad_url, data=json.dumps(data), headers=headers)
    response.raise_for_status() 
    return json.dumps(response.json(), indent=4)






# print(create_trad(payload))


def close_trad(data):
    url = update_trad_url + str(data['id']) +"/"
    payload = {
        'is_open': False
    }
    response = requests.put(url, data=json.dumps(payload), headers=headers)
    response.raise_for_status()
    
    return json.dumps(response.json(), indent=4)

# payload = {
#     "id": 2,
#     "symbol": "BTCUSDT",
#     "quantity": 0.01,
#     "initial_price": 58000.0,
#     "target_price": 59000.0,
#     "stop_price": 57000.0,
#     "start_time": "2024-12-01T23:31:46.637979+03:00",
#     "timeout": "120",
#     "investment": 1000.0,
#     "is_open": True,
#     "created_time": "2024-12-01T23:31:46.641735+03:00",
#     "updated_time": "2024-12-01T23:31:46.641745+03:00"
# }

# print(close_trad(payload))

# close_trad(payload)


# print(get_open_trad())
