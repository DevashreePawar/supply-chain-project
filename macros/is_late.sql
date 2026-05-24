{#
============================================================================
is_late() macro

Returns 1 if an order should be considered LATE per the project's CANONICAL
definition; 0 otherwise.

CANONICAL DEFINITION:
    An order is "late" iff DELIVERY_STATUS = 'Late delivery'.

WHY THIS DEFINITION (and not day-math):
    The DataCo dataset includes both:
      1. The DELIVERY_STATUS string (4 possible values; categorical)
      2. The day-arithmetic: DAYS_FOR_SHIPPING_REAL vs DAYS_FOR_SHIPMENT_SCHEDULED

    These two signals DISAGREE on a non-trivial fraction of rows (some orders
    where day-math says "on time" carry status "Late delivery", and vice versa).

    We picked the DELIVERY_STATUS string as canonical because:
      a. It matches the dataset's own classification — interpretable
      b. Every memo number, dashboard tile, and stakeholder figure was
         computed against this definition
      c. The day-math version is preserved as is_on_time_flag for analyses
         where shipping SLA is the question (different question, different flag)

    See tests/assert_late_flags_drift_within_threshold.sql for the divergence
    monitor that alerts if the two signals ever drift further apart.

USAGE:
    SELECT
        order_id,
        {{ is_late('DELIVERY_STATUS') }} AS is_late_flag
    FROM ...

ARGS:
    delivery_status_col — the column name (as a string) holding the
                          DELIVERY_STATUS values from raw.
============================================================================
#}

{% macro is_late(delivery_status_col) %}
    CASE WHEN {{ delivery_status_col }} = 'Late delivery' THEN 1 ELSE 0 END
{% endmacro %}
