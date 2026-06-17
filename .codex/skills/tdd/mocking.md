# When to Mock

Mock at system boundaries only:

- External APIs
- Email, payment, queues, object storage
- Time and randomness
- File system when a temp directory is not enough
- Databases when a test database or transaction is impractical

Do not mock:

- Your own modules
- Internal collaborators
- Private helpers
- Anything you control and can run cheaply

## Designing for Mockability

At system boundaries, design interfaces that are easy to replace in tests.

1. Use dependency injection.

Pass external dependencies in rather than creating them internally.

```python
# Easy to test
def process_payment(order: Order, payment_client: PaymentClient) -> Receipt:
    return payment_client.charge(order.total)


# Hard to test
def process_payment(order: Order) -> Receipt:
    client = StripeClient(os.environ["STRIPE_KEY"])
    return client.charge(order.total)
```

2. Prefer specific boundary functions over generic clients.

```python
# Good: each function returns one specific shape
class BillingApi:
    def get_customer(self, customer_id: str) -> Customer: ...
    def create_invoice(self, customer_id: str, amount: Money) -> Invoice: ...


# Bad: tests need conditional mock logic
class ApiClient:
    def request(self, method: str, path: str, payload: dict | None = None) -> dict: ...
```

3. Use pytest tools intentionally.

- Prefer real objects and fixtures for internal code
- Use `monkeypatch` for environment variables and time/random boundaries
- Use `tmp_path` for file-system behavior
- Use `unittest.mock` for external boundary calls only

Good mocks are boring. They stand in for the outside world, not for your own design.
