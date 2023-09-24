from google.cloud import secretmanager
from flask import Flask, jsonify
import google_crc32c
import openai
import os


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
# def setup_openai_api():
#     openai.api_type = access_secret_version("API_TYPE", "1")
#     openai.api_base = access_secret_version("API_BASE", "1")
#     openai.api_version = access_secret_version("API_VERSION", "1")
#     openai.api_key = access_secret_version("API_KEY", "1")

# def query(user_query, channel_history):
#     system_instruction = f"You are a Software Engineer. Your job is to write effective code in a pair programming environment with your teammate, Brad."
#     # Starting with the system instruction
#     messages = [{"role": "system", "content": system_instruction}]
    
#     # Convert and add the previous interactions from the history
#     for interaction in channel_history:
#         messages.append({"role": "user", "content": interaction["prompt"]})
#         messages.append({"role": "assistant", "content": interaction["response"]})

#     # Add the current user query
#     messages.append({"role": "user", "content": user_query})

#     # Limit to the last 10 interactions (or whatever limit you prefer)
#     messages = messages[-10:]
#     print(messages)

#     # Asynchronous API call
#     chat_completion_resp = openai.ChatCompletion.create(
#         engine=access_secret_version("ENGINE", "1"),
#         messages=messages,
#         temperature=0.7,
#         max_tokens=800,
#         top_p=0.95,
#         frequency_penalty=0,
#         presence_penalty=0,
#         stop=None
#     )
#     return chat_completion_resp.choices[0].message.content

app = Flask(__name__)

@app.route('/health')
def home():
    return jsonify({"status": "Bot is running!"}), 200


history = {}  # Store history for each channel

if __name__ == "__main__":
    # setup_openai_api()
    app.run(host='0.0.0.0', port=8080)



# @app.router.post("/echo")
# async def echo(request):
#     data = await request.json()
#     user_query = data.get("query")
#     if not user_query:
#         return json({"error": "Query not provided."}, status=400)
    
# c1_un = access_secret_version("C1_UN", "1")
# c2_pw = access_secret_version("C2_PW", "1")

