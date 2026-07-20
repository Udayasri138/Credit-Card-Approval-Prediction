from app import app
client = app.test_client()
res = client.get('/dashboard')
print("Status Code:", res.status_code)
print("Location Headers:", res.headers.get('Location'))
print("Session Keys:", list(client.session_transaction()))
print("Body Sample:", res.data[:500])
