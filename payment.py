import logging

logger = logging.getLogger("payment")


class PricePolicy:
    """Handles pricing policies and validations."""
    
    def __init__(self, min_price: float, target_price: float, max_discount_percent: float):
        self.min_price = min_price
        self.target_price = target_price
        self.max_discount_percent = max_discount_percent
        self.max_discount_amount = target_price * (max_discount_percent / 100)
        self.floor_price = target_price - self.max_discount_amount
    
    def validate_offer(self, offer: float) -> tuple[bool, str]:
        """Validate if offer meets pricing policy."""
        if offer >= self.target_price:
            return True, "Full price accepted"
        elif offer >= self.floor_price:
            discount = self.target_price - offer
            discount_pct = (discount / self.target_price) * 100
            return True, f"{discount_pct:.1f}% discount accepted"
        else:
            needed = self.floor_price - offer
            return False, f"Need ${needed:.2f} more (minimum ${self.floor_price:.2f})"
    
    def guidance(self) -> str:
        """Return pricing guidance."""
        return (
            f"Full Price: ${self.target_price:.2f}\n"
            f"Minimum: ${self.floor_price:.2f}\n"
            f"Max Discount: {self.max_discount_percent:.0f}%"
        )


def payment_instructions() -> str:
    """Return payment instructions."""
    return (
        "💳 **PAYMENT METHODS (CRYPTO ONLY):**\n\n"
        "**SOL (Solana)** - Fastest\n"
        "**BTC (Bitcoin)** - Most secure\n"
        "**ETH (Ethereum)** - Compatible\n"
        "**LTC (Litecoin)** - Alternative\n"
        "**XMR (Monero)** - Private\n\n"
        "Send payment and include order details in note."
    )
