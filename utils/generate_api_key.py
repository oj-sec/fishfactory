#!/usr/bin/env python3

# Helper script to generate Fishfactory API keys. 
# Requires a configured apiSecret signing key:
# openssl rand -base64 60

import jwt
import time
import argparse
import json
from datetime import datetime, timedelta

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--user", required=True, help="Username to embed in generated token.")
    parser.add_argument("-d", "--days", required=False, type=int, default=30, help="Days for token to be valid.")

    args = parser.parse_args()

    with open("../config.json", "r") as f:
        config = json.loads(f.read())
        secret = config['apiSecret']

    payload = {
        "iat": time.mktime((datetime.now()).timetuple()),
        "type": "access",
        "sub": args.user,
        "exp": time.mktime((datetime.now() + timedelta(days=args.days)).timetuple())
    }

    encoded_jwt = jwt.encode(payload, secret, algorithm="HS256")

    print(encoded_jwt)