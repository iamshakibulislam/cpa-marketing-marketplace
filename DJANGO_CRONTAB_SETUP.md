# Django Crontab Setup Guide

This guide explains how to set up and use django-crontab for automated payment processing in the CPA Network.

## Overview

Django-crontab is a Django app that allows you to schedule tasks using cron syntax. It's configured in your Django settings and managed through Django management commands.

## Installation

### 1. Install django-crontab

```bash
pip install django-crontab
```

### 2. Add to INSTALLED_APPS

In `cpa/settings.py`:
```python
INSTALLED_APPS = [
    # ... other apps
    'django_crontab',  # Add django-crontab for scheduled tasks
]
```

### 3. Configure CRONJOBS

In `cpa/settings.py`:
```python
# Django Crontab Configuration
CRONJOBS = [
    # Run payment processing every day at 6:00 AM
    ('0 6 * * *', 'django.core.management.call_command', ['process_payments'], {}, '>> /var/log/cpa_cron.log 2>&1'),
]

# Additional configuration
CRONTAB_LOCK_JOBS = True
CRONTAB_COMMENT = 'django-crontabs for cpa'
CRONTAB_PYTHON_EXECUTABLE = '/usr/bin/python3'
CRONTAB_DJANGO_MANAGE_PATH = str(BASE_DIR / 'manage.py')
```

## Usage

### 1. Add Crontab Jobs

After configuring CRONJOBS in settings.py, add the jobs to your system's crontab:

```bash
python manage.py crontab add
```

This will:
- Add the configured jobs to your system's crontab
- Mark them with the project comment for easy identification
- Use the specified Python executable and Django settings

### 2. List Current Crontab Jobs

```bash
python manage.py crontab show
```

### 3. Remove Crontab Jobs

```bash
python manage.py crontab remove
```

### 4. Run Jobs Manually

You can also run the payment processing manually:

```bash
# Normal run (only on payment dates)
python manage.py process_payments

# Force run (even if not a payment date)
python manage.py process_payments --force

# Dry run (show what would be processed)
python manage.py process_payments --dry-run
```

## Cron Syntax

The cron syntax used in CRONJOBS follows the standard format:

```
minute hour day month weekday
```

### Examples:

- `'0 6 * * *'` - Every day at 6:00 AM
- `'0 6 * * 1'` - Every Monday at 6:00 AM
- `'0 6 1 * *'` - First day of every month at 6:00 AM
- `'0 6 1,15 * *'` - 1st and 15th of every month at 6:00 AM
- `'0 6 * * 1,3,5'` - Monday, Wednesday, Friday at 6:00 AM

### Field Values:

- **minute**: 0-59
- **hour**: 0-23
- **day**: 1-31
- **month**: 1-12
- **weekday**: 0-6 (0=Sunday, 1=Monday, etc.)

## Configuration Options

### CRONJOBS
List of scheduled jobs in the format:
```python
(cron_timing, python_module_path, [args], {kwargs}, suffix)
```

### CRONTAB_LOCK_JOBS
Prevent overlapping jobs (default: False)
```python
CRONTAB_LOCK_JOBS = True
```

### CRONTAB_COMMAND_PREFIX
Environment variables or commands to run before each job:
```python
CRONTAB_COMMAND_PREFIX = 'STAGE=production'
```

### CRONTAB_COMMAND_SUFFIX
Commands to run after each job:
```python
CRONTAB_COMMAND_SUFFIX = '2>&1'
```

### CRONTAB_COMMENT
Comment to mark crontab entries:
```python
CRONTAB_COMMENT = 'django-crontabs for cpa'
```

## Payment Processing Logic

The payment processing follows these rules:

1. **First-time users**: Only processed on the first Monday of each month
2. **Returning users**: Processed on both payment dates (first Monday and first Monday after 15th)
3. **Minimum balance**: $100 USD required
4. **Payment method**: Must have approved Binance payment method

## Logging

All cron job output is logged to `/var/log/cpa_cron.log` by default. You can monitor the logs:

```bash
# View recent logs
tail -f /var/log/cpa_cron.log

# View last 50 lines
tail -n 50 /var/log/cpa_cron.log
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   sudo chmod +x /path/to/your/project/manage.py
   ```

2. **Python Path Issues**
   - Ensure `CRONTAB_PYTHON_EXECUTABLE` points to the correct Python interpreter
   - Use absolute paths in settings

3. **Django Settings**
   - Ensure `CRONTAB_DJANGO_SETTINGS_MODULE` is set correctly
   - Check that `CRONTAB_DJANGO_MANAGE_PATH` points to the correct manage.py

4. **Crontab Not Running**
   ```bash
   # Check if cron service is running
   sudo service cron status
   
   # Check system cron logs
   grep CRON /var/log/syslog
   ```

### Debug Mode

To run with verbose logging, modify the cron job:
```python
CRONJOBS = [
    ('0 6 * * *', 'django.core.management.call_command', ['process_payments', '--verbosity=2'], {}, '>> /var/log/cpa_cron.log 2>&1'),
]
```

## Security Considerations

1. **File Permissions**: Ensure manage.py and settings are not world-writable
2. **Log Security**: Protect log files from unauthorized access
3. **Environment Variables**: Use environment variables for sensitive data
4. **Backup**: Regularly backup crontab configuration

## Monitoring

### Check Crontab Status
```bash
# List current crontab
crontab -l

# Check if jobs are running
ps aux | grep cron
```

### View Django Crontab Jobs
```bash
python manage.py crontab show
```

## Best Practices

1. **Test First**: Always test cron jobs manually before scheduling
2. **Use Management Commands**: Prefer Django management commands over direct function calls
3. **Log Everything**: Ensure all output is logged for debugging
4. **Monitor Regularly**: Check logs and job status regularly
5. **Backup Configuration**: Keep backups of your crontab configuration

## Support

For issues or questions:
1. Check the logs first (`/var/log/cpa_cron.log`)
2. Verify cron service is running
3. Test manually with `python manage.py process_payments`
4. Check Django settings configuration
5. Review system cron logs 