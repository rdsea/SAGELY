import requests
import logging

# Configuring logging
logging.basicConfig(level=logging.INFO)

# Configuration
# JAEGER_API_URL = 'http://localhost:16686/api/dependencies'

JAEGER_API_URL = "http://localhost:16686/api/traces?lookback=1h&service=preprocessing"
DEFAULT_LIMIT = 100  # Adjust the limit to control the number of traces per request


def fetch_traces(jaeger_api_url, limit):
    """
    Fetch traces from Jaeger.
    """
    traces = []
    params = {"limit": limit}
    try:
        response = requests.get(jaeger_api_url, params=params)
        response.raise_for_status()  # Raises an HTTPError if the response code was unsuccessful
        data = response.json()

        if "data" in data:
            traces.extend(data["data"])
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching traces from Jaeger: {e}")
        if response.content:
            logging.error(f"Response content: {response.content}")

    return traces


def main():
    jaeger_endpoint = JAEGER_API_URL
    limit = DEFAULT_LIMIT

    traces = fetch_traces(jaeger_endpoint, limit)
    if traces:
        for trace in traces:
            print(trace)
        logging.info(f"Total traces fetched: {len(traces)}")
    else:
        logging.info("No traces found or an error occurred.")


if __name__ == "__main__":
    main()
