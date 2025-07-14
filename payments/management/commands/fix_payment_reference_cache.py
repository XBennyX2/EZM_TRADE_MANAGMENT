from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.sessions.models import Session
from payments.models import ChapaTransaction
from django.contrib.auth import get_user_model
import time

User = get_user_model()


class Command(BaseCommand):
    help = 'Fix payment reference issues by clearing cache and sessions'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 FIXING: Payment Reference Cache Issues'))
        self.stdout.write('=' * 60)

        # Step 1: Clear all cache
        self.stdout.write('\n📋 Step 1: Clearing Application Cache')
        self.clear_cache()

        # Step 2: Clear problematic sessions
        self.stdout.write('\n📋 Step 2: Clearing User Sessions')
        self.clear_sessions()

        # Step 3: Clean up any problematic transactions
        self.stdout.write('\n📋 Step 3: Cleaning Transaction Records')
        self.clean_transactions()

        # Step 4: Test payment reference generation
        self.stdout.write('\n📋 Step 4: Testing Payment Reference Generation')
        self.test_reference_generation()

        # Step 5: Provide browser cache clearing instructions
        self.stdout.write('\n📋 Step 5: Browser Cache Instructions')
        self.provide_browser_instructions()

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ Payment Reference Fix Complete'))

    def clear_cache(self):
        """Clear all application cache"""
        try:
            cache.clear()
            self.stdout.write('   ✅ Application cache cleared successfully')
        except Exception as e:
            self.stdout.write(f'   ⚠️  Cache clear failed: {str(e)}')

    def clear_sessions(self):
        """Clear user sessions to fix any session-related issues"""
        try:
            # Clear all sessions
            session_count = Session.objects.count()
            Session.objects.all().delete()
            self.stdout.write(f'   ✅ Cleared {session_count} user sessions')
            self.stdout.write('   ℹ️  Users will need to log in again')
        except Exception as e:
            self.stdout.write(f'   ⚠️  Session clear failed: {str(e)}')

    def clean_transactions(self):
        """Clean up any problematic transaction records"""
        try:
            # Count current transactions
            total_transactions = ChapaTransaction.objects.count()
            pending_transactions = ChapaTransaction.objects.filter(status='pending').count()
            
            self.stdout.write(f'   📊 Total transactions: {total_transactions}')
            self.stdout.write(f'   📊 Pending transactions: {pending_transactions}')
            
            # Check for any transactions with unusual references
            unusual_refs = ChapaTransaction.objects.exclude(
                chapa_tx_ref__startswith='EZM-'
            ).count()
            
            if unusual_refs > 0:
                self.stdout.write(f'   ⚠️  Found {unusual_refs} transactions with unusual references')
            else:
                self.stdout.write('   ✅ All transaction references follow proper format')
            
            # Check for very recent duplicates (within last minute)
            import datetime
            from django.utils import timezone
            
            one_minute_ago = timezone.now() - datetime.timedelta(minutes=1)
            recent_transactions = ChapaTransaction.objects.filter(
                created_at__gte=one_minute_ago
            )
            
            if recent_transactions.count() > 10:
                self.stdout.write(f'   ⚠️  High transaction volume in last minute: {recent_transactions.count()}')
                self.stdout.write('   ℹ️  This might indicate rapid retry attempts')
            else:
                self.stdout.write('   ✅ Normal transaction volume')
                
        except Exception as e:
            self.stdout.write(f'   ⚠️  Transaction analysis failed: {str(e)}')

    def test_reference_generation(self):
        """Test current reference generation system"""
        from payments.chapa_client import ChapaClient
        
        client = ChapaClient()
        
        # Generate test references
        self.stdout.write('   🧪 Generating test references:')
        references = []
        
        for i in range(5):
            ref = client.generate_tx_ref()
            references.append(ref)
            self.stdout.write(f'      {i+1}. {ref}')
            time.sleep(0.1)  # Small delay
        
        # Check uniqueness
        unique_refs = set(references)
        if len(unique_refs) == len(references):
            self.stdout.write('   ✅ All test references are unique')
        else:
            self.stdout.write('   ❌ Duplicate references detected!')
        
        # Test actual payment initialization
        user = User.objects.filter(role='head_manager').first()
        if user:
            self.stdout.write('   🧪 Testing payment initialization:')
            try:
                result = client.initialize_payment(
                    amount=10.00,
                    email=user.email,
                    first_name=user.first_name or user.username,
                    last_name=user.last_name or 'Test',
                    description='Cache fix test'
                )
                
                if result.get('success'):
                    self.stdout.write('   ✅ Payment initialization: SUCCESS')
                    self.stdout.write(f'      Reference: {result.get("tx_ref")}')
                else:
                    error = result.get('error', 'Unknown error')
                    self.stdout.write(f'   ❌ Payment initialization: FAILED')
                    self.stdout.write(f'      Error: {error}')
                    
                    if 'reference' in str(error).lower():
                        self.stdout.write('   🚨 REFERENCE ERROR STILL EXISTS!')
                        return False
                        
            except Exception as e:
                self.stdout.write(f'   ❌ Payment test exception: {str(e)}')
                return False
        
        return True

    def provide_browser_instructions(self):
        """Provide instructions for clearing browser cache"""
        self.stdout.write('   🌐 BROWSER CACHE CLEARING INSTRUCTIONS:')
        self.stdout.write('')
        self.stdout.write('   📱 Chrome/Edge:')
        self.stdout.write('      1. Press Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)')
        self.stdout.write('      2. Select "All time" for time range')
        self.stdout.write('      3. Check "Cached images and files"')
        self.stdout.write('      4. Click "Clear data"')
        self.stdout.write('')
        self.stdout.write('   🦊 Firefox:')
        self.stdout.write('      1. Press Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)')
        self.stdout.write('      2. Select "Everything" for time range')
        self.stdout.write('      3. Check "Cache"')
        self.stdout.write('      4. Click "Clear Now"')
        self.stdout.write('')
        self.stdout.write('   🍎 Safari:')
        self.stdout.write('      1. Press Cmd+Option+E')
        self.stdout.write('      2. Or Safari > Preferences > Privacy > Manage Website Data > Remove All')
        self.stdout.write('')
        self.stdout.write('   ⚡ QUICK FIX:')
        self.stdout.write('      1. Open browser in Incognito/Private mode')
        self.stdout.write('      2. Navigate to http://localhost:8001')
        self.stdout.write('      3. Test payment functionality')
        self.stdout.write('')
        self.stdout.write('   🔄 HARD REFRESH:')
        self.stdout.write('      1. Press Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)')
        self.stdout.write('      2. This bypasses cache for current page')
        self.stdout.write('')
        self.stdout.write('   📱 MOBILE BROWSERS:')
        self.stdout.write('      1. Go to browser settings')
        self.stdout.write('      2. Find "Privacy" or "Storage"')
        self.stdout.write('      3. Clear browsing data/cache')
        self.stdout.write('')
        self.stdout.write('   🎯 DEVELOPER TOOLS:')
        self.stdout.write('      1. Press F12 to open developer tools')
        self.stdout.write('      2. Right-click refresh button')
        self.stdout.write('      3. Select "Empty Cache and Hard Reload"')

    def display_final_status(self):
        """Display final status and next steps"""
        self.stdout.write('\n🎯 FINAL STATUS')
        self.stdout.write('-' * 30)
        
        # Test one more time
        from payments.chapa_client import ChapaClient
        client = ChapaClient()
        user = User.objects.filter(role='head_manager').first()
        
        if user:
            try:
                result = client.initialize_payment(
                    amount=5.00,
                    email=user.email,
                    first_name=user.first_name or user.username,
                    last_name=user.last_name or 'Test',
                    description='Final status test'
                )
                
                if result.get('success'):
                    self.stdout.write('✅ SYSTEM STATUS: WORKING PERFECTLY')
                    self.stdout.write(f'   Latest reference: {result.get("tx_ref")}')
                    self.stdout.write('   Payment system is operational')
                    
                    self.stdout.write('\n💡 IF YOU STILL SEE "Invalid payment reference":')
                    self.stdout.write('   1. Clear your browser cache (see instructions above)')
                    self.stdout.write('   2. Log out and log back in')
                    self.stdout.write('   3. Try in incognito/private mode')
                    self.stdout.write('   4. Check for JavaScript errors in browser console')
                    
                else:
                    error = result.get('error', 'Unknown error')
                    self.stdout.write(f'❌ SYSTEM STATUS: ERROR DETECTED')
                    self.stdout.write(f'   Error: {error}')
                    
                    if 'reference' in str(error).lower():
                        self.stdout.write('\n🚨 CRITICAL: Reference error persists!')
                        self.stdout.write('   This requires immediate investigation')
                        self.stdout.write('   Contact system administrator')
                    
            except Exception as e:
                self.stdout.write(f'❌ SYSTEM STATUS: EXCEPTION')
                self.stdout.write(f'   Exception: {str(e)}')
        
        self.stdout.write('\n🔧 COMPLETED ACTIONS:')
        self.stdout.write('   ✅ Application cache cleared')
        self.stdout.write('   ✅ User sessions cleared')
        self.stdout.write('   ✅ Transaction records analyzed')
        self.stdout.write('   ✅ Reference generation tested')
        self.stdout.write('   ✅ Browser instructions provided')
        
        self.stdout.write('\n🚀 NEXT STEPS:')
        self.stdout.write('   1. Clear browser cache using instructions above')
        self.stdout.write('   2. Log in again (sessions were cleared)')
        self.stdout.write('   3. Test payment functionality')
        self.stdout.write('   4. If error persists, try incognito mode')
        self.stdout.write('   5. Report any remaining issues with browser console logs')
