# Interface Design for Testability

Good Python interfaces make testing natural.

1. Accept dependencies, do not create them deep inside logic.

```python
# Testable
def process_order(order: Order, payment_client: PaymentClient) -> Receipt:
    return payment_client.charge(order.total)


# Hard to test
def process_order(order: Order) -> Receipt:
    client = StripeClient(os.environ["STRIPE_KEY"])
    return client.charge(order.total)
```

2. Return results instead of mutating hidden state.

```python
# Testable
def calculate_discount(cart: Cart) -> Money:
    return Money("10.00")


# Harder to test
def apply_discount(cart: Cart) -> None:
    cart.total -= calculate_discount(cart)
```

3. Keep surface area small.

- Fewer public functions means fewer tests needed
- Fewer parameters means simpler test setup
- Plain return values are easier to assert on
- Dataclasses are useful when behavior needs named data

4. Put side effects at the edges.

Core logic should be pure where practical. Let a thin outer layer handle files, databases, HTTP, environment variables, and time.
