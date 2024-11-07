# server.py
import os
from livekit import api, rtc
import asyncio
from flask import Flask, render_template, request
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)


@app.route('/getToken')
def getToken():
  token = api.AccessToken(os.getenv('LIVEKIT_API_KEY'), os.getenv('LIVEKIT_API_SECRET')) \
    .with_identity("identity") \
    .with_name("my name") \
    .with_grants(api.VideoGrants(
        room_join=True,
        room="my-room",
    ))
  return token.to_jwt()

@app.route('/')
async def hello():
    msg = request.args.get("q")
    room = request.args.get("room_id")
    lkapi = api.LiveKitAPI()
    results = await lkapi.room.list_rooms(api.ListRoomsRequest())
    if results.rooms is None:
      return render_template('index.html', msg="no participants found")
    if len(results.rooms) < 1:
      return render_template('index.html', msg="no participants found")
    
    if room is None:
       raise ValueError("room_id is required, either as argument or add room_id to query parameter")
    #  room = (results.rooms[0])
  
    # participants = await lkapi.room.list_participants(api.ListParticipantsRequest(room=room.name))
    # if participants.participants is None :
    #   return render_template('index.html', msg="no participants found")
    
    # if len(participants.participants) < 2:
    #   return render_template('index.html', msg="no participants found") 
    token = api.AccessToken(os.getenv('LIVEKIT_API_KEY'), os.getenv('LIVEKIT_API_SECRET')) \
    .with_identity(request.args.get("identity")) \
    .with_name("user-interrupt") \
    .with_grants(api.VideoGrants(
        room_join=True,
        room=room.name,
    )) 
    print(token.to_jwt())
    r = rtc.Room()
    await r.connect(url=os.getenv("LIVEKIT_URL"),token=token.to_jwt())
    await lkapi.room.send_data(api.SendDataRequest(room=room.name, data=msg.encode(), topic="role"))
    await r.disconnect()
    await lkapi.aclose()
    return render_template('index.html', msg=msg)

if __name__ == "__main__":
   asyncio.run(app.run(host="0.0.0.0", port=8888))