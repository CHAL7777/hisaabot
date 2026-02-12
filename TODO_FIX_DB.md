# TODO Fix - Command messages being parsed as sales

## Problem
When users send commands like `/monthly` or click buttons like `👥 Customers` while in sale recording state, these messages are incorrectly parsed as sales and return error "Please use: 500 bread or 3x 500 bread"

## Root Cause
The `process_sale` and `process_expense` handlers don't check if incoming messages are commands, causing command messages to be processed as sale/expense data.

## Plan
- [ ] Fix `app/handlers/sales.py` - Add command check in `process_sale`
- [ ] Fix `app/handlers/expenses.py` - Add command check in `process_expense`
- [ ] Test the fix

## Changes Made

### 1. app/handlers/sales.py
- Add check at start of `process_sale` to skip messages starting with `/` or matching known commands/buttons
- This allows command messages to be properly routed to their handlers

### 2. app/handlers/expenses.py  
- Add check at start of `process_expense` to skip messages starting with `/`
- This allows command messages to be properly routed to their handlers

## Status
- [x] Plan approved
- [x] Implement sales.py fix
- [x] Implement expenses.py fix
- [ ] Test the fix

