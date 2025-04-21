import requests
import json
import time

MCP_URL = "http://localhost:3456/chat"
MODEL = "tinyllama"

import requests
import json
import pandas as pd
import re

MCP_URL = "http://localhost:3456/chat"
MODEL = "tinyllama"


def optimize_params(
    df: pd.DataFrame, params: dict, context: str = "maximize # of trades"
):
    param_text = "\n".join([f"{k} = {v}" for k, v in params.items()])

    prompt = f"""{param_text}
    
    optimize these hyperparams for me. goal = {context}
    based on the OHLCV below:

    {df}
    return ONLY updated params using same variable names in Python format. no explanation.
    """

    payload = {"model": MODEL, "messages": [{"role": "user", "content": prompt}]}

    try:
        res = requests.post(MCP_URL, json=payload, timeout=60)
        res.raise_for_status()
        data = res.json()
        reply = data.get("message", {}).get("content", "").strip()
        return extract_python_assignments(reply)

    except Exception as e:
        return f"❌ {str(e)}"
