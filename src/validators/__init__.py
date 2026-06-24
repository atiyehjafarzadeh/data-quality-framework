"""
Validators package.

Each module here implements exactly one data quality check and exposes
a single function with the signature:

    check_xxx(df: pandas.DataFrame, ...) -> List[Issue]

Keeping checks isolated, pure, and side-effect-free makes them trivial
to unit test independently of the engine that orchestrates them.
"""

from .null_check import check_nulls
from .duplicate_check import check_duplicates
from .date_check import check_dates
from .email_check import check_emails
from .dtype_check import check_dtype
from .outlier_check import check_outliers

__all__ = [
    "check_nulls",
    "check_duplicates",
    "check_dates",
    "check_emails",
    "check_dtype",
    "check_outliers",
]
