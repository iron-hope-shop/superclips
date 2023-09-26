from google.cloud import secretmanager
from flask import Flask, jsonify
from flask import request, abort
import google_crc32c
import openai
import nltk
from nltk.corpus import stopwords

nltk.download("stopwords")
# Load NLTK stopwords
STOPWORDS = set(stopwords.words("english"))


# Fetch all required secrets at once
def fetch_secrets():
    secrets = [
        "API_TYPE",
        "API_BASE",
        "API_VERSION",
        "API_KEY",
        "ENGINE",
        "C1_UN",
        "C2_PW",
    ]
    return {secret: access_secret_version(secret, "1") for secret in secrets}


SECRETS = fetch_secrets()


def remove_stopwords(text):
    return " ".join([word for word in text.split() if word.lower() not in STOPWORDS])


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


def authenticate():
    auth = request.authorization
    if not auth or not (
        auth.username == SECRETS["C1_UN"] and auth.password == SECRETS["C2_PW"]
    ):
        abort(401)


# Set up OpenAI API configurations
def setup_openai_api():
    openai.api_type = SECRETS["API_TYPE"]
    openai.api_base = SECRETS["API_BASE"]
    openai.api_version = SECRETS["API_VERSION"]
    openai.api_key = SECRETS["API_KEY"]


def query(user_query, channel_history):
    system_instruction = f"Answer briefly and to the point."
    # Starting with the system instruction
    messages = [{"role": "system", "content": system_instruction}]

    # Convert and add the previous interactions from the history
    for interaction in channel_history:
        messages.append({"role": "user", "content": interaction["prompt"]})
        messages.append({"role": "assistant", "content": interaction["response"]})

    # Remove stopwords from user query
    user_query = remove_stopwords(user_query)

    # Add the current user query
    messages.append({"role": "user", "content": user_query})

    # Limit to the last 10 interactions (or whatever limit you prefer)
    messages = messages[-10:]
    print(messages)

    # Asynchronous API call
    chat_completion_resp = openai.ChatCompletion.create(
        engine=SECRETS["ENGINE"],
        messages=messages,
        temperature=0.95,
        max_tokens=500,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
    )
    return chat_completion_resp.choices[0].message.content


app = Flask(__name__)


@app.route("/echo", methods=["POST"])
def echo():
    authenticate()  # Ensure the user is authenticated
    data = request.json
    user_query = data.get("input", "")
    channel_history = data.get("history", [])
    response = query(user_query, channel_history)
    return jsonify({"response": response})


if __name__ == "__main__":
    setup_openai_api()
    app.run(host="0.0.0.0", port=8080)
