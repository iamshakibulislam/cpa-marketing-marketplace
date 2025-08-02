# CPA Networks Configuration

This system uses a database model to manage multiple CPA networks with a management command to populate/update the data.

## Database Model

### CPANetwork Model
The `CPANetwork` model stores all CPA network configurations:

- **network_key**: Unique identifier (e.g., 'NexusSyner')
- **name**: Display name of the network
- **description**: Description of the network
- **click_id_parameter**: Parameter for sending click ID (e.g., 's2', 'subid')
- **postback_click_id_parameter**: Parameter for receiving click ID in postback
- **postback_payout_parameter**: Parameter for receiving payout in postback
- **is_active**: Whether the network is active

## Setup Steps

### 1. Run Migrations
```bash
python manage.py makemigrations offers
python manage.py migrate
```

### 2. Populate CPA Networks
```bash
python manage.py populate_cpa_networks
```

### 3. Configure Site Settings
1. Go to Django Admin → Site Settings
2. Create site settings with your domain
3. Save the settings

### 4. Create Offers
1. Go to Django Admin → Offers → Add Offer
2. **Select CPA Network**: Choose from dropdown (populated from database)
3. **Enter Offer URL**: Original URL from CPA network
4. **Fill other details**: Payout, countries, devices, etc.

## Adding New CPA Networks

### Method 1: Edit Management Command
1. Open `offers/management/commands/populate_cpa_networks.py`
2. Add new network data to the `cpa_networks_data` list
3. Run the command again:
   ```bash
   python manage.py populate_cpa_networks
   ```

### Method 2: Use Django Admin
1. Go to Django Admin → CPA Networks
2. Click "Add CPA Network"
3. Fill in all required fields
4. Save the network

## Management Command Features

The `populate_cpa_networks` command:
- ✅ **Checks for existing networks** by `network_key`
- ✅ **Updates existing networks** with new data
- ✅ **Creates new networks** if they don't exist
- ✅ **Preserves existing data** when re-running
- ✅ **Safe to run multiple times**

## Example Network Data

```python
{
    'network_key': 'NexusSyner',
    'name': 'NexusSyner',
    'description': 'NexusSyner CPA Network',
    'click_id_parameter': 's2',
    'postback_click_id_parameter': 'click_id',
    'postback_payout_parameter': 'payout',
    'is_active': True
}
```

## How It Works

### 1. Click Tracking
When a user clicks a tracking link:
- System generates unique click ID: `userid-offerid-HHMMSS-YYYYMMDD`
- Redirects to CPA network with click ID parameter
- Example: `https://nexussyner.com/offer/?s2=123-456-143022-20241225`

### 2. Postback Handling
When CPA network sends conversion:
- Receives postback at: `https://yourdomain.com/offers/postback/?network=NexusSyner&click_id=123-456-143022-20241225&payout=25.50`
- System creates conversion record
- Links click tracking to conversion

## Postback URLs Feature

### Accessing Postback URLs
1. Go to Django Admin → Site Settings
2. Click "View Postback URLs" button
3. You'll see a page with all configured CPA networks

### Example Generated URLs

#### NexusSyner
```
https://yourdomain.com/offers/postback/?network=NexusSyner&click_id={s2}&payout={{sum}}
```

#### AffRoyal
```
https://yourdomain.com/offers/postback/?network=AffRoyal&subid={subid}&sum={{sum}}
```

### How to Use
1. **Copy the URL**: Click the "Copy" button next to each network
2. **Replace Placeholders**: 
   - `{s2}` or `{subid}` → Replace with actual click ID parameter from your network
   - `{{sum}}` → Replace with actual payout parameter from your network
3. **Configure in CPA Network**: Paste the modified URL into your CPA network's postback settings

## Testing

### 1. Configure Site Settings
1. Go to Django Admin → Site Settings
2. Set your domain name and site URL
3. Save the settings

### 2. Get Postback URLs
1. Click "View Postback URLs" in Site Settings
2. Copy the URLs for your networks
3. Configure them in your CPA networks

### 3. Create an Offer
1. Go to Django Admin → Offers → Add Offer
2. Select CPA Network from dropdown
3. Enter offer URL from CPA network
4. Save the offer

### 4. Test Click Tracking
1. Approve a user for the offer
2. Click "Get Link" on the offer
3. Visit the tracking link
4. Verify redirect to CPA network with click ID

### 5. Test Postback
1. Send test postback to your postback URL
2. Check conversion records in admin
3. Verify click tracking is linked to conversion

## Benefits

- ✅ **Database Storage**: All networks stored in database
- ✅ **Easy Management**: Use Django admin to manage networks
- ✅ **Safe Updates**: Management command updates existing networks
- ✅ **Version Control**: Network data can be version controlled
- ✅ **Flexible**: Add networks via admin or management command
- ✅ **Scalable**: Easy to add many networks
- ✅ **Admin Interface**: Full CRUD operations in Django admin

## Troubleshooting

### Network Not Showing in Dropdown
- Check if `is_active` is set to `True` in admin
- Verify the network exists in database
- Check Django admin → CPA Networks

### Postback Not Working
- Verify site settings are configured correctly
- Check parameter names match CPA network requirements
- Ensure postback URL is accessible from internet

### Click ID Not Being Added
- Verify `click_id_parameter` is correct for the network
- Check offer URL format in admin

### Site Settings Not Working
- Ensure only one active site settings record exists
- Check domain name and site URL are correct
- Restart Django server after changes

### Management Command Issues
- Check network_key is unique
- Verify all required fields are provided
- Check Django logs for errors

### Adding New Networks
1. **Edit the command file**: Add to `cpa_networks_data` list
2. **Run the command**: `python manage.py populate_cpa_networks`
3. **Or use admin**: Go to Django Admin → CPA Networks → Add 