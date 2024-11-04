 
# Dan-LiveKit with Custom LLM, TTS, STT

This project is forked from LiveKit. It is customized to use custom LLM, TTS, STT by setting env vars.


- Install

```bash
pip install -r requirements.txt
```


- Run Agent dev

```bash
python3 agent.py dev
````

- Run Agent prod

```bash
python3 agent.py start
```
 
- Run in docker

1. Build the image.
```bash
  docker build . -t livekit-agent 
```

2. Run the image.
```bash
  docker run --name livekit-agent livekit-agent
```

