# Conversion Counter Implementation

## Overview
This implementation adds a conversion counter to the User model to track all conversion attempts regardless of filtering, and uses this counter for the "divisible by 3" conversion filtering logic.

## Changes Made

### 1. User Model (`user/models.py`)
- Added `conversion_counter` field: `PositiveIntegerField` with default value 0
- Added `get_conversion_counter_display()` method for formatted display
- Added `reset_conversion_counter()` method for admin use

### 2. Database Migration
- Created and applied migration `0005_user_conversion_counter.py`
- All existing users will have `conversion_counter = 0`

### 3. Admin Interface (`user/admin.py`)
- Added `conversion_counter` to `list_display` for easy viewing
- Added `conversion_counter` to Financial fieldsets
- Added `reset_conversion_counters` action for bulk reset operations

### 4. Conversion Logic (`offers/views.py`)
- Updated `handle_postback()` function to use User model's conversion counter
- Counter increments on every conversion attempt (regardless of filtering)
- Filtering logic: `if user.conversion_counter % 3 == 0:`
- Prevents double-counting by checking for existing conversions first

## How It Works

1. **Every Conversion Attempt**: When a postback is received, the user's `conversion_counter` is incremented
2. **Filtering Logic**: If the counter is divisible by 3, the conversion is filtered out (not saved to database)
3. **User Continuity**: Users can continue getting conversions after hitting a divisible-by-3 number
4. **No Stuck Users**: The counter keeps incrementing, so users aren't permanently blocked

## Example Flow
- User gets 1st conversion: counter = 1, conversion saved
- User gets 2nd conversion: counter = 2, conversion saved  
- User gets 3rd conversion: counter = 3, conversion filtered out (divisible by 3)
- User gets 4th conversion: counter = 4, conversion saved
- User gets 5th conversion: counter = 5, conversion saved
- User gets 6th conversion: counter = 6, conversion filtered out (divisible by 3)

## Benefits
- **Accurate Tracking**: All conversion attempts are counted, not just saved ones
- **User-Friendly**: Users don't get stuck at multiples of 3
- **Admin Control**: Admins can view and reset counters as needed
- **Audit Trail**: Complete history of all conversion attempts

## Database Impact
- New field added to User table
- No data migration needed (defaults to 0)
- Minimal performance impact (simple integer increment)

## Future Enhancements
- Dashboard display of conversion counter
- User profile view of conversion counter
- Analytics on filtered vs. saved conversions
- Customizable filtering rules (configurable divisor)
