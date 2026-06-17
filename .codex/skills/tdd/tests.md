# Good and Bad Tests

## Good Tests

Integration-style tests go through real interfaces and verify observable behavior.

```python
def test_user_can_checkout_with_valid_cart():
    cart = Cart()
    cart.add(Product("book", price=Money("12.00")))

    result = checkout(cart, payment_method=FakePaymentMethod.approved())

    assert result.status == "confirmed"
```

Characteristics:

- Tests behavior users or callers care about
- Uses public API only
- Survives internal refactors
- Describes what, not how
- Has one clear reason to fail
- Uses pytest fixtures for setup when setup is shared

## Bad Tests

Implementation-detail tests are coupled to internal structure.

```python
def test_checkout_calls_payment_service_process(mocker):
    payment_service = mocker.patch("app.checkout.payment_service")

    checkout(cart, payment_method)

    payment_service.process.assert_called_once_with(cart.total)
```

Red flags:

- Mocking internal collaborators
- Testing private functions directly
- Asserting on call counts or call order
- Test breaks during refactor without behavior change
- Test name describes how, not what
- Verifying through external means instead of the public interface

```python
# Bad: bypasses interface to verify persistence
def test_create_user_saves_to_database(db):
    create_user({"name": "Alice"})

    row = db.execute("select * from users where name = 'Alice'").fetchone()
    assert row is not None


# Good: verifies through interface
def test_create_user_makes_user_retrievable():
    user = create_user({"name": "Alice"})

    retrieved = get_user(user.id)

    assert retrieved.name == "Alice"
```
