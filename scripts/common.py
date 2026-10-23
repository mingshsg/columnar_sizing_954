"""Shared helpers: load .env and build an authenticated Elasticsearch session."""
import os

import requests

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env(path=None):
    env = {}
    with open(path or os.path.join(PROJECT, ".env")) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def es_session():
    env = load_env()
    s = requests.Session()
    s.auth = (env["ES_USER"], env["ES_PASSWORD"])
    s.headers["Content-Type"] = "application/json"
    return s, env["ES_URL"].rstrip("/")
