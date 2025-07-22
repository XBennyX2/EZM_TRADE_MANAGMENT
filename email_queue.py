#!/usr/bin/env python3
"""
Email Queue System for EZM Trade Management
Saves emails when network fails and sends them when network is available
"""
import os
import sys
import django
import json
import pickle
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.conf import settings

class EmailQueue:
    """Simple email queue system"""
    
    def __init__(self):
        self.queue_dir = '/tmp/email_queue'
        os.makedirs(self.queue_dir, exist_ok=True)
    
    def queue_email(self, subject, message, to_email, attachment_data=None, attachment_name=None, attachment_type='application/pdf'):
        """Queue an email for later sending"""
        try:
            email_data = {
                'subject': subject,
                'message': message,
                'to_email': to_email,
                'from_email': settings.DEFAULT_FROM_EMAIL,
                'attachment_data': attachment_data,
                'attachment_name': attachment_name,
                'attachment_type': attachment_type,
                'queued_at': datetime.now().isoformat(),
            }
            
            # Save to queue file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            queue_file = os.path.join(self.queue_dir, f'email_{timestamp}.pkl')
            
            with open(queue_file, 'wb') as f:
                pickle.dump(email_data, f)
            
            print(f"📥 Email queued: {queue_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to queue email: {e}")
            return False
    
    def send_queued_emails(self):
        """Send all queued emails"""
        queue_files = [f for f in os.listdir(self.queue_dir) if f.endswith('.pkl')]
        
        if not queue_files:
            print("📭 No queued emails found")
            return True
        
        print(f"📧 Found {len(queue_files)} queued emails")
        sent_count = 0
        failed_count = 0
        
        for queue_file in queue_files:
            queue_path = os.path.join(self.queue_dir, queue_file)
            
            try:
                # Load email data
                with open(queue_path, 'rb') as f:
                    email_data = pickle.load(f)
                
                print(f"\n📤 Sending queued email to {email_data['to_email']}")
                
                # Create email
                msg = EmailMultiAlternatives(
                    subject=email_data['subject'],
                    body=email_data['message'],
                    from_email=email_data['from_email'],
                    to=[email_data['to_email']]
                )
                
                # Add attachment if present
                if email_data.get('attachment_data') and email_data.get('attachment_name'):
                    msg.attach(
                        email_data['attachment_name'],
                        email_data['attachment_data'],
                        email_data['attachment_type']
                    )
                
                # Send email
                msg.send()
                
                # Move to sent folder
                sent_dir = os.path.join(self.queue_dir, 'sent')
                os.makedirs(sent_dir, exist_ok=True)
                sent_path = os.path.join(sent_dir, queue_file)
                os.rename(queue_path, sent_path)
                
                print(f"   ✅ Sent successfully")
                sent_count += 1
                
            except Exception as e:
                print(f"   ❌ Failed to send: {e}")
                failed_count += 1
        
        print(f"\n📊 Email sending summary:")
        print(f"   ✅ Sent: {sent_count}")
        print(f"   ❌ Failed: {failed_count}")
        
        return failed_count == 0

# Global instance
email_queue = EmailQueue()

def main():
    """Send all queued emails"""
    print("📧 EZM Email Queue - Sending Queued Emails")
    print("=" * 50)
    
    try:
        success = email_queue.send_queued_emails()
        
        if success:
            print("\n🎉 All queued emails sent successfully!")
        else:
            print("\n⚠️  Some emails failed to send. Check network connection.")
            
    except Exception as e:
        print(f"\n❌ Error processing email queue: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
