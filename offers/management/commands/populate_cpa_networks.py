from django.core.management.base import BaseCommand
from offers.models import CPANetwork

class Command(BaseCommand):
    help = 'Populate CPA networks data'

    def handle(self, *args, **options):
        self.stdout.write('Populating CPA Networks...')
        
        # Define CPA networks data - most use subid for click ID
        cpa_networks_data = [
            # Main Networks (1-30)
            {
                'network_key': 'NexusSyner',
                'name': 'NexusSyner',
                'description': 'NexusSyner CPA Network',
                'click_id_parameter': 's2',
                'postback_click_id_parameter': 'click_id',
                'click_id_wrapper': '{}',
                'is_active': True
            },
            {
                'network_key': 'DreamAff',
                'name': 'DreamAff',
                'description': 'DreamAff CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'click_id_wrapper': '{}',
                'is_active': True
            },
            {
                'network_key': 'AffRoyal',
                'name': 'AffRoyal',
                'description': 'AffRoyal CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'click_id_wrapper': '{}',
                'is_active': True
            },
            {
                'network_key': 'OfferGreenlineMedia',
                'name': 'OfferGreenlineMedia (OGM)',
                'description': 'OfferGreenlineMedia CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'click_id_wrapper': '{}',
                'is_active': True
            },
            {
                'network_key': 'AdGainMedia',
                'name': 'AdGainMedia (AGM)',
                'description': 'AdGainMedia CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'click_id_wrapper': '{}',
                'is_active': True
            },
            {
                'network_key': 'OMSolution',
                'name': 'OMSolution (OMS)',
                'description': 'OMSolution CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'click_id_wrapper': '{}',
                'is_active': True
            },
            {
                'network_key': 'GlobalAds',
                'name': 'GlobalAds',
                'description': 'GlobalAds CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'click_id_wrapper': '{}',
                'is_active': True
            },
            {
                'network_key': 'Olavivo',
                'name': 'Olavivo',
                'description': 'Olavivo CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'is_active': True
            },
            {
                'network_key': 'CrackRevenue',
                'name': 'Crack Revenue',
                'description': 'Crack Revenue CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'is_active': True
            },
            {
                'network_key': 'AdBlueMedia',
                'name': 'AdBlueMedia',
                'description': 'AdBlueMedia CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'is_active': True
            },
            {
                'network_key': 'CPAGrip',
                'name': 'CPAGrip',
                'description': 'CPAGrip CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'is_active': True
            },
            {
                'network_key': 'CPALead',
                'name': 'CPA Lead',
                'description': 'CPA Lead Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'is_active': True
            },
            {
                'network_key': 'AffMine',
                'name': 'AffMine',
                'description': 'AffMine CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'is_active': True
            },
            {
                'network_key': 'CMAffs',
                'name': 'CMAffs',
                'description': 'CMAffs CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'is_active': True
            },
            {
                'network_key': 'Surflink',
                'name': 'Surflink.io',
                'description': 'Surflink.io CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'is_active': True
            },
            {
                'network_key': 'AdMolly',
                'name': 'AdMolly',
                'description': 'AdMolly CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'is_active': True
            },
            {
                'network_key': 'ClicksAdv',
                'name': 'ClicksAdv',
                'description': 'ClicksAdv CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'is_active': True
            },
            {
                'network_key': 'AffClickMedia',
                'name': 'AffClickMedia',
                'description': 'AffClickMedia CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'is_active': True
            },
            {
                'network_key': 'ClickHunts',
                'name': 'ClickHunts',
                'description': 'ClickHunts CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'postback_payout_parameter': 'sum',
                'is_active': True
            },
            {
                'network_key': '365CNV',
                'name': '365CNV',
                'description': '365CNV CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'postback_payout_parameter': 'sum',
                'is_active': True
            },
            {
                'network_key': 'GuruMedia',
                'name': 'GuruMedia',
                'description': 'GuruMedia CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'postback_payout_parameter': 'sum',
                'is_active': True
            },
            {
                'network_key': 'LV111',
                'name': 'LV111',
                'description': 'LV111 CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'postback_payout_parameter': 'sum',
                'is_active': True
            },
            {
                'network_key': 'Olavivo2',
                'name': 'Olavivo (Secondary)',
                'description': 'Olavivo Secondary CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'postback_payout_parameter': 'sum',
                'is_active': True
            },
            {
                'network_key': 'CharMads',
                'name': 'CharMads',
                'description': 'CharMads CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'postback_payout_parameter': 'sum',
                'is_active': True
            },
            {
                'network_key': 'CPAFull',
                'name': 'CPAFull',
                'description': 'CPAFull CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'postback_payout_parameter': 'sum',
                'is_active': True
            },
            {
                'network_key': 'OGAds',
                'name': 'OGAds',
                'description': 'OGAds CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'postback_payout_parameter': 'sum',
                'is_active': True
            },
            {
                'network_key': 'RayAdvertising',
                'name': 'RayAdvertising',
                'description': 'RayAdvertising CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'postback_payout_parameter': 'sum',
                'is_active': True
            },
            {
                'network_key': 'HighRockAds',
                'name': 'HighRockAds',
                'description': 'HighRockAds CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'postback_payout_parameter': 'sum',
                'is_active': True
            },
            {
                'network_key': 'MediaTransits',
                'name': 'MediaTransits',
                'description': 'MediaTransits CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'postback_payout_parameter': 'sum',
                'is_active': True
            },
            {
                'network_key': 'ILSMedia',
                'name': 'ILSMedia',
                'description': 'ILSMedia CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'click_id_wrapper': '{}',
                'is_active': True
            },
            
            # 18+ Networks (31-35)
            {
                'network_key': 'Traffe',
                'name': 'Traffe',
                'description': 'Traffe 18+ CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'click_id_wrapper': '{}',
                'is_active': True
            },
            {
                'network_key': 'DatifyLink',
                'name': 'Datify.link',
                'description': 'Datify.link 18+ CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'click_id_wrapper': '{}',
                'is_active': True
            },
            {
                'network_key': 'Losspollos',
                'name': 'Losspollos',
                'description': 'Losspollos 18+ CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'click_id_wrapper': '{}',
                'is_active': True
            },
            {
                'network_key': 'MyLead',
                'name': 'My Lead',
                'description': 'My Lead 18+ CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'click_id_wrapper': '{}',
                'is_active': True
            },
            {
                'network_key': 'PaySale',
                'name': 'PaySale',
                'description': 'PaySale 18+ CPA Network',
                'click_id_parameter': 'subid',
                'postback_click_id_parameter': 'subid',
                'click_id_wrapper': '{}',
                'is_active': True
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for network_data in cpa_networks_data:
            network_key = network_data['network_key']
            
            # Check if network exists
            try:
                network = CPANetwork.objects.get(network_key=network_key)
                # Update existing network
                for field, value in network_data.items():
                    setattr(network, field, value)
                network.save()
                updated_count += 1
                self.stdout.write(f'Updated: {network.name}')
            except CPANetwork.DoesNotExist:
                # Create new network
                network = CPANetwork.objects.create(**network_data)
                created_count += 1
                self.stdout.write(f'Created: {network.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(cpa_networks_data)} networks: '
                f'{created_count} created, {updated_count} updated'
            )
        )
        
        self.stdout.write(
            self.style.WARNING(
                '\n📝 NOTES:'
                '\n- Most networks use "subid" for click ID parameter'
                '\n- NexusSyner uses "s2" parameter (special case)'
                '\n- Click ID wrapper can be customized (e.g., {} for {s2}, # for #s2#, [] for [s2])'
                '\n- Payout is set when creating offers, not from postback'
                '\n- You can edit parameters in Django Admin → CPA Networks'
            )
        ) 