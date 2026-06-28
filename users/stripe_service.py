import stripe
from django.conf import settings


def configure_stripe():
    """Настраивает Stripe с ключом из settings."""
    stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_product(name: str, description: str = None):
    """
    Создаёт продукт в Stripe.
    Возвращает product.id
    """
    configure_stripe()

    kwargs = {"name": name}
    if description:
        kwargs["description"] = description

    product = stripe.Product.create(**kwargs)
    return product.id


def create_stripe_price(product_id: str, amount: int, currency: str = "rub"):
    """
    Создаёт цену в Stripe для продукта.

    amount — в копейках (центах), т.е. уже умноженное на 100.
    currency — например "rub".

    Возвращает price.id
    """
    configure_stripe()

    price = stripe.Price.create(
        unit_amount=amount,  # в копейках
        currency=currency,
        product=product_id,
    )
    return price.id


def create_stripe_checkout_session(price_id: str, success_url: str, cancel_url: str):
    """
    Создаёт Checkout Session в Stripe.

    Возвращает sessions.id и session.url.
    """
    configure_stripe()

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.id, session.url
