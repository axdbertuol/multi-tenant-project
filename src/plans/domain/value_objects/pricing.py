from decimal import Decimal
from pydantic import BaseModel, field_validator
from typing import Optional
from enum import Enum


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    BRL = "BRL"
    GBP = "GBP"


class PricingModel(str, Enum):
    FIXED = "fixed"
    PER_USER = "per_user"
    USAGE_BASED = "usage_based"
    TIERED = "tiered"


class Pricing(BaseModel):
    amount: Decimal
    currency: Currency
    model: PricingModel
    setup_fee: Decimal = Decimal("0.00")
    per_user_amount: Optional[Decimal] = None
    free_user_count: int = 0

    model_config = {"frozen": True}

    @field_validator("amount", "setup_fee", "per_user_amount")
    @classmethod
    def validate_amounts(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is None:
            return v

        if v < 0:
            raise ValueError("Amount cannot be negative")

        if v > Decimal("999999.99"):
            raise ValueError("Amount cannot exceed 999,999.99")

        # Ensure proper decimal precision (2 decimal places)
        return v.quantize(Decimal("0.01"))

    @field_validator("free_user_count")
    @classmethod
    def validate_free_user_count(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Free user count cannot be negative")

        if v > 1000:
            raise ValueError("Free user count cannot exceed 1000")

        return v

    @classmethod
    def create_fixed(
        cls,
        amount: Decimal,
        currency: Currency = Currency.USD,
        setup_fee: Decimal = Decimal("0.00"),
    ) -> "Pricing":
        return cls(
            amount=amount,
            currency=currency,
            model=PricingModel.FIXED,
            setup_fee=setup_fee,
        )

    @classmethod
    def create_per_user(
        cls,
        base_amount: Decimal,
        per_user_amount: Decimal,
        currency: Currency = Currency.USD,
        free_user_count: int = 0,
        setup_fee: Decimal = Decimal("0.00"),
    ) -> "Pricing":
        return cls(
            amount=base_amount,
            currency=currency,
            model=PricingModel.PER_USER,
            per_user_amount=per_user_amount,
            free_user_count=free_user_count,
            setup_fee=setup_fee,
        )

    @classmethod
    def create_free(cls) -> "Pricing":
        return cls(
            amount=Decimal("0.00"),
            currency=Currency.USD,
            model=PricingModel.FIXED,
            setup_fee=Decimal("0.00"),
        )

    def calculate_total_cost(self, user_count: int = 1) -> Decimal:
        """Calculate total cost based on pricing model and user count."""
        total = self.amount

        if self.model == PricingModel.PER_USER and self.per_user_amount:
            # Calculate billable users (subtract free users)
            billable_users = max(0, user_count - self.free_user_count)
            total += self.per_user_amount * billable_users

        return total

    def calculate_setup_cost(self) -> Decimal:
        """Get setup cost."""
        return self.setup_fee

    def calculate_monthly_cost(self, user_count: int = 1) -> Decimal:
        """Calculate monthly cost (alias for total cost)."""
        return self.calculate_total_cost(user_count)

    def calculate_yearly_cost(self, user_count: int = 1) -> Decimal:
        """Calculate yearly cost with potential discount."""
        monthly_cost = self.calculate_total_cost(user_count)
        # Apply 10% discount for yearly billing
        yearly_cost = monthly_cost * 12 * Decimal("0.9")
        return yearly_cost.quantize(Decimal("0.01"))

    def is_free(self) -> bool:
        """Check if pricing is free."""
        return self.amount == Decimal("0.00") and self.setup_fee == Decimal("0.00")

    def has_setup_fee(self) -> bool:
        """Check if pricing has setup fee."""
        return self.setup_fee > Decimal("0.00")

    def is_per_user_pricing(self) -> bool:
        """Check if pricing is per-user based."""
        return self.model == PricingModel.PER_USER

    def format_amount(self, amount: Decimal) -> str:
        """Format amount with currency."""
        symbol_map = {
            Currency.USD: "$",
            Currency.EUR: "€",
            Currency.BRL: "R$",
            Currency.GBP: "£",
        }

        symbol = symbol_map.get(self.currency, self.currency.value)
        return f"{symbol}{amount:,.2f}"

    def format_price(self, user_count: int = 1) -> str:
        """Format complete price string."""
        total = self.calculate_total_cost(user_count)
        formatted = self.format_amount(total)

        if self.model == PricingModel.PER_USER and user_count > 1:
            formatted += f" ({user_count} users)"

        return formatted

    def get_pricing_description(self) -> str:
        """Get human-readable pricing description."""
        if self.is_free():
            return "Free"

        base_price = self.format_amount(self.amount)

        if self.model == PricingModel.FIXED:
            return f"{base_price}/month"

        elif self.model == PricingModel.PER_USER:
            if self.amount > 0:
                desc = f"{base_price} base"
            else:
                desc = ""

            if self.per_user_amount:
                user_price = self.format_amount(self.per_user_amount)
                if desc:
                    desc += f" + {user_price}/user/month"
                else:
                    desc = f"{user_price}/user/month"

            if self.free_user_count > 0:
                desc += f" (first {self.free_user_count} users free)"

            return desc

        return f"{base_price}/month"

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "amount": float(self.amount),
            "currency": self.currency.value,
            "model": self.model.value,
            "setup_fee": float(self.setup_fee),
            "per_user_amount": float(self.per_user_amount)
            if self.per_user_amount
            else None,
            "free_user_count": self.free_user_count,
        }
