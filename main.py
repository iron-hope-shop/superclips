from flask import Flask, redirect, request, session, jsonify
import os
from google.cloud import secretmanager
import requests
import google_crc32c

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Ensure this is kept secret and use a persistent key in production

# Initialize Secret Manager client
client = secretmanager.SecretManagerServiceClient()

# # Function to retrieve secrets
# def access_secret_version(secret_id):
#     project_id = os.environ.get('GCP_PROJECT')
#     name = f"projects/{project_id}/secrets/{secret_id}/versions/2"
#     response = client.access_secret_version(request={"name": name})
#     return response.payload.data.decode("UTF-8")

def access_secret_version(
    secret_id: str
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
    name = f"projects/superclips/secrets/{secret_id}/versions/2"

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

# Retrieve your Twitter OAuth2.0 credentials from Secret Manager
TWITTER_CLIENT_ID = access_secret_version('twitter_oauth_client_id')
TWITTER_CLIENT_SECRET = access_secret_version('twitter_oauth_client_secret')

# OAuth endpoints given in the Twitter API documentation
TWITTER_AUTHORIZATION_URL = 'https://twitter.com/i/oauth2/authorize'
TWITTER_TOKEN_URL = 'https://api.twitter.com/oauth2/token'

# This should match the callback URL registered in your Twitter app settings
CALLBACK_URL = 'https://superclippy-3ylh5e663a-uc.a.run.app/oauth/callback'


@app.route('/oauth/login')
def oauth_login():
    # The state parameter is optional but recommended for security
    session['state'] = os.urandom(8).hex()
    
    # Redirect user to Twitter to authorize
    oauth_url = (
        f"{TWITTER_AUTHORIZATION_URL}?response_type=code&client_id={TWITTER_CLIENT_ID}"
        f"&redirect_uri={CALLBACK_URL}&scope=tweet.read%20tweet.write%20users.read%20offline.access"
        f"&state={session['state']}"
    )
    return redirect(oauth_url)


@app.route('/oauth/callback')
def oauth_callback():
    # Verify the state matches the state you provided in the /oauth/login route
    if request.args.get('state') != session.get('state'):
        return jsonify({"error": "State parameter does not match"}), 400

    # Exchange the authorization code for an access token
    code = request.args.get('code')
    token_data = {
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': TWITTER_CLIENT_ID,
        'client_secret': TWITTER_CLIENT_SECRET,
        'redirect_uri': CALLBACK_URL
    }
    
    response = requests.post(TWITTER_TOKEN_URL, data=token_data)
    
    if response.status_code == 200:
        tokens = response.json()
        # Store the tokens securely, e.g., in a database or session
        # Here, we just return it as a JSON response
        return jsonify(tokens), 200
    else:
        return jsonify({"error": "Failed to exchange token"}), response.status_code


if __name__ == '__main__':
    # App Engine typically runs on port 8080
    app.run(host='0.0.0.0', port=8080, debug=True)

