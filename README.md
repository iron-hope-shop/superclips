Clippy!

local
```shell
docker run -p 8080:8080 -e PORT=8080 -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json -v /Users/bradmin/apps/superclips/svc-brad-jackson-gpt.json:/app/credentials.json my_app

```

```shell
export GOOGLE_APPLICATION_CREDENTIALS=/Users/bradmin/apps/superclips/svc-brad-jackson-gpt.json
```

orrr
```
GCP_PROJECT=superclips FLASK_APP=main.py FLASK_ENV=development flask run --port=8080
```