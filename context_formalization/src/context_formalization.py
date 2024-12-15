import requests, logging
from kubernetes import client, config
from request_jaeger import JAEGER_API_URL
from datetime import datetime, timedelta

JAEGER_API_URL = 'http://localhost:16686/api/traces'
DEFAULT_LIMIT = 100  # Adjust the limit to control the number of traces per request

# Specify namespace where your services are running
NAMESPACE = 'default'

def get_kubernetes_services(namespace='default'):
    # Load kube config from default location
    config.load_kube_config()
    # Create Kubernetes API client
    v1 = client.CoreV1Api()
    # List services in specified namespace
    services = v1.list_namespaced_service(namespace=namespace)
    # Extract service names
    service_names = [service.metadata.name for service in services.items]
    # Clean up service names and filter out undesired services
    cleaned_service_names = [clean_service_name(name) for name in service_names if name != 'jaeger' and name != 'kubernetes']
    
    # Print the cleaned and filtered service names
    print("Cleaned and filtered service names:", cleaned_service_names)
    ##cleaned_service_names = [clean_service_name(name) for name in service_names if name not in ['jaeger', 'kubernetes']]

    return cleaned_service_names

def clean_service_name(name):
    # Remove '-service' suffix if present
    if name.endswith('-service'):
        name = name[:-8]
    return name

def query_jaeger_for_service(service_name, lookback='1h'):
    # Jaeger query URL
    jaeger_url = f"{JAEGER_API_URL}?lookback={lookback}&service={service_name}"
    print("request: ", jaeger_url)
    # Make request to Jaeger API
    response = requests.get(jaeger_url)
    data = response.json()
    
    # Check if the service has any traces
    if data.get("data"):
        return True
    return False

def fetch_traces(jaeger_api_url, limit, service_name):
    """
    Fetch traces from Jaeger.
    """
    traces = []
    params = {
        'limit': limit
    }
    try:
        response = requests.get(jaeger_api_url + '?service=' + service_name, params=params)
        response.raise_for_status()  # Raises an HTTPError if the response code was unsuccessful
        data = response.json()

        if 'data' in data:
            traces.extend(data['data'])
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching traces from Jaeger: {e}")
        if response.content:
            logging.error(f"Response content: {response.content}")

    return traces

def get_current_traces_and_spans(jaeger_api_url, limit, service_name):
    """
    Get the current trace and span information for the given service.
    """
    traces = fetch_traces(jaeger_api_url, limit, service_name)
    current_traces_and_spans = {}

    # search for the most closet span
    most_recent_span = None

    for trace in traces:
        trace_id = trace['traceID']
        spans = trace.get('spans', [])

        for span in spans:
            # process = span.get('process', {})
            # if process.get('serviceName') == service_name:

            span_id = span['spanID']
            operation_name = span['operationName']
            start_time = datetime.utcfromtimestamp(span['startTime'] / 1e6)  # convert microseconds to seconds
            duration = span['duration'] / 1e3  # convert microseconds to milliseconds
            end_time = start_time + timedelta(milliseconds=duration)

            if trace_id not in current_traces_and_spans:
                current_traces_and_spans[trace_id] = []

            current_traces_and_spans[trace_id].append({
                'span_id': span_id,
                'operation_name': operation_name,
                'start_time': start_time,
                'end_time': end_time,
                'duration_ms': duration
            })
    return current_traces_and_spans

def get_most_recent_span(jaeger_api_url, limit, service_name):
    """
    Get the most recent span from the fetched traces.
    """

    traces = fetch_traces(jaeger_api_url, limit, service_name)

    most_recent_span = None

    for trace in traces:
        spans = trace.get('spans', [])

        for span in spans:
            start_time = datetime.utcfromtimestamp(span['startTime'] / 1e6)  # convert microseconds to seconds
            if not most_recent_span or start_time > most_recent_span['start_time']:
                span_id = span['spanID']
                operation_name = span['operationName']
                duration = span['duration'] / 1e3  # convert microseconds to milliseconds
                end_time = start_time + timedelta(milliseconds=duration)

                most_recent_span = {
                    'span_id': span_id,
                    'operation_name': operation_name,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_ms': duration
                }

    return most_recent_span
def main():
    # Get list of services from Kubernetes
    services = get_kubernetes_services(namespace=NAMESPACE)
    # Query Jaeger for each service and determine if it's handling requests
    active_services = []
    for service in services:
        if query_jaeger_for_service(service):
            active_services.append(service)
    print("Services currently handling requests:", active_services)

    # trace = fetch_traces(JAEGER_API_URL, 1, active_services[0])
    #  print(trace)

    # current_traces_and_spans = get_current_traces_and_spans(JAEGER_API_URL, 1, active_services[0])
    # print(current_traces_and_spans) 
    #
    # for trace_id, spans in current_traces_and_spans.items():
    #     print(f"Trace ID: {trace_id}")
    #     for span in spans:
    #         print(f"  Span ID: {span['span_id']}")
    #         print(f"  Operation Name: {span['operation_name']}")
    #         print(f"  Start Time (UTC): {span['start_time']}")
    #         print(f"  End Time (UTC): {span['end_time']}")
    #         print(f"  Duration (ms): {span['duration_ms']}")
    #         print()
    
    most_recent_span = get_most_recent_span(JAEGER_API_URL, 1, active_services[0])
    
    if most_recent_span:
        print("Most recent span information:")
        print(f"  Span ID: {most_recent_span['span_id']}")
        print(f"  Operation Name: {most_recent_span['operation_name']}")
        print(f"  Start Time (UTC): {most_recent_span['start_time']}")
        print(f"  End Time (UTC): {most_recent_span['end_time']}")
        print(f"  Duration (ms): {most_recent_span['duration_ms']}")
    else:
        print("No spans found for the given service.")

if __name__ == "__main__":
    main()
