from firebase.firebase import FirebaseApplication, FirebaseAuthentication
import pandas
auth = FirebaseAuthentication(secret="RmLjwuIq9T8fzua4ev3BBEqxyEKsLdr7BegTypcF",email="vophanphuochai2003@gmail.com")
app = FirebaseApplication('https://esp-sensor-station-default-rtdb.asia-southeast1.firebasedatabase.app/', authentication=auth)
PUSH_CHARS = '-0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz'
BASE64 =     "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
result = app.get("/0001",None)
result = result["push"]
df = pandas.DataFrame(result).T
timestamps = []
for key in list(result.keys()):
    timestamp_b64 = key[0:8]
    timestamp = 0
    for i in range(0,8):
        timestamp += PUSH_CHARS.index(timestamp_b64[i]) * (64**(7-i))
    timestamps.append(timestamp)
df["timestamp"] = timestamps
df = df.loc[:, ['timestamp','id', 'temperature', 'humidity','pressure','rain','sustain_windDir','sustain_windSpd','gust_windDir','gust_windSpd']]
df = df.set_index("timestamp")
df.to_excel("Firebase_data.xlsx")