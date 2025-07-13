# Transfer Request Approve/Decline Implementation

## Problem Fixed
The transfer request system was only showing "View" buttons instead of "Approve/Decline" buttons for incoming transfer requests that needed approval.

## Solution Implemented

### 1. **Added Approve/Decline Views** (`store/views.py`)

#### `approve_store_transfer_request(request, request_id)`
- Handles approval of incoming transfer requests
- Validates stock availability in source store
- Transfers stock from source to destination store
- Updates request status to 'approved'
- Supports both form and AJAX submissions

#### `decline_store_transfer_request(request, request_id)`
- Handles decline of incoming transfer requests
- Requires a reason for declining
- Updates request status to 'rejected'
- Supports both form and AJAX submissions

### 2. **Added URL Patterns** (`store/urls.py`)
```python
path('manager/approve-transfer-request/<int:request_id>/', views.approve_store_transfer_request, name='approve_store_transfer_request'),
path('manager/decline-transfer-request/<int:request_id>/', views.decline_store_transfer_request, name='decline_store_transfer_request'),
```

### 3. **Updated Transfer Requests View** (`users/views.py`)

#### Modified `store_manager_transfer_requests()`
- **Before**: Only showed requests FROM the current store
- **After**: Shows both incoming (FROM store) and outgoing (TO store) requests
- Updated query to use `Q(from_store=store) | Q(to_store=store)`
- Updated statistics to include both types of requests

### 4. **Enhanced Template** (`templates/mainpages/store_manager_transfer_requests.html`)

#### Updated Actions Column
- **Incoming Requests** (from_store.store_manager == user): Shows Approve/Decline buttons
- **Outgoing Requests** (to_store.store_manager == user): Shows View button
- Added visual indicators for INCOMING vs OUTGOING requests

#### Added Modal Dialogs
- **Approval Modal**: Allows setting approved quantity and notes
- **Decline Modal**: Requires reason for declining

#### Added JavaScript Functions
- `approveTransferRequest()`: Opens approval modal with pre-filled data
- `declineTransferRequest()`: Opens decline modal

### 5. **Visual Improvements**

#### Transfer Direction Display
- **INCOMING**: Yellow badge with down arrow - "Other store requesting from us"
- **OUTGOING**: Blue badge with up arrow - "We requested from other store"

## Business Logic

### For Store Manager A (Source Store):
1. **Incoming Requests**: Other stores requesting products FROM Store A
   - Store A manager sees "INCOMING" badge
   - Store A manager can Approve/Decline
   - If approved, stock moves FROM Store A TO requesting store

### For Store Manager B (Requesting Store):
1. **Outgoing Requests**: Store B requesting products FROM other stores
   - Store B manager sees "OUTGOING" badge
   - Store B manager can only View (cannot approve their own requests)

## Key Features

### ✅ **Proper Authorization**
- Only source store managers can approve/decline incoming requests
- Requesting store managers cannot approve their own requests

### ✅ **Stock Validation**
- Checks available stock before approval
- Prevents over-allocation of inventory

### ✅ **Automatic Stock Transfer**
- On approval, automatically moves stock between stores
- Updates both source and destination inventory

### ✅ **User Experience**
- Clear visual indicators for request types
- Modal dialogs for smooth workflow
- Proper error handling and feedback

### ✅ **Data Integrity**
- Validates request ownership
- Ensures only pending requests can be processed
- Maintains audit trail with reviewer and timestamps

## Files Modified

1. **`store/views.py`** - Added approve/decline views
2. **`store/urls.py`** - Added URL patterns
3. **`users/views.py`** - Updated transfer requests view logic
4. **`templates/mainpages/store_manager_transfer_requests.html`** - Enhanced UI

## Testing Instructions

### Manual Testing:
1. **Create two stores** with different managers
2. **Add stock** to Store A
3. **Login as Store B manager** and request transfer from Store A
4. **Login as Store A manager** and go to Transfer Requests page
5. **Verify** you see the request with "INCOMING" badge and Approve/Decline buttons
6. **Click Approve** and verify stock transfer happens
7. **Check both stores** to confirm stock levels updated

### Expected Behavior:
- ✅ Store A manager sees incoming requests with approve/decline options
- ✅ Store B manager sees outgoing requests with view option only
- ✅ Approval transfers stock and updates request status
- ✅ Decline requires reason and updates request status
- ✅ Visual indicators clearly show request direction

## Database Note
There may be a database migration issue with a `decline_reason` field. If you encounter this:
1. Check for pending migrations: `python manage.py showmigrations`
2. Apply migrations: `python manage.py migrate`
3. Or create a new migration if needed

## Result
✅ **Transfer requests now show proper Approve/Decline buttons for incoming requests!**
✅ **Store managers can approve/decline requests directly from their dashboard!**
✅ **Clear visual distinction between incoming and outgoing requests!**
