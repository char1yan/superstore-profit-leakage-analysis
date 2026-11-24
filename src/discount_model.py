"""Discount-cap scenario model, shared by the notebook and the Excel builder.

For every order line with discount d, a cap c (applied only to in-scope sub-categories) gives:
    new discount     d' = min(d, c)
    price ratio      r  = (1 - d') / (1 - d)        # >= 1, the customer pays more
    volume factor    v  = max(0, 1 + e * (r - 1))   # e = price elasticity (negative)
    new sales           = sales * r * v
    new profit          = (profit + sales * (r - 1)) * v   # unit cost unchanged
"""
import numpy as np
import pandas as pd


def apply_discount_cap(orders: pd.DataFrame, cap: float, elasticity: float, in_scope=None) -> pd.DataFrame:
    df = orders.copy()
    scope = np.ones(len(df), dtype=bool) if in_scope is None else df["sub_category"].isin(in_scope).to_numpy()
    new_disc = np.where(scope, np.minimum(df["discount"], cap), df["discount"])
    ratio = (1 - new_disc) / (1 - df["discount"])
    vol = np.maximum(0, 1 + elasticity * (ratio - 1))
    df["new_discount"] = new_disc
    df["new_sales"] = df["sales"] * ratio * vol
    df["new_profit"] = (df["profit"] + df["sales"] * (ratio - 1)) * vol
    return df


def scenario_summary(orders, cap, elasticity, in_scope=None):
    s = apply_discount_cap(orders, cap, elasticity, in_scope)
    return {
        "cap": cap,
        "elasticity": elasticity,
        "sales": s["new_sales"].sum(),
        "profit": s["new_profit"].sum(),
        "profit_uplift": s["new_profit"].sum() - s["profit"].sum(),
        "sales_change": s["new_sales"].sum() - s["sales"].sum(),
    }
