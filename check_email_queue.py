#!/usr/bin/env python3
"""
Check and manage email queue for EZM Trade Management
"""
import os
import pickle
from datetime import datetime

def check_queue():
    """Check what emails are in the queue"""
    queue_dir = '/tmp/email_queue'
    
    if not os.path.exists(queue_dir):
        print("📭 No email queue directory found")
        return
    
    queue_files = [f for f in os.listdir(queue_dir) if f.endswith('.pkl')]
    
    if not queue_files:
        print("📭 No emails in queue")
        return
    
    print(f"📧 Found {len(queue_files)} queued emails:")
    print("=" * 50)
    
    for i, queue_file in enumerate(queue_files, 1):
        queue_path = os.path.join(queue_dir, queue_file)
        
        try:
            with open(queue_path, 'rb') as f:
                email_data = pickle.load(f)
            
            print(f"\n📧 Email {i}:")
            print(f"   📅 Queued: {email_data.get('queued_at', 'Unknown')}")
            print(f"   📧 To: {email_data.get('to_email', 'Unknown')}")
            print(f"   📋 Subject: {email_data.get('subject', 'Unknown')}")
            print(f"   📎 Attachment: {email_data.get('attachment_name', 'None')}")
            print(f"   📁 File: {queue_file}")
            
        except Exception as e:
            print(f"\n❌ Error reading {queue_file}: {e}")
    
    print(f"\n💡 To send these emails when network is available:")
    print(f"   python email_queue.py")

if __name__ == '__main__':
    print("📧 EZM Email Queue Status")
    print("=" * 30)
    check_queue()
