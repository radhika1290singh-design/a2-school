# A2 School — DB Spec 10: `fee_periods`

## Dependencies
- `enrollments` (06) must exist first
- `users` (02) must exist first

## Purpose
Tracks fee payment status per student per billing period. Generated upfront
for the full academic year at enrollment creation time.

## Table: `fee_periods`

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | Primary key |
| `enrollment_id` | UUID | NO | FK → enrollments.id. Student-type only |
| `period_label` | text | NO | e.g. "April 2026" (monthly), "Q1 2026" (quarterly), "2025-2026" (yearly) |
| `period_start` | date | NO | |
| `period_end` | date | NO | |
| `amount_due` | numeric | NO | Copied from classes.fee_amount at generation time. NOT a live reference — changing the class fee later does NOT affect already-generated periods |
| `status` | enum(`paid`,`unpaid`) | NO | Default 'unpaid'. All-or-nothing, no partial payments |
| `paid_date` | date | YES | Set when marked paid |
| `marked_by_user_id` | UUID | YES | FK → users.id. Admin or the section's teacher |
| `created_at` | timestamp | NO | Default now() |

## Generation rules
- Generated UPFRONT at enrollment creation — all periods for the academic
  year are created immediately (e.g. all 12 months at once for monthly)
- Billing cycle comes from schools.fee_billing_cycle
- monthly → 12 periods, dates aligned to calendar months
- quarterly → 4 periods
- yearly → 1 period covering full academic_year start_date to end_date
- All periods start with status = 'unpaid'

## Rules
- Teacher can mark paid/unpaid only for students in their own section
- Admin can mark paid/unpaid for any student in their school
- Student has read-only access to their own fee periods only
- amount_due is snapshotted at generation — historical records stay accurate
  even if the class fee_amount is changed later
