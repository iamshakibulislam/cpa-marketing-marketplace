# Cron Job Setup for CPA Network

This document explains how to set up the automated payment processing cron job for the CPA Network.

## Overview

The cron job automatically processes user payments and creates invoices on specific payment dates:
- **First Monday of each month**: All users (first-time and returning)
- **First Monday after 15th day of each month**: Returning users only

## Requirements

- Minimum balance: $100 USD
- Approved payment method (Binance email)
- Active user account

## Payment Logic

### First-Time Users
- **Payment Date**: Only on the first Monday of each month
- **Status**: Invoice created with 'pending' status
- **Balance**: Reset to $0 after invoice creation

### Returning Users
- **Payment Dates**: Both first Monday of month AND first Monday after 15th day
- **Status**: Invoice created with 'pending' status
- **Balance**: Reset to $0 after invoice creation

## Setup Instructions

### 1. Make the Script Executable

```bash
chmod +x offers/cron_jobs.py
```

### 2. Set Up Crontab

Open your crontab file:
```bash
crontab -e
```

### 3. Add the Cron Job

Add one of the following lines to your crontab:

#### Option A: Run every day at 2 AM (recommended)
```bash
0 2 * * * /usr/bin/python3 /path/to/your/project/offers/cron_jobs.py >> /var/log/cpa_cron.log 2>&1
```

#### Option B: Run every Monday at 2 AM
```bash
0 2 * * 1 /usr/bin/python3 /path/to/your/project/offers/cron_jobs.py >> /var/log/cpa_cron.log 2>&1
```

#### Option C: Run every hour (for testing)
```bash
0 * * * * /usr/bin/python3 /path/to/your/project/offers/cron_jobs.py >> /var/log/cpa_cron.log 2>&1
```

### 4. Replace Path

Replace `/path/to/your/project/` with the actual path to your Django project.

### 5. Create Log Directory

```bash
sudo mkdir -p /var/log
sudo touch /var/log/cpa_cron.log
sudo chmod 666 /var/log/cpa_cron.log
```

## How It Works

1. **Date Check**: The script checks if today is a payment date
2. **User Filtering**: Finds users with:
   - Balance >= $100
   - Approved payment method
3. **First-Time User Check**: 
   - First-time users (no previous invoices) only processed on first Monday
   - Returning users processed on both payment dates
4. **Invoice Creation**: Creates invoices for eligible users
5. **Balance Reset**: Sets user balance to $0
6. **Logging**: Logs all activities

## Payment Schedule

- **First Payment**: First Monday of next month (all users)
- **Subsequent Payments**: 
  - First Monday of each month (all users)
  - First Monday after 15th day of each month (returning users only)

## Testing

### Manual Test
```bash
cd /path/to/your/project
python manage.py shell
```

```python
from offers.cron_jobs import process_user_payments
result = process_user_payments()
print(result)
```

### Check Logs
```bash
tail -f /var/log/cpa_cron.log
```

## Monitoring

### Check Cron Job Status
```bash
crontab -l
```

### View Recent Logs
```bash
tail -n 50 /var/log/cpa_cron.log
```

### Check System Cron Logs
```bash
grep CRON /var/log/syslog
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   chmod +x offers/cron_jobs.py
   ```

2. **Python Path Issues**
   - Use full path to Python: `/usr/bin/python3`
   - Or use virtual environment path

3. **Django Settings**
   - Ensure `DJANGO_SETTINGS_MODULE` is set correctly
   - Check database connectivity

4. **Log File Issues**
   ```bash
   sudo chown $USER:$USER /var/log/cpa_cron.log
   ```

### Debug Mode

To run with verbose logging, modify the script:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

1. **File Permissions**: Ensure script is not world-writable
2. **Log Security**: Protect log files from unauthorized access
3. **Database Security**: Use environment variables for sensitive data
4. **Backup**: Regularly backup invoice data

## Invoice Status

- **Pending**: Invoice created, awaiting admin approval
- **Paid**: Invoice approved and payment sent
- **Rejected**: Invoice rejected by admin

## Admin Interface

Access the Django admin to:
- View all invoices
- Mark invoices as paid/rejected
- Manage payment methods
- Monitor user balances

## Support

For issues or questions:
1. Check the logs first
2. Verify cron job is running
3. Test manually in Django shell
4. Check database connectivity 