
import httpx

def send_mobile_push(title, body):
    url = "http://localhost:5050/push-alert"
    payload = {"title": title, "body": body}
    try:
        response = httpx.post(url, json=payload, timeout=5)
        print("Mobile push sent:", response.status_code)
    except Exception as e:
        print("Failed to send mobile push:", e)
