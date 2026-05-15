import time
from mistralai.client.errors.sdkerror import SDKError


def mistral_complete_with_retry(client, max_retries=4, **kwargs):
    delay = 5
    for attempt in range(1, max_retries + 1):
        try:
            return client.chat.complete(**kwargs)
        except SDKError as e:
            if attempt == max_retries:
                raise
            if "503" in str(e) or "502" in str(e) or "529" in str(e) or "rate" in str(e).lower():
                print(f"\n  [retry {attempt}/{max_retries} after {delay}s — {str(e)[:60]}]", flush=True)
                time.sleep(delay)
                delay *= 2
            else:
                raise
