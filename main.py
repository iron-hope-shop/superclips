from aiohttp import ClientSession, TCPConnector
from blacksheep.server.responses import json
from blacksheep.server.responses import text
from blacksheep.server import Application
from google.cloud import secretmanager
import google_crc32c
import asyncio
import base64
import openai

def access_secret_version(
    secret_id: str, version_id: str
) -> secretmanager.AccessSecretVersionResponse:
    """
    Access the payload for the given secret version if one exists. The version
    can be a version number as a string (e.g. "5") or an alias (e.g. "latest").
    """

    # Import the Secret Manager client library.
    from google.cloud import secretmanager

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version.
    name = f"projects/superclips/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version.
    response = client.access_secret_version(request={"name": name})

    # Verify payload checksum.
    crc32c = google_crc32c.Checksum()
    crc32c.update(response.payload.data)
    if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
        print("Data corruption detected.")
        return response

    # WARNING: Do not print the secret in a production environment
    payload = response.payload.data.decode("UTF-8")
    return payload

# Set up OpenAI API configurations
def setup_openai_api():
    openai.api_type = "azure"
    openai.api_base = access_secret_version("api_base", "1")
    openai.api_version = "2023-07-01-preview"
    openai.api_key = access_secret_version("OPENAI_API_KEY", "1")
    # Set up aiohttp session with an option to bypass SSL verification (for development purposes only!)
    connector = TCPConnector(ssl=False)
    openai.aiosession.set(ClientSession(connector=connector))

async def query(user_query):
    system_instruction = f"You are a Software Engineer. Your job is to write effective code in a pair programming environment with your teammate, Brad."
    # Asynchronous API call
    chat_completion_resp = await openai.ChatCompletion.acreate(
        engine="EchoChamber",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_query}
        ],
        temperature=0.7,
        max_tokens=8000,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    return chat_completion_resp.choices[0].message.content


async def main(user_query):
    setup_openai_api()
    response = await query(user_query)
    await openai.aiosession.get().close()
    return response

app = Application()

# Expected credentials (hardcoded for demonstration purposes)
uid = access_secret_version("uid", "1")
code = access_secret_version("passwd", "1")

async def basic_auth_middleware(request, handler):
    
    auth_header_value = request.headers.get(b'authorization')
    auth_header = auth_header_value[0] if isinstance(auth_header_value, tuple) else auth_header_value
    
    
    if not auth_header:
        return text("Unauthorized", status=401)
    
    auth_type, _, auth_string = auth_header.partition(b' ')
    if auth_type.lower() != b'basic':
        return text("Unauthorized", status=401)
    
    decoded_auth_string = base64.b64decode(auth_string).decode('utf-8')
    username, _, password = decoded_auth_string.partition(':')
    
    if username != uid or password != code:
        return text("Unauthorized", status=401)
    
    return await handler(request)


app.middlewares.append(basic_auth_middleware)

@app.router.post("/echo")
async def echo(request):
    data = await request.json()
    user_query = data.get("query")
    if not user_query:
        return json({"error": "Query not provided."}, status=400)
    
    response = await main(user_query)
    return json({"response": response})

@app.route("/")
async def health():
    return json({"status": "healthy"})

if __name__ == "__main__":
    asyncio.run(app.start(port=8080))